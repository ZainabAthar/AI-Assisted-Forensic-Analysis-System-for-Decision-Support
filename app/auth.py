# CAT-Net-Webapp/app/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from . import db
# Create a Blueprint instance for authentication routes
auth = Blueprint('auth', __name__, url_prefix='/auth')
@auth.route('/login', methods=['GET', 'POST'])
def login():
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
    #Create new session and return ID.
    ssn_id=db.ssn_new(usrname) 
    if not ssn_id:#expected to be unreachable.
        print('Failed to create session.')
        flash('Failed to create session.')
        return render_template('auth/login.html')
    session['session_id']=ssn_id
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
    #TODO.
    ssn_id=session['session_id']
    if not ssn_id:
        flash('Invalid session.')
        return url_for('main.index')
    db.ssn_rm(ssn_id)
    flash('Logged out successfully.','info')
    return redirect(url_for('main.index'))
