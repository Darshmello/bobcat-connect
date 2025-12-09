from flask import Flask, render_template, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from models import db, User
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bobcat.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please login to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
from blueprints.auth import auth
from blueprints.student import student

app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(student, url_prefix='/student')

# Will be created by Neil/Darsh
try:
    from blueprints.club import club
    app.register_blueprint(club, url_prefix='/club')
except ImportError:
    pass

try:
    from blueprints.admin import admin
    app.register_blueprint(admin, url_prefix='/admin')
except ImportError:
    pass

@app.route('/')
def index():
    if current_user.is_authenticated:
        # Redirect to appropriate dashboard
        if current_user.role == 'student':
            return redirect(url_for('student.dashboard'))
        elif current_user.role == 'club':
            return redirect(url_for('club.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
    return render_template('index.html')

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created!")

if __name__ == '__main__':
    app.run(debug=True)