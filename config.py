import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-fallback-secret-key-12345')
    
    # Handle database URL configurations, e.g., Render/Postgres URL starts with postgres://, but SQLAlchemy requires postgresql://
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session cookie protection
    SESSION_COOKIE_SECURE = False  # Set to True in production (HTTPS)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
