"""
 Created by Myung-Joon Kwon
 mjkwon2021@gmail.com
 July 7, 2020
"""
import os
from pathlib import Path
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
project_root = Path(__file__).parent
# dataset_root = Path(r"C:\Users\mmc\Downloads\Splicing")
dataset_root = Path(r"/content/drive/MyDrive/FYP/CAT-Net/Splicing")
dataset_paths = {
    # Specify where are the roots of the datasets.
    # 'FR': dataset_root / "FantasticReality_v1",
    # 'IMD': dataset_root / "IMD2020",
    'CASIA': dataset_root / "CASIA",
    # 'NC16': dataset_root / "NC2016_Test",
    # 'Columbia': dataset_root / "Columbia Uncompressed Image Splicing Detection",
    # 'Carvalho': dataset_root / "tifs-database",
    # 'tampCOCO': dataset_root / "tampCOCO",
    # 'compRAISE': dataset_root / "compRAISE",
    # 'COVERAGE': dataset_root / "COVERAGE",
    # 'CoMoFoD': dataset_root / "CoMoFoD_small_v2",
    # 'GRIP': dataset_root / "CMFDdb_grip",
    # 'SAVE_PRED': project_root / "output_pred",
    'SAVE_PRED': BASE_DIR / 'predictions', 
}

# Ensure the prediction output folder exists
os.makedirs(dataset_paths['SAVE_PRED'], exist_ok=True)

