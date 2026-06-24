import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///taxtrace.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ['http://localhost:5500', 'http://localhost:5000']
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    PORT = int(os.environ.get('PORT') or 3000)
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'