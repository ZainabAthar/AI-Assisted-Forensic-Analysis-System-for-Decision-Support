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

# Import required modules
from forensic_report_integration import generate_forensic_report_from_analysis
from audioproc import interface as audio_proc
from audio_report_generator import AudioForensicReportGenerator

@pytest.fixture
def mock_npz(tmp_path):
    """Creates a mock .npz file for image analysis."""
    npz_path = tmp_path / "test_image.npz"
    data = {
        'map': np.random.rand(100, 100),
        'conf': np.random.rand(100, 100),
        'score': np.array(0.75),
        'imgsize': np.array([100, 100])
    }
    np.savez(npz_path, **data)
    return str(npz_path)

@patch('reportlab.platypus.SimpleDocTemplate.build')
def test_image_to_report_integration(mock_build, mock_npz, tmp_path):
    """
    Core Integration 1: Image Analysis Result (.npz) -> Forensic PDF Report
    """
    output_pdf = tmp_path / "image_report.pdf"
    
    success, message = generate_forensic_report_from_analysis(
        npz_file_path=mock_npz,
        output_path=str(output_pdf),
        image_path=None # Optional for test
    )
    
    assert success is True
    # In my experience, generate_forensic_report_from_analysis calls generator.create_pdf_report
    # which eventually calls doc.build()
    assert mock_build.called

@patch('audioproc.interface._load_audio')
@patch('audioproc.interface._extract_embedding')
@patch('audioproc.interface._compute_similarity_saliency')
@patch('reportlab.platypus.SimpleDocTemplate.build')
def test_audio_to_report_integration(mock_build, mock_sal, mock_ext, mock_load, tmp_path):
    """
    Core Integration 2: Audio Analysis -> Saliency Visualizations -> Forensic PDF Report
    """
    # Setup paths
    wave_path = tmp_path / "wave.png"
    spec_path = tmp_path / "spec.png"
    report_pdf = tmp_path / "audio_report.pdf"
    
    # Create dummy images so PDF generation doesn't crash on file existence check
    wave_path.write_text("fake image")
    spec_path.write_text("fake image")
    
    # 1. Run Analysis (Mocked)
    model, fe = MagicMock(), MagicMock()
    mock_load.return_value = np.zeros(100)
    mock_ext.return_value = torch.zeros(128)
    mock_sal.return_value = (np.zeros(100), np.linspace(0, 1, 100))
    
    res = audio_proc.compute_similarity(model, fe, "a1.wav", "a2.wav", threshold=0.5)
    
    # 2. Generate Report
    report_gen = AudioForensicReportGenerator()
    success, msg = report_gen.create_pdf_report(
        output_path=str(report_pdf),
        similarity_score=res['similarity'],
        decision="Same Speaker" if res['decision'] else "Different Speakers",
        waveform_path=str(wave_path),
        spectrogram_path=str(spec_path),
        audio_names=["test1.wav", "test2.wav"]
    )
    
    assert success is True
    assert mock_build.called
