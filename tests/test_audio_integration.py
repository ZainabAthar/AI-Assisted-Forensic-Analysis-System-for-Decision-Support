import pytest
import os
import sys
import torch
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup paths
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "Report generation" / "core"))

from audioproc import interface as audio_proc
from audio_report_generator import AudioForensicReportGenerator

@pytest.fixture
def sample_audios():
    """Returns paths to real audio files found in the project."""
    a1 = "temp_ui/input/harvard.wav"
    a2 = "temp_ui/input/LanceBlair_Raw_Audio_Voiceover_2026.wav"
    return str(project_root / a1), str(project_root / a2)

@patch('audioproc.wsi.WhisperModel')
@patch('torch.load')
def test_audio_to_report_integration(mock_torch_load, mock_whisper, sample_audios, tmp_path):
    """
    End-to-end integration test: 
    Audio files -> Similarity Analysis -> Visualizations -> PDF Report
    """
    a1, a2 = sample_audios
    if not os.path.exists(a1) or not os.path.exists(a2):
        pytest.skip("Sample audio files not found.")
    
    # Mock model and checkpoint
    mock_torch_load.return_value = {'best_thresh': 0.6}
    
    # Mock whisper model for inference
    mock_instance = MagicMock()
    # Mock the embedding extraction (returns a vector of size 128)
    mock_embeddings = MagicMock()
    mock_embeddings.last_hidden_state = torch.randn(1, 50, 512)
    mock_instance.return_value = mock_embeddings
    mock_whisper.from_pretrained.return_value = mock_instance
    
    # Set output directories to temp
    audio_proc.IMG_DIR = str(tmp_path / "viz")
    os.makedirs(audio_proc.IMG_DIR, exist_ok=True)
    
    # 1. Run Analysis (using actual interface functions but mocked inference)
    # Since we're mocking torch.load and Whisper, we'll use a mocked model object
    model = MagicMock()
    fe = MagicMock()
    
    # We'll need to patch _extract_embedding to avoid real model weights
    with patch('audioproc.interface._extract_embedding') as mock_ext:
        mock_ext.return_value = torch.randn(128)
        
        # 2. Compute similarity
        res = audio_proc.compute_similarity(model, fe, a1, a2, threshold=0.6)
        assert 'similarity' in res
        
        # 3. Generate Visualizations
        # Mocking _compute_similarity_saliency as it's very heavy/complex
        with patch('audioproc.interface._compute_similarity_saliency') as mock_sal:
            mock_sal.return_value = (np.random.rand(100), np.linspace(0, 1, 100))
            
            wave_path = audio_proc.visualize_waveform_similarity(model, fe, a1, a2)
            spec_path = audio_proc.visualize_spectrogram_similarity(model, fe, a1, a2)
            
            assert os.path.exists(wave_path)
            assert os.path.exists(spec_path)
            
            # 4. Generate PDF Report
            report_gen = AudioForensicReportGenerator()
            report_pdf = tmp_path / "integration_report.pdf"
            
            success, msg = report_gen.create_pdf_report(
                output_path=str(report_pdf),
                similarity_score=res['similarity'],
                decision="Same Speaker" if res['decision'] else "Different Speakers",
                waveform_path=wave_path,
                spectrogram_path=spec_path,
                audio_names=[os.path.basename(a1), os.path.basename(a2)]
            )
            
            assert success is True
            assert os.path.exists(report_pdf)
            assert os.path.getsize(report_pdf) > 0
