# CAT-Net-Webapp/app/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request

# Create a Blueprint instance for authentication routes
auth = Blueprint('auth', __name__, url_prefix='/auth')

# --- Placeholder User/Auth Logic ---
# Global state to mock a logged-in user (DO NOT USE IN PRODUCTION)
DUMMY_USER = {'is_logged_in': False, 'username': 'Guest'}

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Retrieve current login status for template rendering
    is_logged_in = DUMMY_USER.get('is_logged_in', False)
    
    if is_logged_in:
        # If already logged in, go to dashboard
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        # Placeholder logic for POST submission
        DUMMY_USER['is_logged_in'] = True
        
        # Safely get username from form data
        username = request.form.get('username', 'TestUser') 
        DUMMY_USER['username'] = username
        
        flash(f'Successfully logged in as {username}!', 'success')
        return redirect(url_for('main.dashboard')) 
        
    # FIX: Pass the necessary template context (user and status)
    return render_template('auth/login.html', 
                           user=DUMMY_USER, 
                           is_logged_in=is_logged_in)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    is_logged_in = DUMMY_USER.get('is_logged_in', False)
    
    if request.method == 'POST':
        # Placeholder: assume successful registration and redirect to login
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    # FIX: Pass the necessary template context
    return render_template('auth/signup.html', 
                           user=DUMMY_USER, 
                           is_logged_in=is_logged_in)

@auth.route('/logout')
def logout():
    DUMMY_USER['is_logged_in'] = False
    DUMMY_USER['username'] = 'Guest'
    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.index'))