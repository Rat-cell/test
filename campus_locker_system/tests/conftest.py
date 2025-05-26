import pytest
from app import create_app, db
from app.config import Config
from app.persistence.models import Locker # Import Locker to pre-populate

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use in-memory SQLite for tests
    WTF_CSRF_ENABLED = False # Disable CSRF for testing forms if Flask-WTF is used later

@pytest.fixture(scope='session') # Changed to session scope for efficiency
def app():
    app = create_app()
    app.config.from_object(TestConfig)
    return app

@pytest.fixture(scope='module') # Use module scope for db
def client(app):
    return app.test_client()

@pytest.fixture(scope='module') # Use module scope for db setup/teardown
def init_database(app):
    with app.app_context():
        db.create_all()

        # Pre-populate with some lockers for testing assignment
        if not Locker.query.first(): # Add only if no lockers exist
            locker1 = Locker(size='small', status='free')
            locker2 = Locker(size='medium', status='free')
            locker3 = Locker(size='large', status='free')
            locker4 = Locker(size='small', status='occupied')
            db.session.add_all([locker1, locker2, locker3, locker4])
            db.session.commit()

        yield db  # Provide the db object to tests

        # db.session.remove() # Not strictly necessary with in-memory and drop_all
        db.drop_all()     # Drop all tables after tests in this module
