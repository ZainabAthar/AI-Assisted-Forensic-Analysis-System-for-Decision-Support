from flask import (
    Blueprint, render_template, request, current_app,
    redirect, url_for, flash, send_from_directory, session
)
from werkzeug.utils import secure_filename
from . import db
import os

from .catnet_core.analysis_service import analyze_image_with_catnet

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route('/')
def index():
    ssn_id = session.get('session_id')

    if ssn_id is None:
        ssn_id, _ = db.ssn_new(request.remote_addr)  # FIX: unpack tuple
        session['session_id'] = ssn_id

    return render_template(
        'index.html',
        is_logged_in=db.ssn_usr_id(ssn_id) is not None
    )


@main.route('/dashboard')
def dashboard():
    ssn_id = session.get('session_id')
    if ssn_id is None:
        return 'Invalid session.', 404

    usr_id = db.ssn_usr_id(ssn_id)
    usrname = db.usr_name(usr_id)

    return render_template(
        'dashboard.html',
        username=usrname,
        is_logged_in=usr_id is not None
    )


@main.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    predictions_folder = os.path.join(
        current_app.root_path,
        'catnet_core',
        'predictions'
    )
    return send_from_directory(
        directory=predictions_folder,
        path=filename,
        as_attachment=True
    )


@main.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('main.dashboard'))

    file = request.files['file']

    if file.filename == '':
        flash('No selected file.', 'danger')
        return redirect(url_for('main.dashboard'))

    if not (file and allowed_file(file.filename)):
        flash('Invalid file type.', 'danger')
        return redirect(url_for('main.dashboard'))

    filename = secure_filename(file.filename)
    upload_path = os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        filename
    )
    file.save(upload_path)

    ssn_id = session.get('session_id')
    usr_id = db.ssn_usr_id(ssn_id)
    usrname = db.usr_name(usr_id)

    try:
        analysis_results = analyze_image_with_catnet(
            upload_path,
            user_id=usrname
        )

        if usrname:
            flash('Analysis complete. Data stored in your profile.', 'success')
        else:
            flash(
                'Analysis complete. Since you are not logged in, this report will not be saved.',
                'warning'
            )

        return render_template(
            'report.html',
            filename=filename,
            image_url=url_for('static', filename=f'uploads/{filename}'),
            heatmap_url=url_for(
                'static',
                filename=analysis_results['heatmap_url_path']
            ),
            report_data=analysis_results,
            username=usrname if usrname else 'guest',
            is_logged_in=usrname is not None
        )

    except Exception as e:
        flash(f'Analysis failed due to a model error: {e}', 'danger')
        current_app.logger.error(f"Analysis Error: {e}")
        return redirect(url_for('main.dashboard'))
