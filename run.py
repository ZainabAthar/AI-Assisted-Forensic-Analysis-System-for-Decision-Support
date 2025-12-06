# CAT-Net-Webapp/run.py (FINAL MODIFIED VERSION)

import sys
import os
from pathlib import Path

# --- THE OVERPOWER FIX: Adjusting System Path ---
# Calculate the path to app/catnet_core/
BASE_DIR = Path(__file__).parent
CATNET_CORE_PATH = str(BASE_DIR / 'app' / 'catnet_core')

# Add app/catnet_core to the Python path so all internal imports 
# (like 'from lib import X') work as absolute imports.
if CATNET_CORE_PATH not in sys.path:
    sys.path.insert(0, CATNET_CORE_PATH)
# ------------------------------------------------

from app import create_app
from dotenv import load_dotenv

# Load environment variables (optional, but good practice)
load_dotenv() 

try:
    print("\n--- Attempting to create Flask app and load core modules... ---")
    print(f"--- System Path Root Added: {CATNET_CORE_PATH} ---")

    # create_app() is where the model is initialized.
    app = create_app() 
    
    print("--- App created successfully. Starting server. ---")

    if __name__ == '__main__':
        app.run(debug=True)

except Exception as e:
    # This trap will now likely catch YAML parsing errors or PyTorch loading errors, not import errors.
    print("\n\n#################################################################")
    print(f"FATAL STARTUP ERROR: {type(e).__name__}: {e}")
    print("A critical error occurred before the server could start.")
    print("#################################################################\n\n")
    sys.exit(1)