import pytest
from app.persistence.models import Locker, Parcel, AdminUser, AuditLog # Import models for verification
from app import db # Import db for direct session manipulation if needed
from app.application.services import log_audit_event, assign_locker_and_create_parcel # Add assign_locker_and_create_parcel
import json # Add this

# Helper fixture for admin login
@pytest.fixture
def logged_in_admin_client(client, init_database, app):
    with app.app_context():
        admin_username = "test_admin_fr08"
        admin_pass = "supersecure"
        admin = AdminUser.query.filter_by(username=admin_username).first()
        if not admin:
            admin = AdminUser(username=admin_username)
            admin.set_password(admin_pass)
            db.session.add(admin)
            db.session.commit()
        
        login_response = client.post('/admin/login', data={
            'username': admin_username,
            'password': admin_pass
        }, follow_redirects=True)
        assert login_response.status_code == 200 # Ensure login is successful
        return client # client is now logged in

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

def test_admin_login_success_logs_audit(client, init_database, app):
    with app.app_context():
        admin_username = "testadmin_audit_login"
        admin_pass = "password123"
        admin = AdminUser(username=admin_username)
        admin.set_password(admin_pass)
        db.session.add(admin)
        db.session.commit()

        client.post('/admin/login', data={'username': admin_username, 'password': admin_pass})
        
        log_entry = AuditLog.query.filter_by(action="ADMIN_LOGIN_SUCCESS").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['admin_username'] == admin_username
        assert details['admin_id'] == admin.id

def test_admin_login_fail_logs_audit(client, init_database, app):
    with app.app_context():
        username_attempted = "nonexistentuser"
        client.post('/admin/login', data={'username': username_attempted, 'password': 'wrongpassword'})
        
        log_entry = AuditLog.query.filter_by(action="ADMIN_LOGIN_FAIL").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['username_attempted'] == username_attempted
        
def test_admin_logout_logs_audit(client, init_database, app):
    with app.app_context():
        admin_username = "testadmin_audit_logout"
        admin_pass = "password123"
        admin = AdminUser(username=admin_username)
        admin.set_password(admin_pass)
        db.session.add(admin)
        db.session.commit()
        # Log in first
        client.post('/admin/login', data={'username': admin_username, 'password': admin_pass})
        
        # Then log out
        client.get('/admin/logout')
        
        log_entry = AuditLog.query.filter_by(action="ADMIN_LOGOUT").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['admin_id'] == admin.id

def test_admin_audit_logs_view(client, init_database, app):
    with app.app_context():
        admin_user = AdminUser(username="auditviewer")
        admin_user.set_password("securepassword")
        db.session.add(admin_user)
        db.session.commit()

        login_resp = client.post('/admin/login', data={
            'username': 'auditviewer',
            'password': 'securepassword'
        }, follow_redirects=True)
        assert login_resp.status_code == 200

        log_audit_event("SPECIFIC_TEST_AUDIT_ACTION_PAGE", {"test_detail_page": "visible"})
        
        response = client.get('/admin/audit-logs')
        assert response.status_code == 200
        assert b"Audit Logs" in response.data
        assert b"SPECIFIC_TEST_AUDIT_ACTION_PAGE" in response.data
        assert b"test_detail_page" in response.data
        assert b"visible" in response.data

# Tests for Locker Status Management (FR-08) Presentation Layer
def test_admin_manage_lockers_page_access(client, logged_in_admin_client, init_database, app):
    # Test anonymous access
    response_anon = client.get('/admin/lockers', follow_redirects=True)
    assert response_anon.status_code == 200 # Redirects to login
    assert b"Admin Login" in response_anon.data 
    assert b"Please log in to access this page." in response_anon.data

    # Test admin access
    response_admin = logged_in_admin_client.get('/admin/lockers')
    assert response_admin.status_code == 200
    assert b"Manage Lockers" in response_admin.data
    # Check for some locker data (e.g., Locker ID 1 from init_database)
    assert b"Locker ID: 1" in response_admin.data # Assuming template shows ID like this or similar
    assert b"small" in response_admin.data # Assuming template shows size

def test_admin_update_locker_status_flow(logged_in_admin_client, init_database, app):
    with app.app_context():
        locker_id_to_test = 1 # Locker 1 is 'small', 'free' initially
        locker = db.session.get(Locker, locker_id_to_test)
        assert locker is not None and locker.status == 'free'

        # Action 1: Mark 'free' locker as 'out_of_service'
        response_to_oos = logged_in_admin_client.post(
            f'/admin/locker/{locker_id_to_test}/set-status',
            data={'new_status': 'out_of_service'},
            follow_redirects=True
        )
        assert response_to_oos.status_code == 200
        assert b"Locker 1 status successfully updated to 'out_of_service'." in response_to_oos.data
        assert db.session.get(Locker, locker_id_to_test).status == 'out_of_service'
        
        log_oos = AuditLog.query.filter(
            AuditLog.action == "ADMIN_LOCKER_STATUS_CHANGED",
            AuditLog.details.like(f'%"locker_id": {locker_id_to_test}%'),
            AuditLog.details.like(f'%"new_status": "out_of_service"%')
        ).order_by(AuditLog.timestamp.desc()).first()
        assert log_oos is not None

        # Action 2: Mark 'out_of_service' locker back to 'free'
        response_to_free = logged_in_admin_client.post(
            f'/admin/locker/{locker_id_to_test}/set-status',
            data={'new_status': 'free'},
            follow_redirects=True
        )
        assert response_to_free.status_code == 200
        assert b"Locker 1 status successfully updated to 'free'." in response_to_free.data
        assert db.session.get(Locker, locker_id_to_test).status == 'free'

        log_free = AuditLog.query.filter(
            AuditLog.action == "ADMIN_LOCKER_STATUS_CHANGED",
            AuditLog.details.like(f'%"locker_id": {locker_id_to_test}%'),
            AuditLog.details.like(f'%"new_status": "free"%')
        ).order_by(AuditLog.timestamp.desc()).first()
        assert log_free is not None

def test_admin_update_locker_status_fail_occupied_to_free(logged_in_admin_client, init_database, app):
    with app.app_context():
        locker_id_to_test = 2 # Use a different locker to avoid interference, e.g. Locker 2 ('medium', 'free')
        
        # Ensure it's free for deposit
        locker_obj_before_deposit = db.session.get(Locker, locker_id_to_test)
        assert locker_obj_before_deposit is not None
        if locker_obj_before_deposit.status != 'free':
            locker_obj_before_deposit.status = 'free'
            Parcel.query.filter_by(locker_id=locker_id_to_test).delete()
            db.session.commit()

        # Deposit a parcel to make it 'occupied'
        parcel, _, _ = assign_locker_and_create_parcel('medium', 'test_fr08_occupied@example.com')
        assert parcel is not None
        assert parcel.locker_id == locker_id_to_test # Ensure it used the intended locker
        
        # Admin marks it 'out_of_service' (this part is fine)
        response_to_oos = logged_in_admin_client.post(
            f'/admin/locker/{locker_id_to_test}/set-status',
            data={'new_status': 'out_of_service'},
            follow_redirects=True
        )
        assert response_to_oos.status_code == 200
        assert db.session.get(Locker, locker_id_to_test).status == 'out_of_service'

        # Attempt to mark 'out_of_service' (but still occupied by 'deposited' parcel) to 'free'
        response_to_free_fail = logged_in_admin_client.post(
            f'/admin/locker/{locker_id_to_test}/set-status',
            data={'new_status': 'free'},
            follow_redirects=True
        )
        assert response_to_free_fail.status_code == 200
        assert f"Error updating locker {locker_id_to_test}: Cannot set locker to 'free'. Parcel ID {parcel.id} is still marked as 'deposited' in this locker.".encode() in response_to_free_fail.data
        assert db.session.get(Locker, locker_id_to_test).status == 'out_of_service' # Should remain OOS
