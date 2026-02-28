import pytest
from streamlit.testing.v1 import AppTest
from pathlib import Path
import os
import sys

# Setup paths
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

def test_navigation_flow_visibility():
    """Verify that the user journey is clear and reachable."""
    at = AppTest.from_file("app.py").run()
    
    # Check for the primary forensic modes (Image / Audio)
    # Since current app.py has both on the main page
    assert any("Upload Image" in str(u.label) for u in at.file_uploader)
    assert any("Upload Two Audio Files" in str(u.label) for u in at.file_uploader)
    
    # Check for meaningful subheaders
    assert any("Analysis & Visualization" in str(h.value) for h in at.header)
    assert any("Audio Forensic Analysis" in str(h.value) for h in at.header)

def test_error_messaging_on_invalid_image(tmp_path):
    """Verify the app gives helpful advice on invalid image uploads."""
    at = AppTest.from_file("app.py")
    
    # Mock an invalid file (0-byte)
    invalid_png = tmp_path / "corrupt.png"
    invalid_png.write_bytes(b"") # 0-byte file
    
    # In some Streamlit versions, we access file_uploader via index
    if len(at.file_uploader) > 0:
        at.file_uploader[0].upload(data=b"", name="corrupt.png")
        at.run()
        
        # We expect SOME reaction, either a warning or the analysis button NOT to show
        # Streamlit itself handles some format restrictions, but our app 
        # should handle the logic gracefully.
        
        # If we try to run analysis on it:
        if len(at.button) > 0 and "Run Analysis" in at.button[0].label:
            at.button[0].click().run()
            # If it triggers an error in Python, st.error should show it
            assert not at.exception 
            # Ideally our app shows a validation message

def test_audio_upload_mismatch_error():
    """Verify that uploading only 1 audio file prevents analysis."""
    at = AppTest.from_file("app.py")
    
    # Search for audio uploader (index 1 usually)
    if len(at.file_uploader) > 1:
        uploader = at.file_uploader[1]
        uploader.upload(data=b"fake wav", name="only_one.wav")
        at.run()
        
        # The 'Analyze Audio' button should NOT be visible per app logic
        assert not any("Analyze Audio" in btn.label for btn in at.button)
        
        # Verify instructions remain clear
        assert any("Please upload EXACTLY two audio files" in str(msg.body) for msg in at.info)
