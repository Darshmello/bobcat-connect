from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from flask_bcrypt import Bcrypt

auth = Blueprint('auth', __name__)
bcrypt = Bcrypt()

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

def redirect_by_role(user):
    """Helper function to redirect user based on their role"""
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
        
        # Validate @ucmerced.edu email
        if not email.endswith(UCMERCED_DOMAIN):
            flash(INVALID_EMAIL_MSG, FLASH_DANGER)
            return redirect(url_for('auth.register'))
        
        # Validate role
        if role not in VALID_ROLES:
            flash(INVALID_ROLE_MSG, FLASH_DANGER)
            return redirect(url_for('auth.register'))
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash(EMAIL_ALREADY_REGISTERED, FLASH_DANGER)
            return redirect(url_for('auth.register'))
        
        # Hash password and create user
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