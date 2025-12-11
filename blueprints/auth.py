from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, bcrypt
from models import User

auth = Blueprint('auth', __name__)

# Constants
EMAIL_ALREADY_REGISTERED = 'Email already registered'
INVALID_EMAIL_MSG = 'Must use @ucmerced.edu email'
INVALID_ROLE_MSG = 'Invalid role selection'
INVALID_CREDENTIALS_MSG = 'Invalid email or password'
REGISTRATION_SUCCESS_MSG = 'Registration successful! Please login.'
LOGOUT_SUCCESS_MSG = 'Logged out successfully'
FLASH_DANGER = 'danger'
FLASH_SUCCESS = 'success'
UCMERCED_DOMAIN = '@ucmerced.edu'
VALID_ROLES = ['student', 'club', 'admin']

# --- NEW: SECURITY CODES ---
ADMIN_CODES = ['darshisadmin', 'neilisadmin']

def redirect_by_role(user):
    role_redirects = {
        'student': 'student.dashboard',
        'club': 'club.dashboard',
        'admin': 'admin.dashboard'
    }
    return redirect(url_for(role_redirects.get(user.role, 'index')))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        role = request.form.get('role')
        
        # 1. Validate Email
        if not email.endswith(UCMERCED_DOMAIN):
            flash(INVALID_EMAIL_MSG, FLASH_DANGER)
            return redirect(url_for('auth.register'))
        
        # 2. Validate Role
        if role not in VALID_ROLES:
            flash(INVALID_ROLE_MSG, FLASH_DANGER)
            return redirect(url_for('auth.register'))
        
        # 3. NEW: Validate Admin Passcode
        if role == 'admin':
            admin_code = request.form.get('admin_code')
            if admin_code not in ADMIN_CODES:
                flash('Incorrect Admin Passcode. Permission denied.', FLASH_DANGER)
                return redirect(url_for('auth.register'))

        # 4. Check if user exists
        if User.query.filter_by(email=email).first():
            flash(EMAIL_ALREADY_REGISTERED, FLASH_DANGER)
            return redirect(url_for('auth.register'))
        
        # 5. Create User
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(email=email, password_hash=hashed_pw, role=role)
        db.session.add(user)
        db.session.commit()
        
        flash(REGISTRATION_SUCCESS_MSG, FLASH_SUCCESS)
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_by_role(current_user)
    
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect_by_role(user)
        else:
            flash(INVALID_CREDENTIALS_MSG, FLASH_DANGER)
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(LOGOUT_SUCCESS_MSG, FLASH_SUCCESS)
    return redirect(url_for('index'))