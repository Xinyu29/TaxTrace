import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    # Use absolute path for database so it works from any directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(BASE_DIR, "taxtrace.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ['http://localhost:5500', 'http://localhost:3000']
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    PORT = int(os.environ.get('PORT') or 3000)
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
