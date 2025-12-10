from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Club, Event
from extensions import db
from datetime import datetime, timezone

club_bp = Blueprint('club', __name__)

def check_club_role():
    if current_user.role != 'club' or current_user.role != 'admin':
        flash('Access denied. Club Officer account required.', 'danger')
        return False
    return True

@club_bp.route('/dashboard')
@login_required
def dashboard():
    if not check_club_role():
        return redirect(url_for('index'))
    
    # 1. Find the club associated with this user
    # NOTE: You need to decide how to link a User to a Club they OWN.
    # For this MVP, we can assume the User's name matches the Club, 
    # OR we just let them manage *any* club for the demo (easier).
    
    # Simple Demo Logic: Let them manage the "Machine Learning Club" as an example
    # In a real app, you'd have a 'club_id' column in the User table.
    my_club = Club.query.filter_by(name="Machine Learning Club").first()

    return render_template('club/dashboard.html', club=my_club)

@club_bp.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if not check_club_role():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Logic to create event
        # ... get other fields ...
        
        flash('Event created successfully!', 'success')
        return redirect(url_for('club.dashboard'))
        
    return render_template('club/create_event.html')