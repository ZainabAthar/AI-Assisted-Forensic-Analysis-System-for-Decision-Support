from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
import matplotlib.pyplot as plt
import torch.nn.functional as F
from pathlib import Path
import numpy as np
from . import wsi
import librosa
import torch
import os
MODEL_PATH=os.path.join(wsi.CHECKPOINT_DIR,'best_model.pth')
IMG_DIR='./visualizations'
def compute_similarity(model,feature_extractor,audio1_pth,audio2_pth,threshold):
    #Load audios.
    audio1=_load_audio(audio1_pth)
    audio2=_load_audio(audio2_pth)
    #Extract embeddings.
    embed1=_extract_embedding(model,feature_extractor,audio1)
    embed2=_extract_embedding(model,feature_extractor,audio2)
    #Compute cosine similarity.
    similarity=F.cosine_similarity(
        embed1.unsqueeze(0),
        embed2.unsqueeze(0)
    ).item()
    decision=similarity>=threshold
    return{
        'similarity':float(similarity),
        'decision':bool(decision),
        'embed1':embed1.numpy(),
        'embed2':embed2.numpy(),
        'threshold':threshold
    }
def _extract_embedding(model,feature_extractor,audio,sample_rate=wsi.AUDIO_SAMPLING_RATE):
    model.eval()
    with torch.no_grad():
        inputs=feature_extractor(
            audio,
            sampling_rate=wsi.AUDIO_SAMPLING_RATE,
            return_tensors='pt'
        )
        features=inputs['input_features'].to(wsi.DEVICE)
        features=wsi.pad_or_truncate(features,target_length=3000)
        embed=model(features)
        embed=F.normalize(embed,p=2,dim=1)
        return embed.squeeze(0).cpu()
def _load_audio(pth,sample_rate=wsi.AUDIO_SAMPLING_RATE):
    pth=Path(pth)
    if not pth.exists():
        raise FileNotFoundError(f'Audio file not found: {pth}.')
    audio,_=librosa.load(str(pth),sr=sample_rate,duration=30.0,mono=True)
    audio_trimmed,_=librosa.effects.trim(audio,top_db=20,frame_length=2048,hop_length=512)
    return audio_trimmed
def init_model(model_pth=MODEL_PATH):
    if not os.path.exists(model_pth):
        raise FileNotFoundError(f'Model checkpoint not found at {model_pth}.')
    checkpoint=torch.load(model_pth,map_location='cpu',weights_only=False)
    best_thresh=checkpoint.get('best_thresh',0.6)
    model,feature_extractor=wsi.load_trained_model(model_pth)
    return model,feature_extractor,best_thresh
def _compute_similarity_saliency(model,feature_extractor,audio,fixed_embed,sample_rate=wsi.AUDIO_SAMPLING_RATE):
    model.eval()
    inputs=feature_extractor(
        audio,
        sampling_rate=sample_rate,
        return_tensors='pt'
    )
    input_features=wsi.pad_or_truncate(inputs['input_features'].to(wsi.DEVICE),target_length=3000)
    input_features.requires_grad_(True)
    test_embed=model(input_features)
    test_embed=F.normalize(test_embed,p=2,dim=1)
    score=F.cosine_similarity(test_embed,fixed_embed.unsqueeze(0).to(wsi.DEVICE),dim=1)
    model.zero_grad()
    score.backward(retain_graph=True)
    saliency=torch.abs(input_features.grad[0]).sum(dim=0).cpu().detach().numpy()
    time_steps=np.linspace(0,min(len(audio)/sample_rate,30),len(saliency))
    return saliency,time_steps
def visualize_waveform_similarity(model,feature_extractor,audio1_pth,audio2_pth,sample_rate=wsi.AUDIO_SAMPLING_RATE):
    os.makedirs(IMG_DIR,exist_ok=True)
    audio1=_load_audio(audio1_pth)
    audio2=_load_audio(audio2_pth)
    embed1=_extract_embedding(model,feature_extractor,audio1)
    embed2=_extract_embedding(model,feature_extractor,audio2)
    sal1,time1=_compute_similarity_saliency(model,feature_extractor,audio1,embed2)
    sal2,time2=_compute_similarity_saliency(model,feature_extractor,audio2,embed1)
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(15,8))
    _plot_saliency_waveform(audio1,sal1,time1,ax1,f'Audio 01 Similarity')
    _plot_saliency_waveform(audio2,sal2,time2,ax2,f'Audio 02 Similarity')
    ax2.set_xlabel('Time (s)')
    plt.tight_layout()
    out_pth=Path(IMG_DIR)/f'{Path(audio1_pth).stem}_vs_{Path(audio2_pth).stem}_waveform.png'
    plt.savefig(out_pth,dpi=600,bbox_inches='tight',facecolor='white')
    plt.close()
    return str(out_pth)
def _plot_saliency_waveform(audio,saliency,time_steps,ax,title,sample_rate=wsi.AUDIO_SAMPLING_RATE):
    time_audio=np.linspace(0,len(audio)/sample_rate,len(audio))
    sal_resampled=np.interp(time_audio,time_steps,saliency)
    sal_max=np.max(sal_resampled)
    sal_norm=sal_resampled/sal_max if sal_max>0 else np.zeros_like(sal_resampled)
    points=np.array([time_audio,audio]).T.reshape(-1,1,2)
    segments=np.concatenate([points[:-1],points[1:]],axis=1)
    colors=plt.cm.plasma(sal_norm)
    lc=LineCollection(segments,colors=colors,linewidth=2,alpha=0.8)
    ax.add_collection(lc)
    ax.set_xlim(time_audio[0],time_audio[-1])
    ax.set_ylim(np.min(audio)*1.1,np.max(audio)*1.1)
    ax.set_title(title)
    ax.set_ylabel('Amplitude')
    ax.grid(True,alpha=0.3)
def visualize_spectrogram_similarity(model,feature_extractor,audio1_pth,audio2_pth,sample_rate=wsi.AUDIO_SAMPLING_RATE):
    os.makedirs(IMG_DIR,exist_ok=True)
    audio1=_load_audio(audio1_pth)
    audio2=_load_audio(audio2_pth)
    embed1=_extract_embedding(model,feature_extractor,audio1)
    embed2=_extract_embedding(model,feature_extractor,audio2)
    sal1,time1=_compute_similarity_saliency(model,feature_extractor,audio1,embed2)
    sal2,time2=_compute_similarity_saliency(model,feature_extractor,audio2,embed1)
    fig,(ax1,ax2)=plt.subplots(2,1,figsize=(15,8))
    _plot_saliency_spectrogram(audio1,sal1,time1,ax1,f'Audio 01 Similarity')
    _plot_saliency_spectrogram(audio2,sal2,time2,ax2,f'Audio 02 Similarity')
    ax2.set_xlabel('Time (s)')
    plt.tight_layout()
    out_pth=Path(IMG_DIR)/f'{Path(audio1_pth).stem}_vs_{Path(audio2_pth).stem}_spectrogram.png'
    plt.savefig(out_pth,dpi=600,bbox_inches='tight',facecolor='white')
    plt.close()
    return str(out_pth)
def _plot_saliency_spectrogram(audio,saliency,time_steps,ax,title,sample_rate=wsi.AUDIO_SAMPLING_RATE):
    duration=len(audio)/sample_rate
    S=np.abs(librosa.stft(audio))
    S_db=librosa.power_to_db(S,ref=np.max)
    img1=librosa.display.specshow(S_db,sr=sample_rate,x_axis='time',y_axis='hz',ax=ax,cmap='gray_r')
    time_audio=np.linspace(0,duration,len(audio))
    sal_resampled=np.interp(time_audio,time_steps,saliency)
    sal_max=np.max(sal_resampled)
    sal_norm=sal_resampled/sal_max if sal_max>0 else np.zeros_like(sal_resampled)
    ax_sal=ax.twinx()
    n_frames=S_db.shape[1]
    sal_spec=np.interp(np.linspace(0,1,n_frames),np.linspace(0,1,len(sal_norm)),sal_norm)
    x_sal=np.linspace(0,duration,len(sal_spec))
    ax_sal.fill_between(x_sal,0,sal_spec,color='gold',alpha=0.5)
    ax_sal.set_ylim(0,1)
    ax_sal.set_ylabel('Model Saliency ->',color='gold',fontweight='bold')
    ax_sal.tick_params(axis='y',colors='gold')
    ax.set_title(title,fontweight='bold')
    ax.set_xlim(0,duration)
    ax.set_ylabel('Frequency (Hz)')
    plt.colorbar(img1,ax=ax,format='%+2.0f dB',label='Intensity')
