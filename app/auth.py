# CAT-Net-Webapp/app/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from . import db
# Create a Blueprint instance for authentication routes
auth = Blueprint('auth', __name__, url_prefix='/auth')
@auth.route('/login', methods=['GET', 'POST'])
def login():
    ssn_id=session.get('session_id')
    if ssn_id is None:
        return'Invalid session.',404#TODO improve error reporting.
    if request.method=='GET':
        return render_template('auth/login.html')
    #Extract user credentials.
    usrname=request.form.get('username')
    pwd=request.form.get('password')
    if not usrname or not pwd:
        return'Missing username or password.'
    #Authenticate user. 
    if db.usr_auth(usrname,pwd)is False:
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
    ssn_id=session.get('session_id')
    if ssn_id is None:
        return'Invalid session.',404#TODO improve error reporting.
    if request.method=='GET':
        return render_template('auth/signup.html')
    #Extract user credentials.
    usrname=request.form.get('username')
    pwd=request.form.get('password')
    if not usrname or not pwd:
        return'Missing username or password.'
    #Register new user.
    match db.usr_reg(usrname,pwd):
        case db.RET.ERR_USRNAME_TAKEN:
            flash('Username taken.','danger')
            return render_template('auth/signup')
        case db.RET.ERR_INVALID_INPUT:
            flash('Invalid username or password.','danger')
            return render_template('auth/signup')
    #Create new session.
    usr_id=db.usr_id(usrname)
    ssn_id=db.ssn_new(request.remote_addr)
    if ssn_id is None:
        flash('Failed to create new session.')
        return render_template('auth/signup')
    if not db.ssn_usr_bind(sid=ssn_id,uid=usr_id):
        flash('Failed to bind new user session.','danger')
        return render_template('auth/signup.html')
    session['session_id']=ssn_id
    return redirect(url_for('main.dashboard'))
@auth.route('/logout')
def logout():
    ssn_id=session.get('session_id')
    if ssn_id is None:
        return'Invalid session.',404#TODO improve error reporting.
    #Close session & start a new one.
    db.ssn_rm(ssn_id)#temporary solution.
    session['session_id']=None
    flash('Logged out successfully.','info')
    return redirect(url_for('main.index'))
#TODO Implement robust batch clean up for sessions.
