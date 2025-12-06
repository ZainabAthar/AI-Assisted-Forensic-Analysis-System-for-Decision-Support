# CAT-Net-Webapp/app/routes.py

from flask import Blueprint, render_template, request, current_app, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
# --- MODEL/SERVICE IMPORT (This path is CORRECT) ---
from .catnet_core.analysis_service import analyze_image_with_catnet 

# Import the dummy user status from auth.py
from .auth import DUMMY_USER 

# Define the Blueprint for the main application routes
main = Blueprint('main', __name__)

# --- Configuration ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    """Home page/Landing page."""
    is_logged_in = DUMMY_USER.get('is_logged_in', False)
    return render_template('index.html', user=DUMMY_USER, is_logged_in=is_logged_in)

@main.route('/dashboard')
def dashboard():
    """Main page for uploading images."""
    is_logged_in = DUMMY_USER.get('is_logged_in', False)
    return render_template('dashboard.html', user=DUMMY_USER, is_logged_in=is_logged_in)

@main.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """Securely serves files from the predictions directory for download."""
    
    predictions_folder = os.path.join(current_app.root_path, 'catnet_core', 'predictions')
    
    return send_from_directory(
        directory=predictions_folder, 
        path=filename, 
        as_attachment=True
    )

@main.route('/analyze', methods=['POST'])
def analyze():
    """Handles image upload and runs the CAT-Net model."""
    
    # 1. Check if the POST request has the file part
    if 'file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    file = request.files['file']
    
    # 2. Check if user selected a file
    if file.filename == '':
        flash('No selected file.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    # 3. Process and save the file
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        # Determine user ID for saving the prediction map
        user_id = DUMMY_USER['username'] if DUMMY_USER['is_logged_in'] else 'guest'

        # 4. Run Model Inference
        try:
            # Pass the physical path of the uploaded image
            analysis_results = analyze_image_with_catnet(upload_path, user_id=user_id)
            
            # 5. Handle Storage/Report generation
            is_logged_in = DUMMY_USER.get('is_logged_in', False)
            if is_logged_in:
                # TODO: Store results (filename, heatmap_url_path, prediction) in DB
                flash('Analysis complete. Data stored in your profile.', 'success')
            else:
                flash('Analysis complete. Since you are not logged in, this report will not be saved.', 'warning')
            
            # Pass image URL and the report data (including the heatmap path)
            # CRITICAL FIX: Pass 'user' and 'is_logged_in' for the base templates (layout/navbar)
            return render_template('report.html', 
                                   filename=filename,
                                   image_url=url_for('static', filename=f'uploads/{filename}'),
                                   heatmap_url=url_for('static', filename=analysis_results['heatmap_url_path']),
                                   report_data=analysis_results,
                                   user=DUMMY_USER,  # <-- ADDED
                                   is_logged_in=is_logged_in) # <-- ADDED
            
        except Exception as e:
            # We catch ALL exceptions here, including model loading failures.
            flash(f'Analysis failed due to a model error: {e}', 'danger')
            current_app.logger.error(f"Analysis Error: {e}")
            return redirect(url_for('main.dashboard'))

    flash('Invalid file type.', 'danger')
    return redirect(url_for('main.dashboard'))