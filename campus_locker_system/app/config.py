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
    PARCEL_DEFAULT_PIN_VALIDITY_DAYS = 7 # Default validity of a PIN in days

    # Reminder Notifications Configuration
    REMINDER_NOTIFICATION_SCHEDULE_HOURS = [24] # Hours after deposit to send reminder notifications
    PRE_RETURN_NOTIFICATION_HOURS = 24          # Hours before max pickup time to send a pre-return notification

    # APScheduler Job Intervals
    REMINDER_JOB_INTERVAL_HOURS = 6     # Interval in hours for running the reminder notification job
    OVERDUE_PROCESSING_JOB_INTERVAL_HOURS = 24 # Interval in hours for running the overdue parcel processing job
