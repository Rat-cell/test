import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key'
    
    # Main database configuration
    MAIN_DB_FILENAME = 'campus_locker.db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', MAIN_DB_FILENAME) # In project root
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Audit database configuration
    AUDIT_DB_FILENAME = 'campus_locker_audit.db'
    AUDIT_SQLALCHEMY_DATABASE_URI = os.environ.get('AUDIT_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', AUDIT_DB_FILENAME) # In project root

    SQLALCHEMY_BINDS = {
        'audit': AUDIT_SQLALCHEMY_DATABASE_URI
    }

    # Flask-Mail configuration for MailHog
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = 'noreply@campuslocker.example.com'
