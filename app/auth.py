# CAT-Net-Webapp/app/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from . import db
# Create a Blueprint instance for authentication routes
auth = Blueprint('auth', __name__, url_prefix='/auth')
@auth.route('/login', methods=['GET', 'POST'])
def login():
    ssn_id=session.get('session_id')
    if not ssn_id:
        return'Invalid session.',404#TODO improve error reporting.
    if request.method=='GET':
        return render_template('auth/login.html')
    #Extract user credentials.
    usrname=request.form.get('username')
    pwd=request.form.get('password')
    if not usrname or not pwd:
        return'Missing username or password.'
    #Authenticate user. 
    if not db.usr_auth(usrname,pwd):
        flash('Invalid username or password.','danger')#TODO: more verbose errors. 
        return render_template('auth/login.html')
    #Update session.
    usr_id=db.usr_id(usrname)
    ret=db.ssn_usr_bind(ssn_id,usr_id)
    if not ret:
        return'Internal error. Try again later.'#TODO improve error reporting.
    return redirect(url_for('main.dashboard'))
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method=='GET':
        return render_template('auth/signup.html')
    #Extract user credentials.
    usrname=request.form.get('username')
    pwd=request.form.get('password')
    if not usrname or not pwd:
        return'Missing username or password.'
    #Register new user.
    if not db.usr_reg(usrname,pwd):
        return redirect(url_for('auth.signup'))
    #Create new session.
    ssn_id=db.ssn_new(usrname)
    session['session_id']=ssn_id
    return redirect(url_for('main.dashboard'))
@auth.route('/logout')
def logout():
    ssn_id=session.get('session_id')
    if not ssn_id:#Invalid session check.
        return'Invalid session.',404#TODO improve error reporting.
    #Close session & start a new one.
    db.ssn_rm(ssn_id)
    session['session_id']=None
    flash('Logged out successfully.','info')
    return redirect(url_for('main.index'))
#TODO Implement robust batch clean up for sessions.
