import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoFeatureExtractor,WhisperModel
from torch.utils.data import Dataset,DataLoader
from datasets import load_dataset,Audio
import numpy as np
from sklearn.metrics import roc_curve,auc
import os
from pathlib import Path
# Same configs as training
MODEL_ID="openai/whisper-tiny"
AUDIO_SAMPLING_RATE=16000
BATCH_SIZE=16
EMBED_DIM=256
DEVICE=torch.device("cuda"if torch.cuda.is_available() else"cpu")
MODEL_SAVE_PATH="speaker_embedding_model_online_triplet_multiview.pth"
# EXACT SAME MODEL ARCHITECTURE AS TRAINING
class EmbeddingExtractor(nn.Module):
    def __init__(self, whisper_model,embed_dim):
        super().__init__()
        self.whisper=whisper_model
        d_model=self.whisper.config.d_model
        self.projection=nn.Sequential(
            nn.Linear(d_model,embed_dim),
            nn.ReLU(),
            nn.Linear(embed_dim,embed_dim)
        )
    def forward(self,input_features):
        batch_size=input_features.size(0)
        decoder_input_ids=torch.tensor([self.whisper.config.decoder_start_token_id]*batch_size).unsqueeze(1).to(input_features.device)
        outputs=self.whisper(input_features, decoder_input_ids=decoder_input_ids)
        encoder_states=outputs.encoder_last_hidden_state
        pooled=encoder_states.mean(dim=1)
        embeddings=self.projection(pooled)
        return embeddings
# Load model EXACTLY like training
def load_trained_model(checkpoint_path,model_id=MODEL_ID,embed_dim=EMBED_DIM):
    checkpoint=torch.load(checkpoint_path,map_location=DEVICE,weights_only=False)
    whisper_model=WhisperModel.from_pretrained(model_id).to(DEVICE)
    whisper_model.config.output_hidden_states=True
    for param in whisper_model.decoder.parameters():
        param.requires_grad=False
    model=EmbeddingExtractor(whisper_model,embed_dim).to(DEVICE)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    feature_extractor=AutoFeatureExtractor.from_pretrained(model_id)
    return model,feature_extractor
class SpeakerEvalDataset(Dataset):
    def __init__(self,dataset):
        self.dataset=dataset
    def __len__(self):
        return len(self.dataset)
    def __getitem__(self,idx):
        item=self.dataset[idx]
        audio=item['audio']['array']
        label=item['speaker_id']
        return{'audio':audio,'speaker_id':label}
def pad_or_truncate(features,target_length=3000):
    if features.shape[-1]<target_length:
        padding=target_length-features.shape[-1]
        features=F.pad(features,(0,padding),mode="constant",value=0)
    elif features.shape[-1]>target_length:
        features=features[...,:target_length]
    return features
def eval_collate_fn(batch):
    audio_list=[item['audio']for item in batch]
    label_list=[item['speaker_id']for item in batch]
    # Global feature_extractor to avoid repeated loading
    feature_extractor=AutoFeatureExtractor.from_pretrained(MODEL_ID)
    features=feature_extractor(
        audio_list, 
        sampling_rate=AUDIO_SAMPLING_RATE, 
        return_tensors="pt", 
        padding=True
    ).input_features#Shape: [batch_size,80,variable_time].
    # Pad/truncate to 3000.
    padded_features=[]
    for i in range(features.size(0)):
        single_feature=features[i:i+1]#[1,80,time].
        padded=pad_or_truncate(single_feature,target_length=3000)
        padded_features.append(padded)
    features=torch.cat(padded_features, dim=0)  # [batch_size, 80, 3000]
    labels=torch.tensor(label_list)
    return features,labels
def calculate_metrics(model, dataloader):
    model.eval()
    scores=[]
    true_labels=[]
    print("Computing embeddings and similarities...")
    with torch.no_grad():
        for batch_idx,(features,labels)in enumerate(dataloader):
            features=features.to(DEVICE)
            labels=labels.to(DEVICE)
            embeddings=model(features)
            norm_emb=F.normalize(embeddings,p=2,dim=1)
            sim_matrix=torch.matmul(norm_emb,norm_emb.T)
            for i in range(embeddings.size(0)):
                for j in range(i+1,embeddings.size(0)):
                    scores.append(sim_matrix[i,j].item())
                    true_labels.append(1 if labels[i]==labels[j]else 0)
            if (batch_idx+1)%10==0:
                print(f"Processed {batch_idx+1}/{len(dataloader)} batches.")
    print("Calculating EER, AUC, Accuracy...")
    scores=np.array(scores)
    true_labels=np.array(true_labels)
    fpr,tpr,thresholds=roc_curve(true_labels,scores)
    fnr=1-tpr
    diff=np.abs(fpr-fnr)
    eer=fpr[np.argmin(diff)]
    auc_score=auc(fpr, tpr)
    thresh=thresholds[np.argmin(diff)]
    preds=(scores>=thresh).astype(int)
    accuracy=(preds==true_labels).mean()
    return eer,auc_score,accuracy,thresh
# Main evaluation
def main():
    # Load best model
    checkpoint_path=Path("best_model.pth")
    if not os.path.exists(checkpoint_path):
        checkpoint_path=MODEL_SAVE_PATH
        print(f"Best model not found, using final model: {checkpoint_path}.")
    print(f"Loading model from {checkpoint_path}.")
    model,feature_extractor=load_trained_model(checkpoint_path)
    # Prepare test dataset
    print("Loading librispeech_asr clean test...")
    test_dataset_raw=load_dataset('librispeech_asr','clean',split='test')
    test_dataset_raw=test_dataset_raw.cast_column("audio",Audio(sampling_rate=AUDIO_SAMPLING_RATE,decode=True))
    # Map speaker IDs
    all_spk_ids=list(set(test_dataset_raw["speaker_id"]))
    speaker_to_id={spk:idx for idx,spk in enumerate(all_spk_ids)}
    def map_speaker(example):
        example["speaker_id"]=speaker_to_id[example["speaker_id"]]
        return example
    test_dataset_raw=test_dataset_raw.map(map_speaker)
    print(f"Test dataset size: {len(test_dataset_raw)}.")
    # Create proper dataset and dataloader
    test_dataset=SpeakerEvalDataset(test_dataset_raw)
    test_dataloader=DataLoader(
        test_dataset, 
        batch_size=BATCH_SIZE, 
        shuffle=False, 
        collate_fn=eval_collate_fn,
        num_workers=0#Set to 0 to avoid multiprocessing issues.
    )
    # Evaluate
    print("Starting evaluation...")
    eer,auc_score,accuracy,best_thresh=calculate_metrics(model,test_dataloader)
    print(f"\n{'='*50}")
    print(f"       EVALUATION RESULTS")
    print(f"{'='*50}")
    print(f"EER:           {eer:.4f}")
    print(f"AUC:           {auc_score:.4f}")
    print(f"Accuracy:      {accuracy:.4f}")
    print(f"Best Threshold:{best_thresh:.4f}")
    print(f"{'='*50}")
    checkpoint={
        'model_state_dict':model.state_dict(),
        'best_thresh':best_thresh,
        'eer':eer,
        'auc_score':auc_score,
        'accuracy':accuracy
    }
    torch.save(checkpoint,checkpoint_path)
if __name__=="__main__":
    main()

