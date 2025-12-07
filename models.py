from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum('student', 'club', 'admin', name='user_roles'), nullable=False)  # Switching to Enums for better data integrity (compared to strings)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    followed_clubs = db.relationship('ClubFollower', backref='follower', lazy=True)

    # Relationships
    rsvps = db.relationship('RSVP', backref='user', lazy=True)

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    verified = db.Column(db.Boolean, default=False) # Clubs need to be verified by admin, can comment out for testing
    established_at = db.Column(db.DateTime, default=datetime.utcnow) # Could be changed to established_at if needed
    followers = db.relationship('ClubFollower', backref='club', lazy=True)

    
    # Relationships
    events = db.relationship('Event', backref='club', lazy=True)

class ClubFollower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # One follow per user per club
    __table_args__ = (db.UniqueConstraint('user_id', 'club_id'),)
    

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    datetime = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # could remove if not needed
    
    # Relationships
    rsvps = db.relationship('RSVP', backref='event', lazy=True)

class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # could remove if not needed but nice to have
    
    # Ensure one RSVP per user per event
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id'),)