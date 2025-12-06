# CAT-Net-Webapp/app/catnet_core/analysis_service.py

import os
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.nn import functional as F
from PIL import Image
from pathlib import Path

# --- Plotting Fixes ---
import matplotlib
matplotlib.use('Agg') # FIX: Use non-interactive backend to prevent GUI errors
import seaborn as sns
import matplotlib.pyplot as plt 

# --- Import dependencies copied from the CAT-Net repo ---
# NOTE: Using absolute imports due to sys.path fix in run.py
from lib.config import config, update_config
from lib import models
from lib.core.criterion import CrossEntropy 
from lib.utils.utils import FullModel
from Splicing.data.data_core import SplicingDataset as splicing_dataset
from project_config import dataset_paths 

# --- Patch for numpy compatibility ---
try:
    _ = np.float
except AttributeError:
    np.float = float

# --- Global Model and Config Variables ---
MODEL = None
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# FIX 1: Use the specific, high-performance model file name
MODEL_CFG = 'experiments/CAT_full.yaml'
MODEL_WEIGHTS = 'CAT_full_v2.pth.tar' 
MODEL_PATH = Path(__file__).parent / MODEL_WEIGHTS

# FIX 2: Define the mock path string required by the configuration system
MOCK_CONFIG_PATH = 'output/splicing_dataset/CAT_full/CAT_full_v2.pth.tar'


def load_catnet_model():
    """Initializes and loads the CAT-Net model once."""
    global MODEL
    if MODEL is not None:
        return MODEL

    print(f"[CAT-NET] Running on device: {DEVICE}")

    # 1. Setup Configs 
    args = argparse.Namespace(
        cfg=Path(__file__).parent / MODEL_CFG, 
        opts=[
            # CRITICAL FIX: Pass the mock path string for config system validation
            'TEST.MODEL_FILE', MOCK_CONFIG_PATH, 
            'TEST.FLIP_TEST', 'False', 
            'TEST.NUM_SAMPLES', '0'
        ]
    )
    update_config(config, args)

    # 2. Initialize necessary components (Data and Criterion)
    test_dataset_info = splicing_dataset(crop_size=None, grid_crop=True, blocks=('RGB', 'DCTvol', 'qtable'), DCT_channels=1, mode='arbitrary', read_from_jpeg=True) 

    criterion = CrossEntropy(ignore_label=config.TRAIN.IGNORE_LABEL, weight=test_dataset_info.class_weights).to(DEVICE)

    # 3. Initialize Model Structure
    model_structure = eval('models.' + config.MODEL.NAME + '.get_seg_model')(config)
    model = FullModel(model_structure, criterion)
    
    # 4. Load Weights (Using the correct physical path: MODEL_PATH)
    print(f'[CAT-NET] Loading model from {MODEL_PATH}')
    
    try:
        checkpoint = torch.load(MODEL_PATH, map_location=torch.device('cpu'), weights_only=False)
        model.model.load_state_dict(checkpoint['state_dict'])
        model = nn.DataParallel(model, device_ids=list(config.GPUS)).to(DEVICE)
        model.eval()
        
        MODEL = model
        print("[CAT-NET] Model loaded successfully.")
        return MODEL
        
    except FileNotFoundError:
        print(f"ERROR: Model weights not found at {MODEL_PATH}. Check file path.")
        raise
    except Exception as e:
        print(f"ERROR during model loading: {e}")
        raise

# Call once when the script starts
try:
    load_catnet_model()
except Exception as e:
    print(f"FATAL: Model initialization error: {e}")


def analyze_image_with_catnet(image_path: str, user_id: str = "guest") -> dict:
    """
    Performs CAT-Net inference on a single image file by stream-lining data fetching.
    """
    global MODEL
    if MODEL is None:
        load_catnet_model()
    
    if MODEL is None:
        raise Exception("CAT-Net model failed to initialize.")

    # FIX: Define 'user' to resolve Jinja2 UndefinedError from routes.py
    user = user_id 
    
    # 1. Initialize the SplicingDataset wrapper structure (FULL FEATURES)
    wrapper_dataset = splicing_dataset(
        crop_size=None, grid_crop=True, 
        blocks=('RGB', 'DCTvol', 'qtable'), 
        DCT_channels=1, 
        mode='arbitrary', 
        read_from_jpeg=True
    )
    
    # 2. Get the actual dataset instance & override file list
    single_image_loader = wrapper_dataset.dataset_list[0] 
    single_image_loader.tamp_list = [image_path] 
    
    # 3. DIRECTLY CALL get_tamp(0) to get UNBATCHED tensors
    try:
        image_tensor, label_tensor, qtable_tensor = single_image_loader.get_tamp(0)
    except Exception as e:
        raise Exception(f"Data preprocessing failed: {e}")
    
    
    # 4. Run Inference (Manual Batching)
    with torch.no_grad():
        # Add batch dimension and move to device
        image_tensor = image_tensor.unsqueeze(0).to(DEVICE)
        label_tensor = label_tensor.unsqueeze(0).long().to(DEVICE)
        qtable_tensor = qtable_tensor.unsqueeze(0).to(DEVICE)
        
        # Run Model (3 inputs expected)
        _, pred_logits = MODEL(image_tensor, label_tensor, qtable_tensor)
            
        # Process Output (Segmentation Mask)
        pred = torch.squeeze(pred_logits, 0)
        pred_prob = F.softmax(pred, dim=0)[1] 
        pred_np = pred_prob.cpu().numpy()
        
        # 5. Generate Filename and Path for Heatmap
        original_filename = Path(image_path).name
        heatmap_filename = f"{user_id}_{Path(original_filename).stem}_heatmap.png" 
        heatmap_filepath = dataset_paths['SAVE_PRED'] / heatmap_filename

        # 6. Plot Heatmap
        try:
            H, W = pred_np.shape
            DPI = 100 
            
            fig = plt.figure(frameon=False, figsize=(W / DPI, H / DPI), dpi=DPI)
            sns.heatmap(pred_np, vmin=0, vmax=1, cbar=False, cmap='jet')
            plt.axis('off')
            plt.savefig(heatmap_filepath, bbox_inches='tight', transparent=True, pad_inches=0)
            plt.close(fig)
        except Exception as e:
            # If plotting fails, we raise the error back to routes.py
            raise Exception(f"Failed to generate heatmap visual: {e}")

        # 7. Final Report Generation
        mean_manipulation_score = pred_np.mean()
        max_manipulation_score = pred_np.max()
        DETECTION_THRESHOLD = 0.6 
        
        if max_manipulation_score > DETECTION_THRESHOLD:
             result_text = "Manipulation Detected"
             category = "danger"
        else:
             result_text = "Image Appears Authentic"
             category = "success"

        return {
            'prediction': result_text,
            'max_manipulation_score': f"{max_manipulation_score * 100:.2f}%",
            'average_score': f"{mean_manipulation_score * 100:.2f}%",
            # FIX: Only return the path relative to static/
            'heatmap_url_path': f'predictions/{heatmap_filename}', 
            'category': category,
            'recommendation': "The analysis suggests potential image manipulation/splicing. Please review the heatmap for localized inconsistencies."
        }