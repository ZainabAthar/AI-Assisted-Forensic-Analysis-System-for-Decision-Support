# CAT-Net-Webapp/app/__init__.py

from flask import Flask, session, g
import os

def create_app(config_object=None):
    app = Flask(__name__)

    # ---------------- CONFIG ----------------
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY',
        'default_fallback_secret_key_if_not_set'
    )

    app.config['UPLOAD_FOLDER'] = os.path.join(
        app.root_path, 'static', 'uploads'
    )

    app.config['DB_PATH'] = os.path.join(
        app.root_path, 'database.db'
    )

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ---------------- BLUEPRINTS ----------------
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # ---------------- DB HOOKS ----------------
    from .db import close_db
    app.teardown_appcontext(close_db)

    from . import db

    # ---------------- GLOBAL USER LOADER ----------------
    @app.before_request
    def load_logged_in_user():
        g.user = None
        ssn_id = session.get('session_id')

        if ssn_id:
            usr_id = db.ssn_usr_id(ssn_id)
            if usr_id:
                g.user = {
                    "id": usr_id,
                    "username": db.usr_name(usr_id)
                }

    # 🔴 THIS WAS THE ROOT BUG
    return app
