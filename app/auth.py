from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from . import db

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    ssn_id = session.get('session_id')
    if ssn_id is None:
        return 'Invalid session.', 404

    if request.method == 'GET':
        return render_template('auth/login.html')

    usrname = request.form.get('username')
    pwd = request.form.get('password')

    if not usrname or not pwd:
        flash('Missing username or password.', 'danger')
        return render_template('auth/login.html')

    if db.usr_auth(usrname, pwd) is False:
        flash('Invalid username or password.', 'danger')
        return render_template('auth/login.html')

    usr_id = db.usr_id(usrname)

    if not db.ssn_usr_bind(ssn_id, usr_id):
        return 'Internal error. Try again later.', 500

    return redirect(url_for('main.dashboard'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    ssn_id = session.get('session_id')
    if ssn_id is None:
        return 'Invalid session.', 404

    if request.method == 'GET':
        return render_template('auth/signup.html')

    usrname = request.form.get('username')
    pwd = request.form.get('password')

    if not usrname or not pwd:
        flash('Missing username or password.', 'danger')
        return render_template('auth/signup.html')

    result = db.usr_reg(usrname, pwd)

    if result == db.RET.ERR_USRNAME_TAKEN:
        flash('Username taken.', 'danger')
        return render_template('auth/signup.html')

    if result == db.RET.ERR_INVALID_INPUT:
        flash('Invalid username or password.', 'danger')
        return render_template('auth/signup.html')

    usr_id = db.usr_id(usrname)
    ssn_id, _ = db.ssn_new(request.remote_addr)

    if not db.ssn_usr_bind(ssn_id, usr_id):
        flash('Failed to bind new user session.', 'danger')
        return render_template('auth/signup.html')

    session['session_id'] = ssn_id
    return redirect(url_for('main.dashboard'))


@auth.route('/logout')
def logout():
    ssn_id = session.get('session_id')
    if ssn_id is None:
        return 'Invalid session.', 404

    db.ssn_rm(ssn_id)
    session['session_id'] = None

    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.index'))
