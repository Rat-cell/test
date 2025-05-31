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
    # Database directory - container uses /app/databases, local development uses relative path
    DATABASE_DIR = os.environ.get('DATABASE_DIR') or os.path.join(basedir, '..', 'databases')
    
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

    # Admin notification configuration
    ADMIN_NOTIFICATION_EMAIL = os.environ.get('ADMIN_NOTIFICATION_EMAIL', 'admin@campuslocker.local')

    # Sensor Data Feature Configuration
    ENABLE_LOCKER_SENSOR_DATA_FEATURE = True
    DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE = False

    # Parcel Lifecycle Configuration
    PARCEL_MAX_PICKUP_DAYS = 7
    PARCEL_MAX_PIN_REISSUE_DAYS = 7

    # PIN Configuration
    PIN_EXPIRY_HOURS = int(os.environ.get('PIN_EXPIRY_HOURS', 24))  # PIN validity in hours
    
    # FR-04: Send Reminder After 24h of Occupancy - Configurable timing
    REMINDER_HOURS_AFTER_DEPOSIT = int(os.environ.get('REMINDER_HOURS_AFTER_DEPOSIT', 24))  # Hours to wait before sending reminder
    
    # FR-04: Automatic reminder processing interval (how often to check for reminders)
    REMINDER_PROCESSING_INTERVAL_HOURS = int(os.environ.get('REMINDER_PROCESSING_INTERVAL_HOURS', 1))  # Check every hour
    
    # NFR-04: Backup Configuration - Data Preservation & Recovery
    # ===========================================================
    
    # NFR-04: Backup - Scheduled backup interval in days (client-configurable)
    BACKUP_INTERVAL_DAYS = int(os.environ.get('BACKUP_INTERVAL_DAYS', 7))  # Default: 7 days
    
    # NFR-04: Backup - Backup retention policy in days (client-configurable)
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))  # Default: 30 days
    
    # NFR-02: Database Reliability Configuration - Crash Safety
    # =======================================================
    
    # NFR-02: Reliability - SQLite WAL (Write-Ahead Logging) mode for crash safety
    # Ensures maximum one transaction loss during database crashes
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verify connections before use
        'pool_recycle': 300,    # Recycle connections every 5 minutes
        'connect_args': {
            'check_same_thread': False,  # Allow multi-threaded access
            'timeout': 60,               # 60-second timeout for database locks
        },
        # Configure SQLite to properly handle UTC timezone-aware datetimes
        'module': 'sqlite3'  # Ensure consistent SQLite behavior
    }
    
    # NFR-02: Reliability - Database crash safety and reliability features
    ENABLE_SQLITE_WAL_MODE = os.environ.get('ENABLE_SQLITE_WAL_MODE', 'true').lower() == 'true'
    SQLITE_SYNCHRONOUS_MODE = os.environ.get('SQLITE_SYNCHRONOUS_MODE', 'NORMAL')  # NORMAL, FULL, OFF
    
    # Email-based PIN Generation Configuration (Only System)
    PIN_GENERATION_TOKEN_EXPIRY_HOURS = int(os.environ.get('PIN_GENERATION_TOKEN_EXPIRY', 24))  # hours
    MAX_PIN_GENERATIONS_PER_DAY = int(os.environ.get('MAX_PIN_GENERATIONS_PER_DAY', 3))

    LOG_DIR = os.environ.get('LOG_DIR') or os.path.abspath(os.path.join(basedir, '..', 'logs'))

    # 🏗️ LOCKER CONFIGURATION (Client Configurable)
    # ==============================================
    
    # Locker configuration file path (JSON format) - stored in persistent databases directory
    LOCKER_CONFIG_FILE = os.environ.get('LOCKER_CONFIG_FILE') or os.path.join(basedir, '..', 'databases', 'lockers-hwr.json')
    
    # Simple environment variable setup for quick deployment
    # Format: "count:15,size_small:5,size_medium:5,size_large:5,location_prefix:HWR Locker {unit}"
    LOCKER_SIMPLE_CONFIG = os.environ.get('LOCKER_SIMPLE_CONFIG')
    
    # Locker size physical dimensions (client configurable)
    LOCKER_SIZE_DIMENSIONS = {
        'small': {'height': 30, 'width': 40, 'depth': 45},   # cm
        'medium': {'height': 50, 'width': 40, 'depth': 45},  # cm  
        'large': {'height': 80, 'width': 40, 'depth': 45}    # cm
    }
    
    # Default locker seeding behavior (clients can override via env vars)
    # DISABLED: Using explicit HWR configuration only
    ENABLE_DEFAULT_LOCKER_SEEDING = os.environ.get('ENABLE_DEFAULT_LOCKER_SEEDING', 'false').lower() == 'true'
