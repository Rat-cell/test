import pytest
from app.persistence.models import Locker, Parcel, AdminUser, AuditLog, LockerSensorData # Import LockerSensorData
from app import db # Import db for direct session manipulation if needed
from app.application.services import log_audit_event, assign_locker_and_create_parcel, generate_pin_and_hash # Add generate_pin_and_hash
import json # Add this
from flask import current_app, url_for # Import current_app and url_for
from unittest.mock import patch # For mocking
from datetime import datetime, timedelta # Ensure datetime and timedelta are imported

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
            'recipient_email': 'sender@example.com',
            'confirm_recipient_email': 'sender@example.com' # Added for existing test
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

# Tests for Email Confirmation in Deposit Parcel Route
def test_deposit_parcel_email_confirmation_success(client, init_database, app):
    with app.app_context():
        # Ensure a small locker is available
        assert Locker.query.filter_by(size='small', status='free').first() is not None
        initial_parcel_count = Parcel.query.count()

        response = client.post('/deposit', data={
            'parcel_size': 'small',
            'recipient_email': 'test_success@example.com',
            'confirm_recipient_email': 'test_success@example.com'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"Deposit Successful!" in response.data
        assert b"Recipient PIN:" in response.data
        assert Parcel.query.count() == initial_parcel_count + 1
        new_parcel = Parcel.query.filter_by(recipient_email='test_success@example.com').first()
        assert new_parcel is not None

def test_deposit_parcel_email_mismatch_error(client, init_database, app):
    with app.app_context():
        # Ensure a small locker is available
        assert Locker.query.filter_by(size='small', status='free').first() is not None
        initial_parcel_count = Parcel.query.count()

        response = client.post('/deposit', data={
            'parcel_size': 'small',
            'recipient_email': 'test_mismatch@example.com',
            'confirm_recipient_email': 'test_mismatch_different@example.com'
        }, follow_redirects=True)

        assert response.status_code == 200 # Stays on the deposit form
        assert b"Email addresses do not match. Please try again." in response.data
        assert b"Deposit Successful!" not in response.data
        assert Parcel.query.count() == initial_parcel_count # No new parcel created

def test_deposit_parcel_missing_confirm_email_error(client, init_database, app):
    with app.app_context():
        # Ensure a small locker is available
        assert Locker.query.filter_by(size='small', status='free').first() is not None
        initial_parcel_count = Parcel.query.count()

        response = client.post('/deposit', data={
            'parcel_size': 'small',
            'recipient_email': 'test_missing_confirm@example.com',
            # 'confirm_recipient_email' is deliberately omitted
        }, follow_redirects=True)

        assert response.status_code == 200 # Stays on the deposit form
        assert b"Please confirm the recipient email address." in response.data
        assert b"Deposit Successful!" not in response.data
        assert Parcel.query.count() == initial_parcel_count # No new parcel created

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

# Tests for Parcel Interaction Confirmation API Endpoints
def test_api_retract_deposit_success(client, init_database, app): # client fixture for making requests
    with app.app_context():
        # 1. Setup: Deposit a parcel
        parcel, _, _ = assign_locker_and_create_parcel('small', 'api_retract_success@example.com')
        assert parcel is not None
        original_locker_id = parcel.locker_id

        # 2. Action: POST to the retract endpoint
        response = client.post(f'/api/v1/deposit/{parcel.id}/retract')
        
        # 3. Assert: HTTP 200, JSON response, DB state, Audit log
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert response_data['parcel_id'] == parcel.id
        assert response_data['new_parcel_status'] == 'retracted_by_sender'
        assert response_data['locker_id'] == original_locker_id
        assert response_data['new_locker_status'] == 'free' # Assuming locker was 'occupied'

        assert db.session.get(Parcel, parcel.id).status == 'retracted_by_sender'
        assert db.session.get(Locker, original_locker_id).status == 'free'

        log_entry = AuditLog.query.filter_by(action="USER_DEPOSIT_RETRACTED", details__contains=str(parcel.id)).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None

def test_api_retract_deposit_fail_conditions(client, init_database, app):
    with app.app_context():
        # Parcel not found
        response_not_found = client.post('/api/v1/deposit/99999/retract')
        assert response_not_found.status_code == 404
        assert json.loads(response_not_found.data)['message'] == "Parcel not found."

        # Parcel not in 'deposited' state
        parcel, plain_pin, _ = assign_locker_and_create_parcel('small', 'api_retract_fail@example.com')
        assert parcel is not None
        # Pick up the parcel to change its state
        from app.application.services import process_pickup # Import here to avoid circular if at top
        process_pickup(plain_pin) 
        assert db.session.get(Parcel, parcel.id).status == 'picked_up'
        
        response_wrong_state = client.post(f'/api/v1/deposit/{parcel.id}/retract')
        assert response_wrong_state.status_code == 409 # Conflict
        assert "not in 'deposited' state" in json.loads(response_wrong_state.data)['message']

def test_api_dispute_pickup_success(client, init_database, app):
    with app.app_context():
        # 1. Setup: Deposit and then pickup a parcel
        parcel, plain_pin, _ = assign_locker_and_create_parcel('small', 'api_dispute_success@example.com')
        assert parcel is not None
        original_locker_id = parcel.locker_id
        from app.application.services import process_pickup # Import here
        process_pickup(plain_pin)
        assert db.session.get(Parcel, parcel.id).status == 'picked_up'

        # 2. Action: POST to the dispute endpoint
        response = client.post(f'/api/v1/pickup/{parcel.id}/dispute')

        # 3. Assert: HTTP 200, JSON response, DB state, Audit log
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert response_data['parcel_id'] == parcel.id
        assert response_data['new_parcel_status'] == 'pickup_disputed'
        assert response_data['locker_id'] == original_locker_id
        assert response_data['new_locker_status'] == 'disputed_contents'

        assert db.session.get(Parcel, parcel.id).status == 'pickup_disputed'
        assert db.session.get(Locker, original_locker_id).status == 'disputed_contents'
        
        log_entry = AuditLog.query.filter_by(action="USER_PICKUP_DISPUTED", details__contains=str(parcel.id)).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None

def test_api_dispute_pickup_fail_conditions(client, init_database, app):
    with app.app_context():
        # Parcel not found
        response_not_found = client.post('/api/v1/pickup/99999/dispute')
        assert response_not_found.status_code == 404
        assert json.loads(response_not_found.data)['message'] == "Parcel not found."

        # Parcel not in 'picked_up' state (still 'deposited')
        parcel, _, _ = assign_locker_and_create_parcel('small', 'api_dispute_fail@example.com')
        assert parcel is not None
        assert db.session.get(Parcel, parcel.id).status == 'deposited' # Still deposited
        
        response_wrong_state = client.post(f'/api/v1/pickup/{parcel.id}/dispute')
        assert response_wrong_state.status_code == 409 # Conflict
        assert "not in 'picked_up' state" in json.loads(response_wrong_state.data)['message']

# Tests for Report Missing Item (FR-06) API and Admin UI

# API Tests for /api/v1/parcel/<parcel_id>/report-missing
def test_api_report_missing_success(client, init_database, app):
    with app.app_context():
        # 1. Setup: Deposit a parcel
        parcel, _, _ = assign_locker_and_create_parcel('small', 'api_report_missing_success@example.com')
        assert parcel is not None
        original_locker_id = parcel.locker_id

        # 2. Action: POST to the report-missing endpoint
        response = client.post(f'/api/v1/parcel/{parcel.id}/report-missing')
        
        # 3. Assert: HTTP 200, JSON response, DB state, Audit log
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert response_data['parcel_id'] == parcel.id
        assert response_data['new_parcel_status'] == 'missing'
        assert response_data['locker_id'] == original_locker_id
        # 'new_locker_status' is not returned by current API implementation, so not asserted here

        assert db.session.get(Parcel, parcel.id).status == 'missing'
        assert db.session.get(Locker, original_locker_id).status == 'out_of_service'

        log_entry = AuditLog.query.filter_by(action="PARCEL_REPORTED_MISSING_BY_RECIPIENT", details__contains=str(parcel.id)).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['original_parcel_status'] == 'deposited'

def test_api_report_missing_fail_conditions(client, init_database, app):
    with app.app_context():
        # Parcel not found
        response_not_found = client.post('/api/v1/parcel/99999/report-missing')
        assert response_not_found.status_code == 404
        assert json.loads(response_not_found.data)['message'] == "Parcel not found."

        # Parcel not in 'deposited' or 'pickup_disputed' state (e.g., 'picked_up')
        parcel, plain_pin, _ = assign_locker_and_create_parcel('small', 'api_report_missing_fail@example.com')
        assert parcel is not None
        from app.application.services import process_pickup # Import for setup
        process_pickup(plain_pin) # Change status to 'picked_up'
        assert db.session.get(Parcel, parcel.id).status == 'picked_up'
        
        response_wrong_state = client.post(f'/api/v1/parcel/{parcel.id}/report-missing')
        assert response_wrong_state.status_code == 409 # Conflict
        assert "cannot be reported missing by recipient from its current state: 'picked_up'" in json.loads(response_wrong_state.data)['message']

# Admin UI Tests for FR-06
def test_admin_view_parcel_page(logged_in_admin_client, init_database, app):
    with app.app_context():
        # 1. Setup: Deposit a parcel
        parcel_to_view, _, _ = assign_locker_and_create_parcel('small', 'admin_view_parcel@example.com')
        assert parcel_to_view is not None

        # 2. Action: GET the parcel view page
        response = logged_in_admin_client.get(f'/admin/parcel/{parcel_to_view.id}/view')
        
        # 3. Assert: HTTP 200, content
        assert response.status_code == 200
        assert f"Parcel Details: ID {parcel_to_view.id}".encode() in response.data
        assert parcel_to_view.recipient_email.encode() in response.data
        assert parcel_to_view.status.encode() in response.data
        # Check for "Mark Parcel as Missing" button (since status is 'deposited')
        assert b"Mark Parcel as Missing" in response.data

        # Test with a non-existent parcel ID
        response_not_found = logged_in_admin_client.get('/admin/parcel/99999/view', follow_redirects=True)
        assert response_not_found.status_code == 200 # Redirects to manage_lockers
        assert b"Parcel ID 99999 not found." in response_not_found.data

def test_admin_mark_parcel_missing_ui_flow(logged_in_admin_client, init_database, app):
    with app.app_context():
        # Test with a 'deposited' parcel
        parcel_dep, _, _ = assign_locker_and_create_parcel('small', 'admin_mark_missing_dep@example.com')
        assert parcel_dep is not None
        original_locker_id_dep = parcel_dep.locker_id

        response_dep = logged_in_admin_client.post(f'/admin/parcel/{parcel_dep.id}/mark-missing', follow_redirects=True)
        assert response_dep.status_code == 200
        assert f"Parcel {parcel_dep.id} successfully marked as missing.".encode() in response_dep.data
        assert db.session.get(Parcel, parcel_dep.id).status == 'missing'
        assert db.session.get(Locker, original_locker_id_dep).status == 'out_of_service'
        
        log_dep = AuditLog.query.filter(
            AuditLog.action == "ADMIN_MARKED_PARCEL_MISSING", 
            AuditLog.details.like(f'%"parcel_id": {parcel_dep.id}%'),
            AuditLog.details.like(f'%"original_parcel_status": "deposited"%')
        ).order_by(AuditLog.timestamp.desc()).first()
        assert log_dep is not None

        # Test with a 'pickup_disputed' parcel
        parcel_dis, plain_pin_dis, _ = assign_locker_and_create_parcel('medium', 'admin_mark_missing_dis@example.com') # Use different locker
        assert parcel_dis is not None
        original_locker_id_dis = parcel_dis.locker_id
        from app.application.services import process_pickup, dispute_pickup # Imports for setup
        process_pickup(plain_pin_dis)
        dispute_pickup(parcel_dis.id)
        assert db.session.get(Parcel, parcel_dis.id).status == 'pickup_disputed'
        assert db.session.get(Locker, original_locker_id_dis).status == 'disputed_contents'

        response_dis = logged_in_admin_client.post(f'/admin/parcel/{parcel_dis.id}/mark-missing', follow_redirects=True)
        assert response_dis.status_code == 200
        assert f"Parcel {parcel_dis.id} successfully marked as missing.".encode() in response_dis.data
        assert db.session.get(Parcel, parcel_dis.id).status == 'missing'
        assert db.session.get(Locker, original_locker_id_dis).status == 'out_of_service'

        log_dis = AuditLog.query.filter(
            AuditLog.action == "ADMIN_MARKED_PARCEL_MISSING", 
            AuditLog.details.like(f'%"parcel_id": {parcel_dis.id}%'),
            AuditLog.details.like(f'%"original_parcel_status": "pickup_disputed"%')
        ).order_by(AuditLog.timestamp.desc()).first()
        assert log_dis is not None

# Tests for API Endpoint: /api/v1/lockers/<int:locker_id>/sensor_data
def test_api_submit_locker_sensor_data_success(client, init_database, app):
    with app.app_context():
        # Locker 1 is created by init_database
        locker = db.session.get(Locker, 1)
        assert locker is not None

        payload = {'has_contents': True}
        response = client.post(f'/api/v1/lockers/{locker.id}/sensor_data', json=payload)

        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['status'] == 'success'
        assert response_data['message'] == 'Sensor data recorded successfully.'
        assert 'sensor_data_id' in response_data

        sensor_record = db.session.get(LockerSensorData, response_data['sensor_data_id'])
        assert sensor_record is not None
        assert sensor_record.locker_id == locker.id
        assert sensor_record.has_contents is True

def test_api_submit_locker_sensor_data_error_handling(client, init_database, app):
    with app.app_context():
        # Locker 1 exists
        locker_id_exists = 1
        locker_id_non_existent = 999

        # Invalid Payload (missing has_contents)
        response_invalid_payload = client.post(f'/api/v1/lockers/{locker_id_exists}/sensor_data', json={})
        assert response_invalid_payload.status_code == 400
        assert b"'has_contents' must be a boolean and is required" in response_invalid_payload.data

        # Invalid has_contents type
        response_invalid_type = client.post(f'/api/v1/lockers/{locker_id_exists}/sensor_data', json={'has_contents': 'not_a_boolean'})
        assert response_invalid_type.status_code == 400
        assert b"'has_contents' must be a boolean and is required" in response_invalid_type.data
        
        # No JSON data provided
        response_no_data = client.post(f'/api/v1/lockers/{locker_id_exists}/sensor_data') # No json kwarg
        assert response_no_data.status_code == 400
        assert b"No data provided" in response_no_data.data


        # Locker Not Found
        response_locker_not_found = client.post(f'/api/v1/lockers/{locker_id_non_existent}/sensor_data', json={'has_contents': False})
        assert response_locker_not_found.status_code == 404
        assert b"Locker not found" in response_locker_not_found.data

def test_api_submit_locker_sensor_data_method_not_allowed(client, init_database, app):
    with app.app_context():
        locker_id = 1 # Locker 1 exists
        response = client.get(f'/api/v1/lockers/{locker_id}/sensor_data')
        assert response.status_code == 405

# Tests for Sensor Data in Admin manage_lockers View
def test_admin_manage_lockers_displays_sensor_data(logged_in_admin_client, init_database, app):
    with app.app_context():
        # Locker 1 exists from init_database
        locker1 = db.session.get(Locker, 1)
        assert locker1 is not None

        # Add sensor data for Locker 1: Present
        sensor_data_present = LockerSensorData(locker_id=locker1.id, has_contents=True)
        db.session.add(sensor_data_present)
        
        # Locker 2 exists from init_database
        locker2 = db.session.get(Locker, 2)
        assert locker2 is not None
        # Add sensor data for Locker 2: Empty
        sensor_data_empty = LockerSensorData(locker_id=locker2.id, has_contents=False)
        db.session.add(sensor_data_empty)

        # Locker 3 exists from init_database, will have no sensor data
        locker3 = db.session.get(Locker, 3)
        assert locker3 is not None
        
        db.session.commit()

        response = logged_in_admin_client.get('/admin/lockers')
        assert response.status_code == 200
        response_html = response.data.decode('utf-8')

        # Check for Locker 1 data - Sensor: Present
        # This is a bit fragile, depends on exact HTML structure
        assert f"<td>{locker1.id}</td>" in response_html
        assert "<td>Present</td>" in response_html # Assuming this is how sensor data (True) is rendered for locker1

        # Check for Locker 2 data - Sensor: Empty
        assert f"<td>{locker2.id}</td>" in response_html
        assert "<td>Empty</td>" in response_html # Assuming this is how sensor data (False) is rendered for locker2

        # Check for Locker 3 data - Sensor: N/A
        assert f"<td>{locker3.id}</td>" in response_html
        assert "<td>N/A</td>" in response_html # Assuming this is how no sensor data is rendered for locker3

# Tests for Sensor Data Configuration in Admin manage_lockers View

def test_admin_manage_lockers_sensor_feature_disabled(logged_in_admin_client, app, init_database):
    with app.app_context():
        original_sensor_feature = current_app.config.get('ENABLE_LOCKER_SENSOR_DATA_FEATURE')
        try:
            current_app.config['ENABLE_LOCKER_SENSOR_DATA_FEATURE'] = False
            
            # Locker 1 exists from init_database
            locker1 = db.session.get(Locker, 1)
            assert locker1 is not None

            response = logged_in_admin_client.get('/admin/lockers')
            assert response.status_code == 200
            response_html = response.data.decode('utf-8')

            # Check for Locker 1 data - Sensor: Disabled
            # Ensure the table cell for sensor status contains "Sensor: Disabled"
            # This regex is a bit more robust to slight HTML changes around the ID.
            # It looks for the row of locker 1 and then the sensor status cell.
            import re
            # Pattern to find the row for Locker 1 and then check its sensor status column
            # This assumes Sensor Status is the 4th column (index 3) after ID, Size, Current Status
            # And that the HTML structure is <td>ID</td> ... <td>Sensor Status</td>
            # A more robust way would be to parse HTML if this becomes too fragile.
            # For now, let's expect a structure like: <td>1</td>...<td>Sensor: Disabled</td>
            # We can check for a segment of the row that includes the locker ID and the expected text.
            assert f"<td>{locker1.id}</td>" in response_html # Verify row for locker 1 exists
            assert "<td>Sensor: Disabled</td>" in response_html # Verify "Sensor: Disabled" is present for that row

        finally:
            current_app.config['ENABLE_LOCKER_SENSOR_DATA_FEATURE'] = original_sensor_feature

def test_admin_manage_lockers_sensor_feature_enabled_specific_data(logged_in_admin_client, app, init_database):
    with app.app_context():
        original_sensor_feature = current_app.config.get('ENABLE_LOCKER_SENSOR_DATA_FEATURE')
        original_default_state = current_app.config.get('DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE')
        try:
            current_app.config['ENABLE_LOCKER_SENSOR_DATA_FEATURE'] = True
            # Ensure default state is something known, e.g. False, so it doesn't interfere if sensor_data is None
            current_app.config['DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE'] = False 

            locker_id_specific = 1 # Use Locker 1 from init_database
            locker = db.session.get(Locker, locker_id_specific)
            assert locker is not None

            # Add specific sensor data
            sensor_data = LockerSensorData(locker_id=locker_id_specific, has_contents=True)
            db.session.add(sensor_data)
            db.session.commit()

            response = logged_in_admin_client.get('/admin/lockers')
            assert response.status_code == 200
            response_html = response.data.decode('utf-8')
            
            # Check for Locker with specific data
            assert f"<td>{locker_id_specific}</td>" in response_html
            # The sensor data is "Present" because has_contents=True
            assert "<td>Sensor: Present</td>" in response_html 

        finally:
            current_app.config['ENABLE_LOCKER_SENSOR_DATA_FEATURE'] = original_sensor_feature
            current_app.config['DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE'] = original_default_state


# Tests for /request-new-pin route
def test_request_new_pin_form_get_request(client, init_database, app):
    with app.app_context():
        response = client.get(url_for('main.request_new_pin_action'))
        assert response.status_code == 200
        assert b"Request New PIN" in response.data
        assert b"Your Email Address:" in response.data
        assert b'name="recipient_email"' in response.data
        assert b"Locker ID:" in response.data
        assert b'name="locker_id"' in response.data
        assert b"Request New PIN</button>" in response.data

@patch('app.presentation.routes.request_pin_regeneration_by_recipient')
def test_request_new_pin_form_post_success(mock_service_call, client, init_database, app):
    with app.app_context():
        # Setup: Create a locker and a deposited parcel
        locker = Locker.query.filter_by(id=1).first() # From init_database
        assert locker is not None
        
        test_email = "test_regen@example.com"
        # No need to actually create parcel if service is mocked,
        # but the service would normally require it.
        # For route testing, we only care the service is called.

        mock_service_call.return_value = True # Simulate service attempting regeneration

        response = client.post(url_for('main.request_new_pin_action'), data={
            'recipient_email': test_email,
            'locker_id': str(locker.id) # Ensure locker_id is string, as it comes from form
        }, follow_redirects=True)

        assert response.status_code == 200 # After redirect, lands on the same page
        assert b"If your details matched an active parcel eligible for a new PIN, an email with the new PIN has been sent" in response.data
        mock_service_call.assert_called_once_with(test_email, str(locker.id))

@patch('app.presentation.routes.request_pin_regeneration_by_recipient')
def test_request_new_pin_form_post_missing_fields(mock_service_call, client, init_database, app):
    with app.app_context():
        # Case 1: Missing recipient_email
        response_missing_email = client.post(url_for('main.request_new_pin_action'), data={
            'locker_id': '1'
        }, follow_redirects=True)
        assert response_missing_email.status_code == 200 # Stays on form
        assert b"Email and Locker ID are required." in response_missing_email.data
        mock_service_call.assert_not_called() # Service should not be called

        # Case 2: Missing locker_id
        mock_service_call.reset_mock() # Reset mock for the next call
        response_missing_locker_id = client.post(url_for('main.request_new_pin_action'), data={
            'recipient_email': 'test@example.com'
        }, follow_redirects=True)
        assert response_missing_locker_id.status_code == 200 # Stays on form
        assert b"Email and Locker ID are required." in response_missing_locker_id.data
        mock_service_call.assert_not_called() # Service should not be called

@patch('app.presentation.routes.request_pin_regeneration_by_recipient')
def test_request_new_pin_form_post_generic_message_security(mock_service_call, client, init_database, app):
    with app.app_context():
        # Simulate a scenario where the service call would internally determine "no match" or "too late"
        # The route should still flash the generic message.
        mock_service_call.return_value = False # Simulate service indicating no action taken (e.g., no match, too late)
        
        response = client.post(url_for('main.request_new_pin_action'), data={
            'recipient_email': 'any_email@example.com',
            'locker_id': '99' # Potentially non-existent
        }, follow_redirects=True)

        assert response.status_code == 200
        # Crucially, the message is generic and does not reveal if the details were valid or not
        assert b"If your details matched an active parcel eligible for a new PIN, an email with the new PIN has been sent" in response.data
        mock_service_call.assert_called_once_with('any_email@example.com', '99')
            # Clean up sensor data to avoid affecting other tests if db state persists across tests
            LockerSensorData.query.filter_by(locker_id=locker_id_specific).delete()
            db.session.commit()


def test_admin_manage_lockers_no_sensor_data_default_false(logged_in_admin_client, app, init_database):
    with app.app_context():
        original_sensor_feature = current_app.config.get('ENABLE_LOCKER_SENSOR_DATA_FEATURE')
        original_default_state = current_app.config.get('DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE')
        try:
            current_app.config['ENABLE_LOCKER_SENSOR_DATA_FEATURE'] = True
            current_app.config['DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE'] = False

            locker_id_no_data = 2 # Use Locker 2 from init_database
            locker = db.session.get(Locker, locker_id_no_data)
            assert locker is not None
            # Ensure no sensor data for this locker
            LockerSensorData.query.filter_by(locker_id=locker_id_no_data).delete()
            db.session.commit()

            response = logged_in_admin_client.get('/admin/lockers')
            assert response.status_code == 200
            response_html = response.data.decode('utf-8')

            assert f"<td>{locker_id_no_data}</td>" in response_html
            assert "<td>Sensor: Empty (default)</td>" in response_html

        finally:
            current_app.config['ENABLE_LOCKER_SENSOR_DATA_FEATURE'] = original_sensor_feature
            current_app.config['DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE'] = original_default_state

def test_admin_manage_lockers_no_sensor_data_default_true(logged_in_admin_client, app, init_database):
    with app.app_context():
        original_sensor_feature = current_app.config.get('ENABLE_LOCKER_SENSOR_DATA_FEATURE')
        original_default_state = current_app.config.get('DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE')
        try:
            current_app.config['ENABLE_LOCKER_SENSOR_DATA_FEATURE'] = True
            current_app.config['DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE'] = True

            locker_id_no_data_default_true = 3 # Use Locker 3 from init_database
            locker = db.session.get(Locker, locker_id_no_data_default_true)
            assert locker is not None
             # Ensure no sensor data for this locker
            LockerSensorData.query.filter_by(locker_id=locker_id_no_data_default_true).delete()
            db.session.commit()

            response = logged_in_admin_client.get('/admin/lockers')
            assert response.status_code == 200
            response_html = response.data.decode('utf-8')
            
            assert f"<td>{locker_id_no_data_default_true}</td>" in response_html
            assert "<td>Sensor: Present (default)</td>" in response_html
            
        finally:
            current_app.config['ENABLE_LOCKER_SENSOR_DATA_FEATURE'] = original_sensor_feature
            current_app.config['DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE'] = original_default_state
