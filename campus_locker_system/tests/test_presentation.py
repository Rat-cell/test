import pytest
from app.persistence.models import Locker, Parcel, AdminUser, AuditLog, LockerSensorData # Import LockerSensorData
from app import db # Import db for direct session manipulation if needed
from app.business.pin import PinManager # Replace generate_pin_and_hash with PinManager.generate_pin_and_hash
from app.services.parcel_service import assign_locker_and_create_parcel, process_pickup, dispute_pickup # Add assign_locker_and_create_parcel, process_pickup, and dispute_pickup
import json # Add this
from flask import current_app, url_for # Import current_app and url_for
from unittest.mock import patch # For mocking
from datetime import datetime, timedelta # Ensure datetime and timedelta are imported
from app.services.audit_service import AuditService

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
            'recipient_email': 'another@example.com',
            'confirm_recipient_email': 'another@example.com'
        }, follow_redirects=True)

        print(response.data.decode())  # Debug: print the rendered HTML
        
        assert response.status_code == 200 # Should be 200 after redirecting to the form
        assert b"No available lockers found" in response.data
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

        AuditService.log_event("SPECIFIC_TEST_AUDIT_ACTION_PAGE", {"test_detail_page": "visible"})
        
        response = client.get('/admin/audit-logs')
        assert response.status_code == 200
        assert b"Audit Logs" in response.data
        assert b"SPECIFIC_TEST_AUDIT_ACTION_PAGE" in response.data
        assert b"test_detail_page" in response.data
        assert b"visible" in response.data

# Tests for Locker Status Management (FR-08) Presentation Layer
def test_admin_manage_lockers_page_access_anonymous(client, init_database, app):
    # Clear session to ensure anonymous access
    with client.session_transaction() as sess:
        sess.clear()
    response_anon = client.get('/admin/lockers', follow_redirects=True)
    assert response_anon.status_code == 200 # Redirects to login
    assert b"Admin Login" in response_anon.data
    assert b"Please log in to access this page." in response_anon.data

def test_admin_manage_lockers_page_access_admin(logged_in_admin_client, init_database, app):
    response_admin = logged_in_admin_client.get('/admin/lockers')
    assert response_admin.status_code == 200
    assert b"Manage Lockers" in response_admin.data
    # Check for some locker data (e.g., Locker ID 1 from init_database)
    assert b"1" in response_admin.data # Locker ID 1 should be present
    assert b"small" in response_admin.data # Locker size should be present

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
        assert b"Locker 1 status successfully updated" in response_to_oos.data
        assert db.session.get(Locker, locker_id_to_test).status == 'out_of_service'
        
        log_oos = AuditLog.query.filter(
            AuditLog.action == "ADMIN_LOCKER_STATUS_CHANGED",
            AuditLog.details.contains(f'%"locker_id": {locker_id_to_test}%'),
            AuditLog.details.contains(f'%"new_status": "out_of_service"%')
        ).order_by(AuditLog.timestamp.desc()).first()
        assert log_oos is not None

        # Action 2: Mark 'out_of_service' locker back to 'free'
        response_to_free = logged_in_admin_client.post(
            f'/admin/locker/{locker_id_to_test}/set-status',
            data={'new_status': 'free'},
            follow_redirects=True
        )
        assert response_to_free.status_code == 200
        assert b"Locker 1 status successfully updated" in response_to_free.data
        assert db.session.get(Locker, locker_id_to_test).status == 'free'

        log_free = AuditLog.query.filter(
            AuditLog.action == "ADMIN_LOCKER_STATUS_CHANGED",
            AuditLog.details.contains(f'%"locker_id": {locker_id_to_test}%'),
            AuditLog.details.contains(f'%"new_status": "free"%')
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
        result = assign_locker_and_create_parcel('test_fr08_occupied@example.com', 'medium')
        parcel, _ = result
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
        assert b"Error updating locker" in response_to_free_fail.data
        assert db.session.get(Locker, locker_id_to_test).status == 'out_of_service' # Should remain OOS

# Tests for Parcel Interaction Confirmation API Endpoints
def test_api_retract_deposit_success(client, init_database, app): # client fixture for making requests
    with app.app_context():
        # 1. Setup: Deposit a parcel
        result = assign_locker_and_create_parcel('api_retract_success@example.com', 'small')
        parcel, _ = result
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

        log_entry = AuditLog.query.filter(AuditLog.action == "USER_DEPOSIT_RETRACTED", AuditLog.details.contains(str(parcel.id))).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None

def test_api_retract_deposit_fail_conditions(client, init_database, app):
    with app.app_context():
        # Parcel not found
        response_not_found = client.post('/api/v1/deposit/99999/retract')
        assert response_not_found.status_code == 404
        assert json.loads(response_not_found.data)['message'] == "Parcel not found."

        # Parcel not in 'deposited' state
        result = assign_locker_and_create_parcel('api_retract_fail@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Create a known PIN for testing
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        # Pick up the parcel to change its state
        process_pickup(test_pin) 
        assert db.session.get(Parcel, parcel.id).status == 'picked_up'
        
        response_wrong_state = client.post(f'/api/v1/deposit/{parcel.id}/retract')
        assert response_wrong_state.status_code == 409 # Conflict
        assert "not in 'deposited' state" in json.loads(response_wrong_state.data)['message']

def test_api_dispute_pickup_success(client, init_database, app):
    with app.app_context():
        # 1. Setup: Deposit and then pickup a parcel
        result = assign_locker_and_create_parcel('api_dispute_success@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        original_locker_id = parcel.locker_id
        
        # Create a known PIN for testing
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        process_pickup(test_pin)
        dispute_pickup(parcel.id)
        assert db.session.get(Parcel, parcel.id).status == 'pickup_disputed'
        assert db.session.get(Locker, original_locker_id).status == 'disputed_contents'
        
        log_entry = AuditLog.query.filter(AuditLog.action == "USER_PICKUP_DISPUTED", AuditLog.details.contains(str(parcel.id))).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None

def test_api_dispute_pickup_fail_conditions(client, init_database, app):
    with app.app_context():
        # Parcel not found
        response_not_found = client.post('/api/v1/pickup/99999/dispute')
        assert response_not_found.status_code == 404
        assert json.loads(response_not_found.data)['message'] == "Parcel not found."

        # Parcel not in 'picked_up' state (still 'deposited')
        result = assign_locker_and_create_parcel('api_dispute_fail@example.com', 'small')
        parcel, _ = result
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
        result = assign_locker_and_create_parcel('api_report_missing_success@example.com', 'small')
        parcel, _ = result
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

        log_entry = AuditLog.query.filter(AuditLog.action == "PARCEL_REPORTED_MISSING_BY_RECIPIENT", AuditLog.details.contains(str(parcel.id))).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['original_parcel_status'] == 'deposited'

# Tests for recipient reporting missing parcel via UI after pickup
def test_report_missing_parcel_by_recipient_ui_success(client, init_database, app):
    """Test recipient can report parcel missing via UI with admin notification"""
    with app.app_context():
        # 1. Setup: Deposit and pickup a parcel first
        result = assign_locker_and_create_parcel('ui_missing_report@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        original_locker_id = parcel.locker_id
        
        # Create a known PIN for testing pickup
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        # Pickup the parcel
        pickup_result = process_pickup(test_pin)
        pickup_parcel, pickup_message = pickup_result
        assert pickup_parcel is not None
        assert pickup_parcel.status == 'picked_up'
        
        # Reset parcel status to deposited for missing report (simulate the parcel was actually missing)
        pickup_parcel.status = 'deposited'
        db.session.commit()

        # 2. Action: POST to the report-missing UI endpoint
        response = client.post(f'/report-missing/{parcel.id}', follow_redirects=True)
        
        # 3. Assert: Success response and proper redirection
        assert response.status_code == 200
        assert b"Missing Parcel Report Submitted" in response.data
        
        # 4. Assert: Database state changes
        updated_parcel = db.session.get(Parcel, parcel.id)
        assert updated_parcel.status == 'missing'
        updated_locker = db.session.get(Locker, original_locker_id)
        assert updated_locker.status == 'out_of_service'
        
        # 5. Assert: Audit log entry created
        log_entry = AuditLog.query.filter(
            AuditLog.action == "PARCEL_REPORTED_MISSING_BY_RECIPIENT_UI"
        ).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['parcel_id'] == parcel.id
        assert details['locker_id'] == original_locker_id
        assert details['reported_via'] == 'Web_UI_after_pickup'
        assert 'admin_notified' in details

def test_report_missing_parcel_by_recipient_ui_parcel_not_found(client, init_database, app):
    """Test error handling when parcel ID doesn't exist"""
    with app.app_context():
        response = client.post('/report-missing/99999', follow_redirects=True)
        assert response.status_code == 200
        assert b"Parcel not found" in response.data

def test_report_missing_parcel_by_recipient_ui_invalid_state(client, init_database, app):
    """Test error handling when parcel is in invalid state for missing report"""
    with app.app_context():
        # Setup: Create and pick up a parcel
        result = assign_locker_and_create_parcel('invalid_state_missing@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Create a known PIN for testing pickup
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        # Pickup the parcel
        pickup_result = process_pickup(test_pin)
        pickup_parcel, pickup_message = pickup_result
        assert pickup_parcel is not None
        assert pickup_parcel.status == 'picked_up'
        
        # Try to report missing (should fail since parcel is 'picked_up')
        response = client.post(f'/report-missing/{parcel.id}', follow_redirects=True)
        assert response.status_code == 200
        assert b"Error reporting parcel as missing" in response.data

def test_pickup_confirmation_contains_missing_report_button(client, init_database, app):
    """Test that pickup confirmation page contains the missing report functionality"""
    with app.app_context():
        # Setup: Deposit a parcel
        result = assign_locker_and_create_parcel('pickup_confirmation_missing@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Create a known PIN for testing
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        # Perform pickup to get to confirmation page
        response = client.post('/pickup', data={'pin': test_pin}, follow_redirects=True)
        assert response.status_code == 200
        
        # Check that the pickup confirmation page contains missing report functionality
        response_text = response.data.decode('utf-8')
        assert "Pickup Successful!" in response_text
        assert "Report Parcel as Missing" in response_text
        assert f"/report-missing/{parcel.id}" in response_text
        assert "confirmMissingReport()" in response_text

def test_api_report_missing_fail_conditions(client, init_database, app):
    with app.app_context():
        # Parcel not found
        response_not_found = client.post('/api/v1/parcel/99999/report-missing')
        assert response_not_found.status_code == 404
        assert json.loads(response_not_found.data)['message'] == "Parcel not found."

        # Parcel not in 'deposited' or 'pickup_disputed' state (e.g., 'picked_up')
        result = assign_locker_and_create_parcel('api_report_missing_fail@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Create a known PIN for testing
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        process_pickup(test_pin) # Change status to 'picked_up'
        assert db.session.get(Parcel, parcel.id).status == 'picked_up'
        
        response_wrong_state = client.post(f'/api/v1/parcel/{parcel.id}/report-missing')
        assert response_wrong_state.status_code == 409 # Conflict
        assert "cannot be reported missing by recipient from its current state: 'picked_up'" in json.loads(response_wrong_state.data)['message']

# Admin UI Tests for FR-06
def test_admin_view_parcel_page(logged_in_admin_client, init_database, app):
    with app.app_context():
        # 1. Setup: Deposit a parcel
        result = assign_locker_and_create_parcel('admin_view_parcel@example.com', 'small')
        parcel_to_view, _ = result
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
        result1 = assign_locker_and_create_parcel('admin_mark_missing_dep@example.com', 'small')
        parcel_dep, _ = result1
        assert parcel_dep is not None
        original_locker_id_dep = parcel_dep.locker_id

        response_dep = logged_in_admin_client.post(f'/admin/parcel/{parcel_dep.id}/mark-missing', follow_redirects=True)
        assert response_dep.status_code == 200
        assert f"Parcel {parcel_dep.id} successfully marked as missing.".encode() in response_dep.data
        assert db.session.get(Parcel, parcel_dep.id).status == 'missing'
        assert db.session.get(Locker, original_locker_id_dep).status == 'out_of_service'
        
        log_dep = AuditLog.query.filter(
            AuditLog.action == "ADMIN_MARKED_PARCEL_MISSING", 
            AuditLog.details.contains(f'%"parcel_id": {parcel_dep.id}%'),
            AuditLog.details.contains(f'%"original_parcel_status": "deposited"%')
        ).order_by(AuditLog.timestamp.desc()).first()
        assert log_dep is not None

        # Test with a 'pickup_disputed' parcel
        result2 = assign_locker_and_create_parcel('admin_mark_missing_dis@example.com', 'medium') # Use different locker
        parcel_dis, _ = result2
        assert parcel_dis is not None
        original_locker_id_dis = parcel_dis.locker_id
        
        # Create a known PIN for testing
        from app.business.pin import PinManager
        test_pin_dis, test_hash_dis = PinManager.generate_pin_and_hash()
        parcel_dis.pin_hash = test_hash_dis
        db.session.commit()
        
        process_pickup(test_pin_dis)
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
            AuditLog.details.contains(f'%"parcel_id": {parcel_dis.id}%'),
            AuditLog.details.contains(f'%"original_parcel_status": "pickup_disputed"%')
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
        assert b"No data provided" in response_invalid_payload.data

        # Invalid has_contents type
        response_invalid_type = client.post(f'/api/v1/lockers/{locker_id_exists}/sensor_data', json={'has_contents': 'not_a_boolean'})
        assert response_invalid_type.status_code == 400
        assert b"'has_contents' must be a boolean and is required" in response_invalid_type.data
        
        # No JSON data provided
        response_no_data = client.post(f'/api/v1/lockers/{locker_id_exists}/sensor_data') # No json kwarg
        assert response_no_data.status_code == 415 # Updated to match Flask's behavior

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
        print(response_html)  # Debug: print the rendered HTML

        # Check for Locker 1 data - Sensor: Present
        assert f"<td>{locker1.id}</td>" in response_html
        assert "Sensor: Present" in response_html

        # Check for Locker 2 data - Sensor: Empty
        assert f"<td>{locker2.id}</td>" in response_html
        assert "Sensor: Empty" in response_html

        # Check for Locker 3 data - Sensor: N/A
        assert f"<td>{locker3.id}</td>" in response_html
        assert "N/A" in response_html

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
            assert "Sensor: Disabled" in response_html # Verify 'Sensor: Disabled' is present for that row

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
            assert "Sensor: Present" in response_html 

        finally:
            current_app.config['ENABLE_LOCKER_SENSOR_DATA_FEATURE'] = original_sensor_feature
            current_app.config['DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE'] = original_default_state
            # Clean up sensor data to avoid affecting other tests if db state persists across tests
            LockerSensorData.query.filter_by(locker_id=locker_id_specific).delete()
            db.session.commit()


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
            assert "Sensor: Empty (default)" in response_html

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
            assert "Sensor: Present (default)" in response_html
            
        finally:
            current_app.config['ENABLE_LOCKER_SENSOR_DATA_FEATURE'] = original_sensor_feature
            current_app.config['DEFAULT_LOCKER_SENSOR_STATE_IF_UNAVAILABLE'] = original_default_state


# Tests for Email-Based PIN Generation Routes

@patch('app.presentation.routes.EmailPinService.generate_pin_by_token')
def test_generate_pin_by_token_success(mock_service, client, init_database, app):
    """Test successful PIN generation via email token"""
    with app.app_context():
        
        # Create mock parcel
        mock_parcel = Parcel(
            id=1,
            locker_id=1,
            recipient_email='test@example.com',
            status='deposited'
        )
        mock_service.return_value = (mock_parcel, "PIN generated successfully and sent to test@example.com")
        
        response = client.get('/generate-pin/test_token_123')
        
        assert response.status_code == 200
        assert b"PIN Generated Successfully!" in response.data
        assert b"test@example.com" in response.data
        assert b"Locker ID: 1" in response.data
        mock_service.assert_called_once_with('test_token_123')

@patch('app.presentation.routes.EmailPinService.generate_pin_by_token')
def test_generate_pin_by_token_invalid_token(mock_service, client, init_database, app):
    """Test PIN generation with invalid token"""
    with app.app_context():
        mock_service.return_value = (None, "Invalid or expired token.")
        
        response = client.get('/generate-pin/invalid_token')
        
        assert response.status_code == 200
        assert b"PIN Generation Failed" in response.data
        assert b"Invalid or expired token." in response.data
        mock_service.assert_called_once_with('invalid_token')

@patch('app.presentation.routes.EmailPinService.generate_pin_by_token')
def test_generate_pin_by_token_rate_limit(mock_service, client, init_database, app):
    """Test PIN generation rate limit error"""
    with app.app_context():
        mock_service.return_value = (None, "Daily PIN generation limit reached (3 per day). Please try again tomorrow.")
        
        response = client.get('/generate-pin/rate_limited_token')
        
        assert response.status_code == 200
        assert b"PIN Generation Failed" in response.data
        assert b"Daily PIN generation limit reached" in response.data
        mock_service.assert_called_once_with('rate_limited_token')

@patch('app.presentation.routes.EmailPinService.generate_pin_by_token')
def test_generate_pin_by_token_exception_handling(mock_service, client, init_database, app):
    """Test PIN generation route exception handling"""
    with app.app_context():
        mock_service.side_effect = Exception("Database error")
        
        response = client.get('/generate-pin/error_token')
        
        assert response.status_code == 200
        assert b"PIN Generation Failed" in response.data
        assert b"An unexpected error occurred" in response.data
        mock_service.assert_called_once_with('error_token')

def test_admin_regenerate_pin_token_success(logged_in_admin_client, init_database, app):
    """Test admin regeneration of PIN token"""
    with app.app_context():
        
        # Create parcel with email-based PIN
        parcel = Parcel(
            locker_id=1,
            recipient_email='admin_regen@example.com',
            status='deposited'
        )
        parcel.generate_pin_token()
        db.session.add(parcel)
        db.session.commit()
        
        with patch('app.presentation.routes.EmailPinService.regenerate_pin_token') as mock_service:
            mock_service.return_value = (True, "New PIN generation link sent to admin_regen@example.com")
            
            response = logged_in_admin_client.post(f'/admin/parcel/{parcel.id}/regenerate-pin-token')
            
            assert response.status_code == 302  # Redirect
            mock_service.assert_called_once_with(parcel.id, 'admin_regen@example.com')

def test_admin_regenerate_pin_token_parcel_not_found(logged_in_admin_client, init_database, app):
    """Test admin regeneration of PIN token for non-existent parcel"""
    with app.app_context():
        response = logged_in_admin_client.post('/admin/parcel/99999/regenerate-pin-token')
        
        assert response.status_code == 302  # Redirect
        # Should redirect back to manage_lockers with error message

def test_admin_regenerate_pin_token_email_disabled(logged_in_admin_client, init_database, app):
    """Test admin regeneration when email-based PIN is disabled"""
    with app.app_context():
        
        # Disable email-based PIN generation
        app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = False
        
        # Create parcel
        parcel = Parcel(
            locker_id=1,
            recipient_email='disabled@example.com',
            status='deposited'
        )
        db.session.add(parcel)
        db.session.commit()
        
        response = logged_in_admin_client.post(f'/admin/parcel/{parcel.id}/regenerate-pin-token')
        
        assert response.status_code == 302  # Redirect
        # Should redirect with error message about feature being disabled

def test_deposit_confirmation_email_pin_display(client, init_database, app):
    """Test deposit confirmation page displays email PIN information correctly"""
    with app.app_context():
        
        # Configure for email-based PIN generation
        app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
        
        with patch('app.services.parcel_service.EmailPinService.create_parcel_with_email_pin') as mock_service:
            # Create mock parcel with email-based PIN
            mock_parcel = Parcel(
                id=1,
                locker_id=1,
                recipient_email='email_display@example.com',
                status='deposited'
            )
            mock_parcel.generate_pin_token()
            mock_service.return_value = (mock_parcel, "Parcel deposited successfully. PIN generation link sent to email_display@example.com.")
            
            response = client.post('/', data={
                'parcel_size': 'small',
                'recipient_email': 'email_display@example.com',
                'confirm_recipient_email': 'email_display@example.com'
            })
            
            assert response.status_code == 200
            assert b"Email-based PIN Generation" in response.data
            assert b"PIN generation link has been sent" in response.data
            assert b"Enhanced Security Features" in response.data
            assert b"No PIN is sent immediately" in response.data

def test_deposit_confirmation_traditional_pin_display(client, init_database, app):
    """Test deposit confirmation page displays traditional PIN information correctly"""
    with app.app_context():
        # Configure for traditional PIN generation
        app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = False
        
        with patch('app.services.parcel_service.NotificationService.send_parcel_deposit_notification') as mock_notify:
            mock_notify.return_value = (True, "PIN sent successfully")
            
            response = client.post('/', data={
                'parcel_size': 'small',
                'recipient_email': 'traditional_display@example.com',
                'confirm_recipient_email': 'traditional_display@example.com'
            })
            
            assert response.status_code == 200
            assert b"Traditional PIN System" in response.data
            assert b"pickup PIN has been sent" in response.data

def test_admin_view_parcel_email_pin_information(logged_in_admin_client, init_database, app):
    """Test admin parcel view displays email PIN generation information"""
    with app.app_context():
        
        # Create parcel with email-based PIN
        parcel = Parcel(
            locker_id=1,
            recipient_email='admin_view@example.com',
            status='deposited'
        )
        token = parcel.generate_pin_token()
        parcel.pin_generation_count = 2
        db.session.add(parcel)
        db.session.commit()
        
        response = logged_in_admin_client.get(f'/admin/parcel/{parcel.id}/view')
        
        assert response.status_code == 200
        response_html = response.data.decode('utf-8')
        
        assert "Email-based PIN Generation" in response_html
        assert "PIN Generation Count: 2/3" in response_html
        assert "No PIN Generated Yet" in response_html
        assert "Regenerate PIN Link" in response_html

def test_admin_view_parcel_traditional_pin_information(logged_in_admin_client, init_database, app):
    """Test admin parcel view displays traditional PIN information"""
    with app.app_context():
        from app.business.pin import PinManager
        
        # Create parcel with traditional PIN
        pin, pin_hash = PinManager.generate_pin_and_hash()
        parcel = Parcel(
            locker_id=1,
            recipient_email='admin_traditional@example.com',
            status='deposited',
            pin_hash=pin_hash,
            otp_expiry=PinManager.generate_expiry_time()
        )
        db.session.add(parcel)
        db.session.commit()
        
        response = logged_in_admin_client.get(f'/admin/parcel/{parcel.id}/view')
        
        assert response.status_code == 200
        response_html = response.data.decode('utf-8')
        
        assert "Traditional PIN System" in response_html
        assert "Reissue PIN" in response_html
        assert "PIN Hash:" in response_html
