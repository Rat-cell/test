from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail # Add this
from .config import Config
from datetime import datetime
import datetime as dt
import sqlite3

# Configure SQLite datetime adapters for Python 3.12+ compatibility
# This fixes the DeprecationWarning: "The default datetime adapter is deprecated"
# Following SQLite3 documentation recommendations for replacement recipes
def adapt_datetime_iso(dt_obj):
    """Convert datetime to ISO string for SQLite storage (Python 3.12+ compatible)"""
    return dt_obj.isoformat()

def convert_datetime(dt_string):
    """Convert ISO string from SQLite back to datetime object (Python 3.12+ compatible)"""
    if isinstance(dt_string, bytes):
        dt_string = dt_string.decode('utf-8')
    return datetime.fromisoformat(dt_string.replace(' ', 'T'))

# Register the new adapters and converters for Python 3.12+ compatibility
sqlite3.register_adapter(datetime, adapt_datetime_iso)
sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_converter("DATETIME", convert_datetime)

db = SQLAlchemy()
mail = Mail() # Add this

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Add DATABASE_DIR to config for database service
    app.config['DATABASE_DIR'] = app.config.get('DATABASE_DIR', '/app/databases')

    # Configure SQLAlchemy
    # NFR-01: Performance - Database optimization for fast locker assignment
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Performance optimization
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600
    }

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app) # Add this

    with app.app_context():
        # NFR-02 & NFR-04: Initialize databases with reliability and backup features
        from app.services.database_service import DatabaseService
        from app.services.admin_auth_service import AdminAuthService # Import AdminAuthService
        from app.business.admin_auth import AdminRole # Import AdminRole

        app.logger.info("🗄️ Starting database initialization...")
        
        # Step 1: Initialize databases and create tables
        # NFR-02: Reliability - Includes SQLite WAL mode configuration for crash safety
        db_success, db_message = DatabaseService.initialize_databases()
        
        if db_success:
            app.logger.info(f"✅ Database initialization successful: {db_message}")
            
            # Step 2: Run post-initialization tasks (including backup checks)
            try:
                DatabaseService.post_initialization_tasks()
                app.logger.info("✅ Post-initialization tasks completed")
            except Exception as e:
                app.logger.warning(f"⚠️ Post-initialization tasks failed: {str(e)}")
        else:
            app.logger.error(f"❌ Database initialization failed: {db_message}")
            # Continue anyway - some functionality may still work
        
        # Legacy create_all() call as fallback (should be redundant now with DatabaseService)
        # try:
        #     db.create_all()
        # except Exception as e:
        #     app.logger.warning(f"⚠️ Legacy db.create_all() failed: {str(e)}")
        
        # Auto-seed lockers from JSON configurations if configured
        # from app.services.locker_initialization_service import LockerInitializationService
        # LockerInitializationService.auto_initialize_from_config()

    # Register Blueprints
    from app.presentation import main_bp
    app.register_blueprint(main_bp)

    # Register API blueprints
    # from app.api import api_bp
    # app.register_blueprint(api_bp, url_prefix='/api')

    # FR-04: Start automatic reminder processing scheduler
    _start_automatic_reminder_scheduler(app)

    # Logging configuration
    if not app.debug and not app.testing:
        import logging
        from logging.handlers import RotatingFileHandler
        import os
        log_dir = app.config.get('LOG_DIR')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        file_handler = RotatingFileHandler(os.path.join(log_dir, 'campus_locker.log'), maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('🚀 Campus Locker System startup')

    return app

def _start_automatic_reminder_scheduler(app):
    """
    FR-04: Start background scheduler for automatic reminder processing
    FR-04: Runs reminder processing every hour without admin intervention
    
    This function starts a background thread that:
    - Runs every hour (configurable)
    - Processes all eligible parcels for reminders
    - Logs all activities for audit trail
    - Handles errors gracefully
    """
    import threading
    import time
    from datetime import datetime
    
    def reminder_scheduler_loop():
        """Background loop that processes reminders periodically"""
        while True:
            try:
                # FR-04: Get scheduling interval from config (default: 1 hour)
                interval_hours = app.config.get('REMINDER_PROCESSING_INTERVAL_HOURS', 1)
                sleep_seconds = interval_hours * 3600  # Convert hours to seconds
                
                app.logger.info(f"FR-04: Reminder scheduler sleeping for {interval_hours} hour(s)")
                time.sleep(sleep_seconds)
                
                # FR-04: Process reminders in application context
                with app.app_context():
                    app.logger.info("FR-04: Starting automatic reminder processing...")
                    
                    # Import here to avoid circular imports
                    from app.services.parcel_service import process_reminder_notifications
                    from app.services.audit_service import AuditService
                    
                    # FR-04: Process all eligible reminders
                    processed_count, error_count = process_reminder_notifications()
                    
                    # FR-04: Log scheduler execution
                    AuditService.log_event("FR-04_SCHEDULED_REMINDER_PROCESSING", {
                        "processed_count": processed_count,
                        "error_count": error_count,
                        "total_eligible": processed_count + error_count,
                        "trigger_source": "automatic_background_scheduler",
                        "execution_time": datetime.now(dt.UTC).strftime('%Y-%m-%d %H:%M:%S'),
                        "next_execution_in_hours": interval_hours
                    })
                    
                    if processed_count > 0 or error_count > 0:
                        app.logger.info(f"FR-04: Automatic reminder processing completed. Processed: {processed_count}, Errors: {error_count}")
                    else:
                        app.logger.debug("FR-04: No reminders needed at this time")
                        
            except Exception as e:
                app.logger.error(f"FR-04: Error in reminder scheduler: {str(e)}")
                # Continue the loop even if there's an error
                time.sleep(300)  # Sleep 5 minutes before retrying
    
    # FR-04: Start scheduler thread only if not in testing mode
    if not app.config.get('TESTING', False):
        scheduler_thread = threading.Thread(
            target=reminder_scheduler_loop,
            daemon=True,  # Dies when main thread dies
            name="ReminderScheduler"
        )
        scheduler_thread.start()
        app.logger.info("FR-04: Automatic reminder scheduler started successfully")
    else:
        app.logger.info("FR-04: Reminder scheduler disabled (testing mode)")
