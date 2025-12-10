from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db, cache
from models import Club, Post, RSVP, ClubFollower
from datetime import datetime, timezone

student = Blueprint('student', __name__)

# --- Helper Functions ---

def check_student_role():
    # Allow Student, Club, and Admin roles to view the student pages
    if current_user.role not in ['student', 'club', 'admin']:
        flash('Access denied.', 'danger')
        return False
    return True

def make_cache_key(*args, **kwargs):
    """
    Creates a unique cache key based on the route path and the current user's ID.
    Ensures User A doesn't see User B's 'Follow' status or private data.
    """
    path = request.path
    uid = current_user.id if current_user.is_authenticated else 'guest'
    return f"{path}_{uid}"

# --- Dashboard & Feeds ---

@student.route('/dashboard')
@login_required
def dashboard():
    """Global Feed: Shows ALL Posts (Events & General) from verified clubs."""
    if not check_student_role():
        return redirect(url_for('index'))
    
    # Unified Query: Get all posts from verified clubs, newest first
    posts = Post.query.join(Club).filter(
        Club.verified == True
    ).order_by(Post.created_at.desc()).all()
    
    # Gather IDs for UI state (e.g. "RSVP'd" or "Following" indicators)
    # Note: We look at 'post_id' now instead of 'event_id'
    user_rsvps = {rsvp.post_id for rsvp in current_user.rsvps}
    followed_club_ids = {follow.club_id for follow in current_user.followed_clubs}
    
    return render_template('student/dashboard.html', 
                         events=posts,  # We pass 'posts' to the 'events' variable for template compatibility
                         user_rsvps=user_rsvps,
                         followed_club_ids=followed_club_ids,
                         feed_type='global')

@student.route('/following')
@login_required
def following_feed():
    """Subscribed Feed: Shows Posts ONLY from clubs the user follows."""
    if not check_student_role():
        return redirect(url_for('index'))

    # 1. Get IDs of clubs the user follows
    followed_club_ids = [f.club_id for f in current_user.followed_clubs]

    # 2. Query posts from those clubs only
    posts = Post.query.filter(
        Post.club_id.in_(followed_club_ids)
    ).order_by(Post.created_at.desc()).all()

    user_rsvps = {rsvp.post_id for rsvp in current_user.rsvps}
    
    return render_template('student/dashboard.html', 
                         events=posts, 
                         user_rsvps=user_rsvps,
                         followed_club_ids=followed_club_ids,
                         feed_type='following')

@student.route('/my-rsvps')
@login_required
def my_rsvps():
    """My Schedule: Shows only 'Event' type posts the user has RSVP'd to."""
    if not check_student_role():
        return redirect(url_for('index'))
    
    # Query RSVPs -> Join Post -> Filter by User
    # Sorted by the event_date so they know what's coming up
    rsvp_posts = Post.query.join(RSVP).filter(
        RSVP.user_id == current_user.id
    ).order_by(Post.event_date).all()
    
    return render_template('student/my_rsvps.html', events=rsvp_posts)

# --- Interactions ---

@student.route('/event/<int:post_id>')
@login_required
def event_detail(post_id):
    """Detail page for a specific Post (Event or General)."""
    if not check_student_role():
        return redirect(url_for('index'))
    
    post = Post.query.get_or_404(post_id)
    
    has_rsvp = RSVP.query.filter_by(user_id=current_user.id, post_id=post_id).first() is not None
    is_following = ClubFollower.query.filter_by(user_id=current_user.id, club_id=post.club_id).first() is not None
    rsvp_count = RSVP.query.filter_by(post_id=post_id).count()
    
    # Pass 'post' as 'event' to keep template compatible
    return render_template('student/event_detail.html', 
                         event=post, 
                         has_rsvp=has_rsvp,
                         is_following=is_following,
                         rsvp_count=rsvp_count)

@student.route('/rsvp/<int:post_id>', methods=['POST'])
@login_required
def toggle_rsvp(post_id):
    if not check_student_role():
        return redirect(url_for('index'))

    post = Post.query.get_or_404(post_id)
    
    # Only allow RSVP if it is actually an event
    if not post.is_event:
        flash('This post is not an event.', 'warning')
        return redirect(request.referrer)

    existing_rsvp = RSVP.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if existing_rsvp:
        db.session.delete(existing_rsvp)
        flash('RSVP removed', 'info')
    else:
        rsvp = RSVP(user_id=current_user.id, post_id=post_id)
        db.session.add(rsvp)
        flash('RSVP confirmed!', 'success')
    
    db.session.commit()
    return redirect(request.referrer or url_for('student.dashboard'))

@student.route('/follow/<int:club_id>', methods=['POST'])
@login_required
def toggle_follow(club_id):
    if not check_student_role():
        return redirect(url_for('index'))

    club = Club.query.get_or_404(club_id)
    existing_follow = ClubFollower.query.filter_by(user_id=current_user.id, club_id=club_id).first()
    
    if existing_follow:
        db.session.delete(existing_follow)
        flash(f'Unfollowed {club.name}', 'info')
    else:
        follow = ClubFollower(user_id=current_user.id, club_id=club_id)
        db.session.add(follow)
        flash(f'Now following {club.name}!', 'success')
    
    db.session.commit()
    # No cache clearing needed with per-user keys
    return redirect(request.referrer or url_for('student.dashboard'))

# --- Club Pages ---

@student.route('/clubs')
@login_required
def browse_clubs():
    all_clubs = Club.query.all()
    return render_template('student/browse_clubs.html', clubs=all_clubs)

@student.route('/club/<string:club_name_slug>')
@login_required
# We remove caching here to ensure the "Follow" button updates instantly on click
def club_detail(club_name_slug):
    if not check_student_role():
        return redirect(url_for('index'))
    
    # Revert Slug: "Machine_Learning_Club" -> "Machine Learning Club"
    club_name = club_name_slug.replace('_', ' ')
    club = Club.query.filter_by(name=club_name).first_or_404()
    
    is_following = ClubFollower.query.filter_by(user_id=current_user.id, club_id=club.id).first() is not None
    
    # 1. Get Upcoming Events (Posts where is_event=True and date is future)
    upcoming_events = Post.query.filter(
        Post.club_id == club.id,
        Post.is_event == True,
        Post.event_date >= datetime.now(timezone.utc)
    ).order_by(Post.event_date).all()

    # 2. Get Recent Posts (Everything else, or just everything for the grid)
    # Using 'club.posts' in the template will get ALL posts. 
    # If you want ONLY non-events for the grid, create a list here:
    # social_posts = [p for p in club.posts if not p.is_event] 
    
    follower_count = ClubFollower.query.filter_by(club_id=club.id).count()
    
    return render_template('student/club_detail.html',
                           club=club,
                           is_following=is_following,
                           upcoming_events=upcoming_events,
                           follower_count=follower_count)

@student.route('/my-clubs')
@login_required
def my_clubs():
    followed_clubs = Club.query.join(ClubFollower).filter(
        ClubFollower.user_id == current_user.id,
        Club.verified == True
    ).all()
    
    return render_template('student/my_clubs.html', clubs=followed_clubs)