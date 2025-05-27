from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail # Add this
from .config import Config

db = SQLAlchemy()
mail = Mail() # Add this

def seed_database():
    """Seed the database with initial data for manual testing"""
    from app.business.locker import Locker
    from app.services.admin_auth_service import AdminAuthService
    from app.business.admin_auth import AdminRole
    
    # Check if lockers already exist
    if Locker.query.count() == 0:
        print("🌱 Seeding database with initial lockers...")
        
        # Create sample lockers for testing
        lockers = [
            # Small lockers
            Locker(size='small', status='free'),
            Locker(size='small', status='free'),
            Locker(size='small', status='free'),
            Locker(size='small', status='free'),
            
            # Medium lockers
            Locker(size='medium', status='free'),
            Locker(size='medium', status='free'),
            Locker(size='medium', status='free'),
            
            # Large lockers
            Locker(size='large', status='free'),
            Locker(size='large', status='free'),
        ]
        
        for locker in lockers:
            db.session.add(locker)
        
        db.session.commit()
        print(f"✅ Created {len(lockers)} initial lockers")
    
    # Check if admin user exists
    from app.persistence.models import AdminUser
    if AdminUser.query.count() == 0:
        print("🔐 Creating default admin user...")
        try:
            admin_user, message = AdminAuthService.create_admin_user('admin', 'AdminPass123!', AdminRole.ADMIN)
            if admin_user:
                print("✅ Default admin user created: admin / AdminPass123!")
            else:
                print(f"⚠️  Could not create admin user: {message}")
        except Exception as e:
            print(f"⚠️  Error creating admin user: {e}")

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
        log_dir = app.config.get('LOG_DIR')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        file_handler = RotatingFileHandler(os.path.join(log_dir, 'campus_locker.log'), maxBytes=10240, backupCount=10)
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
        # Ensure the databases folder exists before creating the database files
        import os
        databases_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'databases'))
        if not os.path.exists(databases_dir):
            os.makedirs(databases_dir)
        from .persistence import models # Ensure models are loaded
        db.create_all()
        
        # Seed database with initial data for manual testing
        seed_database()

    return app
