from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Event, RSVP, Club, ClubFollower
from datetime import datetime, timezone

student = Blueprint('student', __name__)

# Constants
ACCESS_DENIED_MSG = 'Access denied'
ACCESS_DENIED_CATEGORY = 'danger'
ROLE_STUDENT = 'student'

def check_student_role():
    """Helper function to check if current user is a student"""
    if current_user.role != ROLE_STUDENT:
        flash(ACCESS_DENIED_MSG, ACCESS_DENIED_CATEGORY)
        return False
    return True

@student.route('/dashboard')
@login_required
def dashboard():
    if not check_student_role():
        return redirect(url_for('index'))
    
    # Get all upcoming events from verified clubs
    events = Event.query.join(Club).filter(
        Club.verified == True,
        Event.event_datetime >= datetime.now(timezone.utc)  # CHANGED
    ).order_by(Event.event_datetime).all()  # CHANGED
    
    # Get user's RSVPs
    user_rsvps = {rsvp.event_id for rsvp in current_user.rsvps}
    
    # Get user's followed clubs
    followed_club_ids = {follow.club_id for follow in current_user.followed_clubs}
    
    return render_template('student/dashboard.html', 
                         events=events, 
                         user_rsvps=user_rsvps,
                         followed_club_ids=followed_club_ids)

@student.route('/event/<int:event_id>')
@login_required
def event_detail(event_id):
    if not check_student_role():
        return redirect(url_for('index'))
    
    event = Event.query.get_or_404(event_id)
    
    # Check if user has RSVP'd
    has_rsvp = RSVP.query.filter_by(
        user_id=current_user.id, 
        event_id=event_id
    ).first() is not None
    
    # Check if user follows this club
    is_following = ClubFollower.query.filter_by(
        user_id=current_user.id,
        club_id=event.club_id
    ).first() is not None
    
    # Get RSVP count
    rsvp_count = RSVP.query.filter_by(event_id=event_id).count()
    
    return render_template('student/event_detail.html', 
                         event=event, 
                         has_rsvp=has_rsvp,
                         is_following=is_following,
                         rsvp_count=rsvp_count)

@student.route('/rsvp/<int:event_id>', methods=['POST'])
@login_required
def toggle_rsvp(event_id):
    if not check_student_role():
        return redirect(url_for('index'))
    
    event = Event.query.get_or_404(event_id)
    existing_rsvp = RSVP.query.filter_by(
        user_id=current_user.id, 
        event_id=event_id
    ).first()
    
    if existing_rsvp:
        # Remove RSVP
        db.session.delete(existing_rsvp)
        db.session.commit()
        flash('RSVP removed', 'info')
    else:
        # Add RSVP
        rsvp = RSVP(user_id=current_user.id, event_id=event_id)
        db.session.add(rsvp)
        db.session.commit()
        flash('RSVP confirmed!', 'success')
    
    return redirect(url_for('student.event_detail', event_id=event_id))

@student.route('/follow/<int:club_id>', methods=['POST'])
@login_required
def toggle_follow(club_id):
    if not check_student_role():
        return redirect(url_for('index'))
    
    club = Club.query.get_or_404(club_id)
    existing_follow = ClubFollower.query.filter_by(
        user_id=current_user.id, 
        club_id=club_id
    ).first()
    
    if existing_follow:
        # Unfollow
        db.session.delete(existing_follow)
        db.session.commit()
        flash(f'Unfollowed {club.name}', 'info')
    else:
        # Follow
        follow = ClubFollower(user_id=current_user.id, club_id=club_id)
        db.session.add(follow)
        db.session.commit()
        flash(f'Now following {club.name}!', 'success')
    
    return redirect(request.referrer or url_for('student.dashboard'))

@student.route('/my-rsvps')
@login_required
def my_rsvps():
    if not check_student_role():
        return redirect(url_for('index'))
    
    # Get all events user has RSVP'd to
    rsvp_events = Event.query.join(RSVP).filter(
        RSVP.user_id == current_user.id
    ).order_by(Event.event_datetime).all()  # CHANGED
    
    return render_template('student/my_rsvps.html', events=rsvp_events)

@student.route('/my-clubs')
@login_required
def my_clubs():
    if not check_student_role():
        return redirect(url_for('index'))
    
    # Get clubs user explicitly follows
    followed_clubs = Club.query.join(ClubFollower).filter(
        ClubFollower.user_id == current_user.id,
        Club.verified == True
    ).all()
    
    return render_template('student/my_clubs.html', clubs=followed_clubs)

@student.route('/clubs')
@login_required
def browse_clubs():
    # Fetch all clubs from the database
    all_clubs = Club.query.all()
    
    # Render the template we just built
    return render_template('student/browse_clubs.html', clubs=all_clubs)
    

@student.route('/club/<string:club_name_slug>')
@login_required
def club_detail(club_name_slug):
    if not check_student_role():
        return redirect(url_for('index'))
    
    # 1. Convert the URL slug back to the real name (e.g. "Active_Minds" -> "Active Minds")
    club_name = club_name_slug.replace('_', ' ')
    
    # 2. Find the club by Name instead of ID
    # This ensures the link from your Browse Clubs page finds the right entry
    club = Club.query.filter_by(name=club_name).first_or_404()
    
    # 3. Logic remains the same, but we use 'club.id' from the found object
    
    # Check if user follows this club
    is_following = ClubFollower.query.filter_by(
        user_id=current_user.id,
        club_id=club.id  # Updated to use the ID of the found club
    ).first() is not None
    
    # Get upcoming events for this club
    upcoming_events = Event.query.filter(
        Event.club_id == club.id, # Updated to use club.id
        Event.event_datetime >= datetime.now(timezone.utc)
    ).order_by(Event.event_datetime).all()
    
    # Get follower count
    follower_count = ClubFollower.query.filter_by(club_id=club.id).count() # Updated to use club.id
    
    return render_template('student/club_detail.html',
                           club=club,
                           is_following=is_following,
                           upcoming_events=upcoming_events,
                           follower_count=follower_count)