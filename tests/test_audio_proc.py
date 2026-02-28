import pytest
import numpy as np
import torch
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import sys

# Setup paths
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from audioproc import interface as audio_proc

@pytest.fixture
def mock_model():
    model = MagicMock()
    model.eval.return_value = model
    return model

@pytest.fixture
def mock_feature_extractor():
    return MagicMock()

def test_compute_similarity_logic():
    """Test the similarity computation logic with mock embeddings."""
    model = MagicMock()
    feature_extractor = MagicMock()
    
    # v1.1: Patch _load_audio to avoid FileNotFoundError
    with patch('audioproc.interface._load_audio') as mock_load, \
         patch('audioproc.interface._extract_embedding') as mock_extract:
        # Create vectors with known cosine similarity
        mock_load.return_value = np.zeros(100) # Dummy audio
        # Correctly aligned vectors (same)
        v1 = torch.tensor([1.0, 0.0])
        v2 = torch.tensor([1.0, 0.0])
        
        mock_extract.side_effect = [v1, v2]
        
        res = audio_proc.compute_similarity(model, feature_extractor, "path1", "path2", threshold=0.5)
        
        assert res['similarity'] == pytest.approx(1.0)
        assert res['decision'] is True
        
        # Completely different vectors
        v3 = torch.tensor([1.0, 0.0])
        v4 = torch.tensor([0.0, 1.0])
        mock_extract.side_effect = [v3, v4]
        
        res = audio_proc.compute_similarity(model, feature_extractor, "path3", "path4", threshold=0.5)
        assert res['similarity'] == pytest.approx(0.0)
        assert res['decision'] is False

@patch('torch.load')
@patch('audioproc.wsi.load_trained_model')
def test_init_model(mock_load_wsi, mock_torch_load, tmp_path):
    """Test model initialization with mocks."""
    mock_checkpoint = {'best_thresh': 0.85}
    mock_torch_load.return_value = mock_checkpoint
    
    mock_model = MagicMock()
    mock_fe = MagicMock()
    mock_load_wsi.return_value = (mock_model, mock_fe)
    
    # Create a dummy file to pass the exists check
    dummy_pth = tmp_path / "best_model.pth"
    dummy_pth.write_text("Dummy content")
    
    model, fe, thresh = audio_proc.init_model(str(dummy_pth))
    
    assert model == mock_model
    assert fe == mock_fe
    assert thresh == 0.85
    mock_torch_load.assert_called_once()

@patch('audioproc.interface._load_audio')
@patch('audioproc.interface._extract_embedding')
@patch('audioproc.interface._compute_similarity_saliency')
@patch('matplotlib.pyplot.savefig')
def test_visualize_waveform_similarity(mock_savefig, mock_saliency, mock_extract, mock_load, tmp_path):
    """Test waveform visualization flow."""
    # Mock data
    mock_load.return_value = np.zeros(16000)
    mock_extract.return_value = np.zeros(128)
    mock_saliency.return_value = (np.zeros(100), np.linspace(0, 1, 100))
    
    # Set IMG_DIR to a temp path
    audio_proc.IMG_DIR = str(tmp_path)
    
    model = MagicMock()
    fe = MagicMock()
    
    out_path = audio_proc.visualize_waveform_similarity(model, fe, "a1.wav", "a2.wav")
    
    assert "waveform.png" in out_path
    mock_savefig.assert_called_once()
