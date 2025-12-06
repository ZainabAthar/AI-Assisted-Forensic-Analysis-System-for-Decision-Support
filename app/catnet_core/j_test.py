# app/catnet_core/jpegio_test.py

import sys
import os
from pathlib import Path

# Ensure the sys.path fix is replicated here for absolute imports
BASE_DIR = Path(__file__).parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

print(f"Testing environment: {sys.version}")
print(f"Path used for absolute imports: {BASE_DIR}")
print("-" * 30)

try:
    # Attempt the problematic import
    import jpegio
    print("SUCCESS: Module 'jpegio' found and imported.")
    
    # Attempt to access the specific function that failed (this triggers the C linkage)
    if hasattr(jpegio, 'read'):
        print("SUCCESS: jpegio has the 'read' attribute.")
        
        # We can't actually read a file here without a path, but accessing the attribute confirms the module structure.
        
    else:
        print("FAILURE: jpegio module found, BUT missing the 'read' function (C linkage failed).")
        
except ImportError as e:
    print(f"FAILURE: Cannot import jpegio. (Reason: {e})")
except Exception as e:
    print(f"FAILURE: An unexpected error occurred: {e}")