from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail # Add this
from flask_apscheduler import APScheduler # New import for APScheduler
from .config import Config
# Import service functions for scheduling
from app.application.services import send_scheduled_reminder_notifications, process_overdue_parcels

db = SQLAlchemy()
mail = Mail() # Add this
scheduler = APScheduler() # New APScheduler instance

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app) # Add this

    # Logging configuration
    if not app.debug and not app.testing:
        import logging
        from logging.handlers import RotatingFileHandler
        import os
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/campus_locker.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Campus Locker System startup')

    from .presentation import main_bp # Import the blueprint
    app.register_blueprint(main_bp) # Register the blueprint

    from .presentation.api_routes import api_bp # Import the API blueprint
    app.register_blueprint(api_bp) # Register the API blueprint

    with app.app_context():
        from .persistence import models # Ensure models are loaded
        db.create_all()

    # Initialize and start APScheduler if not already running (e.g. in test scenarios)
    # and not in testing mode where scheduler might be handled differently or not needed.
    if not scheduler.running and not app.config.get('TESTING', False):
        scheduler.init_app(app)
        scheduler.start()
        app.logger.info("APScheduler initialized and started.")

        # Scheduling jobs
        reminder_interval_hours = app.config.get('REMINDER_JOB_INTERVAL_HOURS', 6)
        overdue_interval_hours = app.config.get('OVERDUE_PROCESSING_JOB_INTERVAL_HOURS', 24)

        if not scheduler.get_job('send_reminders_job'):
            scheduler.add_job(
                id='send_reminders_job',
                func=send_scheduled_reminder_notifications,
                trigger='interval',
                hours=reminder_interval_hours,
                replace_existing=True 
            )
            app.logger.info(f"Scheduled 'send_scheduled_reminder_notifications' to run every {reminder_interval_hours} hours.")

        if not scheduler.get_job('process_overdue_job'):
            scheduler.add_job(
                id='process_overdue_job',
                func=process_overdue_parcels,
                trigger='interval',
                hours=overdue_interval_hours,
                replace_existing=True
            )
            app.logger.info(f"Scheduled 'process_overdue_parcels' to run every {overdue_interval_hours} hours.")

    return app
