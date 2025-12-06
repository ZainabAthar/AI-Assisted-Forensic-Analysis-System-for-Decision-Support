# CAT-Net-Webapp/app/catnet_core/__init__.py

# By importing the analyze_image_with_catnet function here:
# 1. We make it easily accessible in app/routes.py (e.g., from app.catnet_core import analyze_image_with_catnet).
# 2. MOST IMPORTANTLY: The model loading logic (load_catnet_model()) inside 
#    analysis_service.py is executed when this module is imported during the 
#    Flask startup process, ensuring the model is ready globally.

try:
    from .analysis_service import analyze_image_with_catnet
except ImportError as e:
    # If the core logic fails to import, this likely means dependencies (lib, Splicing) 
    # are missing or imports inside those submodules are broken.
    print(f"CRITICAL: Failed to initialize CAT-Net Core: {e}")
    # We still define the function so the rest of the app doesn't crash on import, 
    # but analysis attempts will fail later.
    def analyze_image_with_catnet(*args, **kwargs):
        raise Exception("CAT-Net Model Core failed to initialize due to critical import errors.")