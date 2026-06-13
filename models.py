from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()

class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Admin {self.username}>'


class Volunteer(db.Model):
    __tablename__ = 'volunteers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    skills = db.Column(db.String(255), nullable=False)  # Comma-separated strings, e.g., "Teaching, Web Development"
    availability = db.Column(db.String(50), nullable=False)  # E.g., "Weekdays", "Weekends", "Flexible"
    registration_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<Volunteer {self.name} - {self.email}>'
