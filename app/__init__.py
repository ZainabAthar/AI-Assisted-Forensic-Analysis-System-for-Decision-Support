# CAT-Net-Webapp/app/__init__.py

from flask import Flask
import os

def create_app(config_object=None):
    # Initialize the Flask app instance
    app = Flask(__name__)
    
    # Configuration setup
    # Gets SECRET_KEY from environment or uses a fallback
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_fallback_secret_key_if_not_set')
    
    # Define where uploads go (in static/uploads)
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    
    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- Register Blueprints (Modules) ---

    # 1. Authentication module (Login, Signup)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    # 2. Core application module (Dashboard, Analyze)
    # Note: We assume app/routes.py contains a blueprint named 'main'
    from .routes import main as main_blueprint 
    app.register_blueprint(main_blueprint)

    # Note on Model Loading: 
    # The CAT-Net model initialization is triggered by the import 
    # statement within app/routes.py, which calls load_catnet_model() 
    # from app/catnet_core/analysis_service.py. This ensures the model 
    # loads before the first web request is processed.
    
    return app