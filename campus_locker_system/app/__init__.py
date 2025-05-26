from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail # Add this
from .config import Config

db = SQLAlchemy()
mail = Mail() # Add this

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

    return app
