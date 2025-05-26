from app.application.services import assign_locker_and_create_parcel, generate_pin_and_hash, verify_pin
from app.persistence.models import Locker, Parcel
from app import db # Import db for direct session manipulation if needed
import pytest # Import pytest to use fixtures

def test_generate_pin_and_hash():
    pin, hashed_value = generate_pin_and_hash()
    assert isinstance(pin, str)
    assert len(pin) == 6
    assert pin.isdigit()
    assert ":" in hashed_value # Format "salt:hash"

def test_verify_pin(): # Removed init_database fixture as it's not strictly needed for this test
    pin, hashed_value = generate_pin_and_hash()
    assert verify_pin(hashed_value, pin) is True
    assert verify_pin(hashed_value, "123456") is False # Incorrect PIN
    assert verify_pin("invalidformat", pin) is False # Malformed stored hash
    # Test with a known hash (if possible, though generate_pin_and_hash is random)
    # For now, the above checks cover the logic well.

def test_assign_locker_and_create_parcel_success(init_database, app): # app fixture for app context
    with app.app_context(): # Ensure operations are within app context
        # Pre-check: Ensure a small, free locker exists (added by init_database)
        initial_free_small_locker = Locker.query.filter_by(size='small', status='free').first()
        assert initial_free_small_locker is not None

        parcel, pin, error = assign_locker_and_create_parcel('small', 'test@example.com')

        assert error is None
        assert parcel is not None
        assert parcel.id is not None
        assert parcel.recipient_email == 'test@example.com'
        assert parcel.status == 'deposited'
        assert pin is not None
        assert len(pin) == 6

        assigned_locker = db.session.get(Locker, parcel.locker_id)
        assert assigned_locker is not None
        assert assigned_locker.status == 'occupied'
        assert assigned_locker.size == 'small'
        # Ensure it's the same locker that was initially free
        assert assigned_locker.id == initial_free_small_locker.id

def test_assign_locker_no_availability(init_database, app):
    with app.app_context():
        # Make all 'large' lockers occupied for this test.
        # init_database adds one free 'large' locker.
        large_lockers = Locker.query.filter_by(size='large').all()
        for locker in large_lockers:
            locker.status = 'occupied'
        db.session.commit()

        parcel, pin, error = assign_locker_and_create_parcel('large', 'test2@example.com')
        assert parcel is None
        assert pin is None
        assert error == "No available locker of the specified size."

        # Verify no new parcel was created
        assert Parcel.query.filter_by(recipient_email='test2@example.com').first() is None
