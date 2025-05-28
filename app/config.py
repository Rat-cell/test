import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key'
    
    # Flask URL generation configuration
    SERVER_NAME = os.environ.get('SERVER_NAME', 'localhost')
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT', '/')
    
    # Main database configuration
    MAIN_DB_FILENAME = 'campus_locker.db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'databases', MAIN_DB_FILENAME) # In databases folder
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Audit database configuration
    AUDIT_DB_FILENAME = 'campus_locker_audit.db'
    AUDIT_SQLALCHEMY_DATABASE_URI = os.environ.get('AUDIT_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'databases', AUDIT_DB_FILENAME) # In databases folder

    SQLALCHEMY_BINDS = {
        'audit': AUDIT_SQLALCHEMY_DATABASE_URI
    }

    # Flask-Mail configuration for MailHog
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 1025))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@campuslocker.local')

    LOCKER_SIZE_DIMENSIONS = {
        'small': {'height': 10, 'width': 10, 'depth': 10},
        'medium': {'height': 20, 'width': 20, 'depth': 20},
        'large': {'height': 30, 'width': 30, 'depth': 30},
    }

    # Sensor Data Feature Configuration
    ENABLE_LOCKER_SENSOR_DATA_FEATURE = True
    DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE = False

    # Parcel Lifecycle Configuration
    PARCEL_MAX_PICKUP_DAYS = 7
    PARCEL_MAX_PIN_REISSUE_DAYS = 7

    # PIN Configuration
    PIN_EXPIRY_HOURS = int(os.environ.get('PIN_EXPIRY_HOURS', 24))  # PIN validity in hours
    
    # Email-based PIN Generation Configuration
    PIN_GENERATION_TOKEN_EXPIRY_HOURS = int(os.environ.get('PIN_GENERATION_TOKEN_EXPIRY', 24))  # hours
    MAX_PIN_GENERATIONS_PER_DAY = int(os.environ.get('MAX_PIN_GENERATIONS_PER_DAY', 3))
    ENABLE_EMAIL_BASED_PIN_GENERATION = os.environ.get('ENABLE_EMAIL_BASED_PIN_GENERATION', 'true').lower() == 'true'

    LOG_DIR = os.environ.get('LOG_DIR') or os.path.abspath(os.path.join(basedir, '..', 'logs')) 