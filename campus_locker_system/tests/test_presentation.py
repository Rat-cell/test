import pytest
from app.persistence.models import Locker, Parcel # Import models for verification
from app import db # Import db for direct session manipulation if needed

def test_deposit_page_loads(client, init_database): # client and init_database fixtures
    response = client.get('/deposit')
    assert response.status_code == 200
    assert b"Deposit Parcel" in response.data # Check for a keyword in the form

def test_deposit_action_success(client, init_database, app): # Added app fixture
    with app.app_context(): # Required for url_for and db operations
        # Ensure a small locker is available (from init_database)
        # init_database should have added a free 'small' locker
        assert Locker.query.filter_by(size='small', status='free').first() is not None

        response = client.post('/deposit', data={
            'parcel_size': 'small',
            'recipient_email': 'sender@example.com'
        }, follow_redirects=True) # follow_redirects to handle the redirect to confirmation or form
        
        assert response.status_code == 200 # Should be 200 after following redirect
        assert b"Deposit Successful!" in response.data
        assert b"Recipient PIN:" in response.data # Check for PIN on confirmation page

        # Verify in DB
        parcel = Parcel.query.filter_by(recipient_email='sender@example.com').first()
        assert parcel is not None
        assert parcel.status == 'deposited'
        assigned_locker = db.session.get(Locker, parcel.locker_id)
        assert assigned_locker is not None # Ensure locker was actually assigned
        assert assigned_locker.status == 'occupied'

def test_deposit_action_no_locker_available(client, init_database, app):
    with app.app_context():
        # Make all small lockers occupied
        # init_database adds one free 'small' locker. We need to make sure it's occupied.
        # And any other small lockers are also occupied.
        small_lockers = Locker.query.filter_by(size='small').all()
        for locker in small_lockers:
            locker.status = 'occupied'
        db.session.commit() # Commit the changes to ensure they are reflected for the test

        response = client.post('/deposit', data={
            'parcel_size': 'small',
            'recipient_email': 'another@example.com'
        }, follow_redirects=True)
        
        assert response.status_code == 200 # Should be 200 after redirecting to the form
        assert b"Error: No available locker of the specified size." in response.data
        assert b"Deposit Successful!" not in response.data # Ensure success message is not there

        # Verify no new parcel was created for this email
        assert Parcel.query.filter_by(recipient_email='another@example.com').first() is None
