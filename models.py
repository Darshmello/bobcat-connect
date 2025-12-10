# models.py
from extensions import db
from flask_login import UserMixin
from datetime import datetime, timezone

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'student', 'club', 'admin'
    
    # Relationships
    rsvps = db.relationship('RSVP', backref='user', lazy=True)
    followed_clubs = db.relationship('ClubFollower', backref='follower', lazy=True)

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    verified = db.Column(db.Boolean, default=False)
    
    # Metadata from scraper
    meeting_time = db.Column(db.String(100))
    location = db.Column(db.String(100))
    member_count = db.Column(db.Integer)

    # Relationships
    posts = db.relationship('Post', backref='club', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    
    # Content
    image_file = db.Column(db.String(120), nullable=False, default='default.jpg')
    caption = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Event Specific Fields (Nullable)
    is_event = db.Column(db.Boolean, default=False)
    event_title = db.Column(db.String(100)) # e.g. "Intro to Python Workshop"
    event_date = db.Column(db.DateTime)     # If set, it's an event
    event_location = db.Column(db.String(100))

    # Relationships
    rsvps = db.relationship('RSVP', backref='post', lazy=True)

class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False) # Changed from event_id
    
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)

class ClubFollower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'club_id'),)