import pytest
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Setup paths
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "Report generation" / "core"))

from reportlab.lib import colors
from audio_report_generator import AudioForensicReportGenerator

@pytest.fixture
def generator():
    return AudioForensicReportGenerator()

def test_report_generation_flow(generator, tmp_path):
    """Test the PDF generation flow with dummy data and mocks."""
    output_pdf = tmp_path / "test_audio_report.pdf"
    waveform_img = tmp_path / "wf.png"
    spectrogram_img = tmp_path / "spec.png"
    
    # Create dummy images
    waveform_img.write_text("fake image")
    spectrogram_img.write_text("fake image")
    
    with patch('reportlab.platypus.SimpleDocTemplate.build') as mock_build:
        success, msg = generator.create_pdf_report(
            output_path=str(output_pdf),
            similarity_score=0.95,
            decision="Same Speaker",
            waveform_path=str(waveform_img),
            spectrogram_path=str(spectrogram_img),
            audio_names=["audio1.wav", "audio2.wav"]
        )
        
        assert success is True
        assert "successfully" in msg
        mock_build.assert_called_once()

def test_custom_styles_initialization(generator):
    """Ensure custom styles are correctly initialized."""
    assert generator.title_style.fontSize == 24
    assert generator.heading_style.textColor.hexval() == colors.HexColor('#1f4788').hexval()
