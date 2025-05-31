import pytest
from app import create_app, db
from app.config import Config
from app.persistence.models import Locker # Import Locker to pre-populate

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory SQLite for tests
    WTF_CSRF_ENABLED = False # Disable CSRF for testing forms if Flask-WTF is used later
    SERVER_NAME = 'localhost'
    MAIL_SUPPRESS_SEND = True
    MAIL_DEFAULT_SENDER = 'test@example.com'
    # Disable auto-seeding during tests to prevent conflicts
    ENABLE_DEFAULT_LOCKER_SEEDING = False

@pytest.fixture(scope='function')
def app():
    app = create_app()
    app.config.from_object(TestConfig)
    
    with app.app_context():
        # Create all tables but don't seed any data
        db.create_all()
        
        yield app
        
        # Clean up
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def init_database(app):
    with app.app_context():
        # Always pre-populate lockers for each test
        locker1 = Locker(size='small', status='free')
        locker2 = Locker(size='medium', status='free')
        locker3 = Locker(size='large', status='free')
        locker4 = Locker(size='small', status='occupied')
        db.session.add_all([locker1, locker2, locker3, locker4])
        db.session.commit()

        yield db  # Provide the db object to tests
