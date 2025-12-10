from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Club, User
from extensions import db

admin_bp = Blueprint('admin', __name__)

def check_admin_role():
    if current_user.role != 'admin':
        flash('Access denied. Admin account required.', 'danger')
        return False
    return True

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not check_admin_role():
        return redirect(url_for('index'))
    
    # Admin Stats
    total_users = User.query.count()
    total_clubs = Club.query.count()
    pending_clubs = Club.query.filter_by(verified=False).all()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_clubs=total_clubs,
                         pending_clubs=pending_clubs)

@admin_bp.route('/verify_club/<int:club_id>')
@login_required
def verify_club(club_id):
    if not check_admin_role():
        return redirect(url_for('index'))
        
    club = Club.query.get_or_404(club_id)
    club.verified = True
    db.session.commit()
    flash(f'{club.name} has been verified!', 'success')
    return redirect(url_for('admin.dashboard'))