# CAT-Net-Webapp/app/routes.py
from flask import Blueprint, render_template, request, current_app, redirect, url_for, flash, send_from_directory,session
from werkzeug.utils import secure_filename
from . import db
import os
# --- MODEL/SERVICE IMPORT (This path is CORRECT) ---
from .catnet_core.analysis_service import analyze_image_with_catnet 
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
    return render_template('index.html',is_logged_in=not db.ssn_usr_id(session['session_id']))
@main.route('/dashboard')
def dashboard():
    """Main page for uploading images."""
    return render_template('dashboard.html',is_logged_in=not db.ssn_usr_id(session['session_id']))
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
    if not(file and file.filename and allowed_file(file.filename)):
        flash('Invalid file type.', 'danger')
        return redirect(url_for('main.dashboard'))
    filename = secure_filename(file.filename)
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)
    # Determine user ID for saving the prediction map
    ssn_id=request.form.get('session_id')
    usr_id=db.ssn_usr_id(ssn_id)
    usrname=db.usr_name(usr_id)#usrname=None if guest user.
    # 4. Run Model Inference
    try:
        # Pass the physical path of the uploaded image
        analysis_results = analyze_image_with_catnet(upload_path,user_id=usrname)
        # 5. Handle Storage/Report generation
        if usrname:#if logged in.
            # TODO: Store results (filename, heatmap_url_path, prediction) in DB
            #db.media_new(ssn_id,filename)
            flash('Analysis complete. Data stored in your profile.', 'success')
        else:#or else guest user.
            flash('Analysis complete. Since you are not logged in, this report will not be saved.', 'warning')
        # Pass image URL and the report data (including the heatmap path)
        # CRITICAL FIX: Pass 'user' and 'is_logged_in' for the base templates (layout/navbar)
        return render_template('report.html', 
                               filename=filename,
                               image_url=url_for('static', filename=f'uploads/{filename}'),
                               heatmap_url=url_for('static', filename=analysis_results['heatmap_url_path']),
                               report_data=analysis_results,
                               username=usrname if usrname else'guest') # <-- ADDED
    except Exception as e:
        # We catch ALL exceptions here, including model loading failures.
        flash(f'Analysis failed due to a model error: {e}', 'danger')
        current_app.logger.error(f"Analysis Error: {e}")
        return redirect(url_for('main.dashboard'))
