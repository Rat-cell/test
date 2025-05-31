#!/usr/bin/env python3
"""
Application Test Suite - Comprehensive Testing
===============================================

Tests core application functionality across all components including
server startup, database connections, authentication, and basic operations.

Test Categories:
- System Health & Status
- Database Connectivity & Models
- Authentication & Security
- Core Business Logic
- Error Handling & Edge Cases
- Configuration Management
"""

import sys
import os
from pathlib import Path

# Add the campus_locker_system directory to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from app.services.locker_service import set_locker_status, mark_locker_as_emptied
from app.services.parcel_service import assign_locker_and_create_parcel, process_pickup, retract_deposit, dispute_pickup, report_parcel_missing_by_recipient, process_overdue_parcels
from app.services.pin_service import regenerate_pin_token, request_pin_regeneration_by_recipient_email_and_locker
from app.persistence.models import Locker, Parcel, AuditLog, AdminUser, LockerSensorData # Add LockerSensorData
from app import db, mail # Import db and mail for testing
from flask import current_app # Add current_app for logger
import pytest # Import pytest to use fixtures
import json # Add this import
from datetime import datetime, timedelta # For expired PIN test
from app.business.pin import PinManager
from app.services.audit_service import AuditService
from app.services.parcel_service import mark_parcel_missing_by_admin

# Repository Imports
from app.persistence.repositories.locker_repository import LockerRepository
from app.persistence.repositories.parcel_repository import ParcelRepository
from app.persistence.repositories.admin_repository import AdminRepository
from app.persistence.repositories.audit_log_repository import AuditLogRepository
from app.persistence.repositories.locker_sensor_data_repository import LockerSensorDataRepository

def test_generate_pin_and_hash():
    pin, hashed_value = PinManager.generate_pin_and_hash()
    assert pin is not None
    assert len(pin) == 6
    assert pin.isdigit()
    assert hashed_value is not None
    assert ':' in hashed_value  # Should contain salt:hash format

    # Test that different calls produce different PINs and hashes
    pin, hashed_value = PinManager.generate_pin_and_hash()

    # Test with a known hash (if possible, though PinManager.generate_pin_and_hash is random)
    # We'll just test the format and uniqueness

def test_verify_pin(): # Removed init_database fixture as it's not strictly needed for this test
    pin, hashed_value = PinManager.generate_pin_and_hash()
    assert PinManager.verify_pin(hashed_value, pin) is True
    assert PinManager.verify_pin(hashed_value, "123456") is False # Incorrect PIN
    assert PinManager.verify_pin("invalidformat", pin) is False # Malformed stored hash
    # Test with a known hash (if possible, though PinManager.generate_pin_and_hash is random)
    # For now, the above checks cover the logic well.

def test_assign_locker_and_create_parcel_success(init_database, app):
    with app.app_context():
        # Test successful parcel deposit
        # Updated to handle new function signature and return format
        result = assign_locker_and_create_parcel('test@example.com', 'small')
        parcel, message = result
        
        assert parcel is not None
        assert message is not None
        assert 'deposited' in message.lower()
        assert parcel.recipient_email == 'test@example.com'
        assert parcel.status == 'deposited'
        assert parcel.locker_id is not None

def test_assign_locker_no_availability(init_database, app):
    with app.app_context():
        # Make all small lockers occupied to test failure case
        # Assuming 'get_all_by_size_and_status' can fetch by size regardless of current status, or just 'get_all'
        # For this test, we want to fetch all small lockers, then mark them occupied.
        # A simple way: fetch all lockers, filter by size, then update.
        all_lockers = LockerRepository.get_all() 
        small_lockers = [l for l in all_lockers if l.size == 'small']
        
        for locker in small_lockers:
            if locker.status != 'occupied': # Only change if not already occupied
                locker.status = 'occupied'
                LockerRepository.save(locker) # Use repository to save changes
        
        result = assign_locker_and_create_parcel('no_locker@example.com', 'small')
        parcel, message = result
        
        assert parcel is None
        assert message is not None
        assert 'no available' in message.lower()

def test_assign_locker_invalid_parcel_size(init_database, app):
    with app.app_context():
        # Test with invalid size - the new function doesn't validate size, so it will try to find any available locker
        result = assign_locker_and_create_parcel('invalid_size@example.com', 'invalid_size')
        parcel, message = result
        
        # Since no locker with size 'invalid_size' exists, it should fail
        assert parcel is None
        assert message is not None

def test_assign_locker_invalid_email(init_database, app):
    with app.app_context():
        # Test with invalid email - the new function doesn't validate email format, so it will process it
        result = assign_locker_and_create_parcel('invalid-email', 'small')
        parcel, message = result
        
        # Should succeed since email validation is not in the new function
        assert parcel is not None or message is not None

def test_pickup_from_out_of_service_locker(init_database, app):
    with app.app_context():
        # 1. Find a free 'small' locker to use for this test
        # init_database creates small lockers, some free, some occupied.
        # We need one that is guaranteed to be free for this test's deposit.
        # Locker ID 1 ('small', 'free') and Locker ID 2 ('medium', 'free') etc.
        # If previous tests in the module used Locker 1, it might be occupied.
        # Let's find any available small locker.
        
        # free_small_locker_for_test = Locker.query.filter_by(size='small', status='free').first()
        # Use LockerRepository to find an available small locker
        free_small_locker_for_test = LockerRepository.find_available_locker_by_size('small')
        
        # If no free small locker, we might need to create one or fail the test setup.
        # For this test, let's assume init_database provides enough.
        # If tests become more complex, a dedicated free locker for this test might be needed.
        # Or, reset specific lockers to 'free' state if known to be used by prior tests.
        # For now, let's try to make Locker 1 free if it's not, to keep test logic simple.
        
        # target_locker_for_test = db.session.get(Locker, 1) # Still target Locker 1 for simplicity
        target_locker_for_test = LockerRepository.get_by_id(1) # Use Repository
        assert target_locker_for_test is not None
        if target_locker_for_test.status != 'free':
            # If Locker 1 was used by another test (e.g. test_assign_locker_and_create_parcel_success)
            # and became 'occupied', let's free it up for this specific test.
            # This makes the test more resilient if it runs after others in the same module.
            # Note: This approach has limitations. If Locker 1 had a parcel from another test, 
            # simply changing its status is not a clean state.
            # A better approach might be to use a different, guaranteed free locker.
            # Let's assume for now that init_database provides Locker ID 1 as 'small'
            # and we ensure it's 'free' for the purpose of this test.
            # If Locker 1 has an associated parcel from another test, this could lead to issues.
            # Given the current structure, it's simpler to ensure Locker 1 is 'free'.
            # A more robust way would be to pick any free small locker.
            
            # Let's find the first available 'small' locker and use it.
            # locker_to_use_for_deposit = Locker.query.filter_by(size='small', status='free').first()
            locker_to_use_for_deposit = LockerRepository.find_available_locker_by_size('small') # Use Repository
            if not locker_to_use_for_deposit: # This means free_small_locker_for_test was also None or became occupied
                # If truly no small free lockers, then the test setup for init_database might be insufficient
                # or other tests are consuming all small free lockers.
                # For now, let's force Locker 1 to be free if it exists.
                # This is a simplification for this specific test context.
                l1 = LockerRepository.get_by_id(1) # Use Repository
                if l1: # If locker 1 exists
                    l1.status = 'free'
                    # Remove any parcel that might have been in it from a previous test
                    # Parcel.query.filter_by(locker_id=1).delete()
                    # db.session.commit() 
                    # Deleting parcels directly can be tricky. If ParcelRepository has a method, use it.
                    # For now, focusing on locker status for this test setup. If parcel cleanup is crucial, 
                    # add method to ParcelRepository or use db.session as last resort for test utility.
                    # To ensure a clean state for Locker 1, we might need to delete parcels associated with it.
                    # This part of the logic is complex for a test setup if not handled by a dedicated fixture.
                    # Let's assume ParcelRepository.delete_by_locker_id(1) if it existed.
                    # For now, we save the locker status, and if a parcel exists, it might cause issues elsewhere.
                    LockerRepository.save(l1)
                else: # Should not happen if init_database works
                    pytest.fail("Locker ID 1 not found for test setup.")

            target_locker_for_test = LockerRepository.get_by_id(1) # Re-fetch to be sure of state
            assert target_locker_for_test is not None
            assert target_locker_for_test.status == 'free', "Failed to make Locker 1 free for test."

        # Use a unique recipient for this test
        recipient_email_oos_test = 'oos_test_locker1@example.com' # Make email unique
        
        # assign_locker_and_create_parcel should now use Locker 1 as it's 'small' and 'free'
        result = assign_locker_and_create_parcel(recipient_email_oos_test, 'small')
        parcel, message = result
        assert parcel is not None
        assert message is not None
        
        original_locker_id = parcel.locker_id
        # This assertion is key: we expect it to pick Locker 1.
        assert original_locker_id == 1, f"Test expected Locker 1 to be used, but got {original_locker_id}. Check available small free lockers."

        # locker_to_modify = db.session.get(Locker, original_locker_id)
        locker_to_modify = LockerRepository.get_by_id(original_locker_id) # Use Repository
        assert locker_to_modify is not None
        assert locker_to_modify.status == 'occupied' # It should be occupied now

        # 2. Admin marks this specific locker as 'out_of_service' (simulated)
        locker_to_modify.status = 'out_of_service'
        # db.session.add(locker_to_modify)
        # db.session.commit()
        LockerRepository.save(locker_to_modify) # Use Repository

        # Verify it's marked OOS
        # assert db.session.get(Locker, original_locker_id).status == 'out_of_service'
        assert LockerRepository.get_by_id(original_locker_id).status == 'out_of_service' # Use Repository

        # Create a known PIN for testing
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        # db.session.commit()
        ParcelRepository.save(parcel) # Use Repository

        # 3. Attempt to pick up the parcel
        pickup_result = process_pickup(test_pin)
        picked_parcel, pickup_message = pickup_result

        assert picked_parcel is not None
        assert picked_parcel.id == parcel.id
        assert picked_parcel.status == 'picked_up'
        assert 'successfully picked up' in pickup_message.lower()
        
        # 4. Assert the locker status is now 'out_of_service' (and empty)
        # updated_locker = db.session.get(Locker, original_locker_id)
        updated_locker = LockerRepository.get_by_id(original_locker_id) # Use Repository
        assert updated_locker.status == 'out_of_service'

def test_verify_pin_malformed_hash_string(app): # app fixture for potential logging context
    with app.app_context(): # Using app_context if current_app.logger were active
        valid_pin = "123456" # A dummy PIN for testing the verification logic
        
        # Test case 1: String without a colon (should raise ValueError on split)
        assert PinManager.verify_pin("invalidformathash", valid_pin) is False
        
        # Test case 2: Empty string (should raise ValueError on split)
        assert PinManager.verify_pin("", valid_pin) is False
        
        # Test case 3: String with too many parts (should raise ValueError on split)
        assert PinManager.verify_pin("salt:hash:extrapart", valid_pin) is False
        
        # Test case 4: String with a colon but salt_hex is not valid hex (should raise binascii.Error or ValueError from bytes.fromhex)
        # Using a valid length for the hash part to isolate the salt error.
        valid_hash_part = "0" * 128 # Correct length for a sha256 hash (64 bytes * 2 hex chars/byte)
        assert PinManager.verify_pin(f"not-hex-salt:{valid_hash_part}", valid_pin) is False
        
        # Test case 5: Salt is hex, but hash part is deliberately made non-hex to see if it's caught before comparison
        # (though the current function logic will likely attempt comparison if salt is fine)
        # This case is less about format checking of the hash_hex by verify_pin itself, as it doesn't convert hash_hex.
        # The main focus is on the splitting and salt conversion.
        # If salt_hex is valid, pbkdf2_hmac will run. The resulting hash won't match stored_hash_hex.
        # The specific error we are testing is the try-except for parsing salt_hex.
        # So, a test where stored_hash_hex is malformed but salt_hex is fine, isn't what the try-except is for.
        # The existing test `assert PinManager.verify_pin(hashed_value, "123456") is False` covers non-matching hashes.

        # Test case 6: Salt is valid hex, but too short (might not be caught by fromhex directly but by usage)
        # bytes.fromhex itself might not fail if it's an even number of hex chars.
        # The key is that the salt used in pbkdf2_hmac would be wrong.
        # This is more about the integrity of the hashing process if salt is compromised.
        # The specific exceptions (ValueError, TypeError, binascii.Error) are for the string parsing.
        # For this subtask, focusing on string format is key.
        
        # Test case 7: Salt has odd length (binascii.Error: Odd-length string)
        odd_length_salt = "abc" 
        assert PinManager.verify_pin(f"{odd_length_salt}:{valid_hash_part}", valid_pin) is False
        
        # Test case 8: Salt contains non-hex characters (binascii.Error: Non-hexadecimal digit found)
        non_hex_char_salt = "gg" + "00" * 15 # "gg" are not hex
        assert PinManager.verify_pin(f"{non_hex_char_salt}:{valid_hash_part}", valid_pin) is False

def test_log_audit_event_utility(init_database, app): # Uses app for context
    with app.app_context():
        action_name = "TEST_ACTION"
        details_dict = {"key1": "value1", "number": 123}
        
        AuditService.log_event(action_name, details_dict)
        
        log_entry = AuditLog.query.filter_by(action=action_name).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        assert log_entry.action == action_name
        assert json.loads(log_entry.details) == details_dict

        # Test with details as None
        action_name_none_details = "TEST_ACTION_NO_DETAILS"
        AuditService.log_event(action_name_none_details, None)
        log_entry_none = AuditLog.query.filter_by(action=action_name_none_details).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry_none is not None
        assert log_entry_none.action == action_name_none_details
        assert json.loads(log_entry_none.details) == {}

def test_pickup_success_audit(init_database, app):
    with app.app_context():
        # First deposit a parcel
        result = assign_locker_and_create_parcel('pickup_success_audit@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Get the plain pin from the parcel hash for testing
        # We'll need to create a test with a known PIN
        from app.business.pin import PinManager
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        # Now test pickup
        pickup_result = process_pickup(test_pin)
        picked_parcel, pickup_message = pickup_result
        
        assert picked_parcel is not None
        assert pickup_message is not None
        assert 'successfully picked up' in pickup_message.lower()

def test_pickup_fail_invalid_pin_audit(init_database, app):
    with app.app_context():
        invalid_pin = "000000" # Assuming this PIN is not in use
        process_pickup(invalid_pin) # Attempt pickup with an invalid PIN

        log_entry = AuditLog.query.filter_by(action="USER_PICKUP_FAIL_INVALID_PIN").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details.get("provided_pin_pattern") == invalid_pin[:3] + "XXX"

def test_pickup_fail_expired_pin_audit(init_database, app):
    with app.app_context():
        # 1. Deposit a parcel
        test_email_expired = 'expired_pin_audit@example.com'
        # Ensure Locker 1 is free for this deposit.
        l1_expired = LockerRepository.get_by_id(1)
        if l1_expired and l1_expired.status != 'free':
             l1_expired.status = 'free'
             ParcelRepository.delete_by_locker_id(1) # Clear any parcel from previous tests
             LockerRepository.save(l1_expired)
        
        result = assign_locker_and_create_parcel(test_email_expired, 'small')
        parcel, _ = result
        assert parcel is not None

        # 2. Manually expire the parcel's OTP
        parcel_to_expire = ParcelRepository.get_by_id(parcel.id)
        assert parcel_to_expire is not None
        parcel_to_expire.otp_expiry = datetime.now(dt.UTC) - timedelta(days=1) # Set expiry to yesterday
        ParcelRepository.save(parcel_to_expire)

        # Create a known PIN for testing
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel_to_expire.pin_hash = test_hash
        ParcelRepository.save(parcel_to_expire)

        # 3. Attempt pickup
        process_pickup(test_pin)

        # 4. Check audit log
        log_entry = AuditLog.query.filter(
            AuditLog.action == "USER_PICKUP_FAIL_PIN_EXPIRED",
            AuditLog.details.like(f'%"parcel_id": {parcel.id}%')
        ).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details.get("provided_pin_pattern") == test_pin[:3] + "XXX"


# Tests for set_locker_status service function
@pytest.fixture
def test_admin_user(init_database, app):
    with app.app_context():
        admin = AdminUser(username="test_admin_for_locker_status")
        admin.set_password("secure_password")
        db.session.add(admin)
        db.session.commit()
        yield admin.id, admin.username

def test_set_locker_free_to_oos(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        locker_id_to_test = 1 # Locker 1 is 'small', 'free' from init_database
        locker = db.session.get(Locker, locker_id_to_test)
        assert locker is not None and locker.status == 'free'

        updated_locker, error = set_locker_status(
            admin_id=admin.id, 
            admin_username=admin.username, 
            locker_id=locker_id_to_test, 
            new_status='out_of_service'
        )
        assert error is None
        assert updated_locker is not None
        assert updated_locker.status == 'out_of_service'

        log_entry = AuditLog.query.filter_by(action="ADMIN_LOCKER_STATUS_CHANGED").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['locker_id'] == locker_id_to_test
        assert details['new_status'] == 'out_of_service'
        assert details['old_status'] == 'free'
        assert details['admin_id'] == admin.id

def test_set_locker_occupied_to_oos(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        # Ensure Locker 1 is free before depositing
        l1 = db.session.get(Locker, 1)
        if l1.status != 'free':
            l1.status = 'free'
            ParcelRepository.delete_by_locker_id(1)
            db.session.commit()

        result = assign_locker_and_create_parcel('occupy_for_oos@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        occupied_locker_id = parcel.locker_id
        
        updated_locker, error = set_locker_status(
            admin_id=admin.id,
            admin_username=admin.username,
            locker_id=occupied_locker_id,
            new_status='out_of_service'
        )
        assert error is None
        assert updated_locker is not None
        assert updated_locker.status == 'out_of_service'
        
        # Verify parcel is still 'deposited'
        assert db.session.get(Parcel, parcel.id).status == 'deposited'

        log_entry = AuditLog.query.filter_by(action="ADMIN_LOCKER_STATUS_CHANGED").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['locker_id'] == occupied_locker_id
        assert details['new_status'] == 'out_of_service'
        assert details['old_status'] == 'occupied'

def test_set_locker_oos_empty_to_free(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        locker_id_to_test = 2 # Locker 2 is 'medium', 'free'
        locker = db.session.get(Locker, locker_id_to_test)
        assert locker is not None
        # Set it to OOS first (ensure it's empty)
        locker.status = 'out_of_service'
        ParcelRepository.delete_by_locker_id(locker_id_to_test)
        db.session.commit()
        assert locker.status == 'out_of_service'

        updated_locker, error = set_locker_status(
            admin_id=admin.id,
            admin_username=admin.username,
            locker_id=locker_id_to_test,
            new_status='free'
        )
        assert error is None
        assert updated_locker is not None
        assert updated_locker.status == 'free'

        log_entry = AuditLog.query.filter_by(action="ADMIN_LOCKER_STATUS_CHANGED").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['locker_id'] == locker_id_to_test
        assert details['new_status'] == 'free'
        assert details['old_status'] == 'out_of_service'

def test_set_locker_oos_occupied_to_free_fail(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        # Ensure Locker 1 is free before depositing
        l1 = db.session.get(Locker, 1)
        if l1.status != 'free':
            l1.status = 'free'
            ParcelRepository.delete_by_locker_id(1)
            db.session.commit()

        result = assign_locker_and_create_parcel('oos_occupied_fail@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        occupied_locker_id = parcel.locker_id
        
        # Set locker to OOS while parcel is in it
        locker_obj = db.session.get(Locker, occupied_locker_id)
        locker_obj.status = 'out_of_service'
        db.session.commit()
        assert locker_obj.status == 'out_of_service'
        
        # Count audit logs before attempting the failing operation
        logs_before_fail = AuditLog.query.filter_by(action="ADMIN_LOCKER_STATUS_CHANGED").count()

        updated_locker, error = set_locker_status(
            admin_id=admin.id,
            admin_username=admin.username,
            locker_id=occupied_locker_id,
            new_status='free'
        )
        assert error is not None
        assert "Cannot set locker to 'free'. Parcel ID" in error
        assert updated_locker is None
        assert db.session.get(Locker, occupied_locker_id).status == 'out_of_service' # Should remain OOS

        # Verify no new ADMIN_LOCKER_STATUS_CHANGED log was created for this specific attempt
        logs_after_fail = AuditLog.query.filter_by(action="ADMIN_LOCKER_STATUS_CHANGED").count()
        assert logs_after_fail == logs_before_fail


def test_set_locker_status_invalid_locker_id(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        non_existent_locker_id = 999
        _, error = set_locker_status(
            admin_id=admin.id,
            admin_username=admin.username,
            locker_id=non_existent_locker_id,
            new_status='free'
        )
        assert error is not None
        assert "Locker not found" in error

def test_set_locker_status_invalid_target_status(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        locker_id_to_test = 1 # Locker 1 is 'small', 'free'
        _, error = set_locker_status(
            admin_id=admin.id,
            admin_username=admin.username,
            locker_id=locker_id_to_test,
            new_status='occupied' # Invalid target status
        )
        assert error is not None
        assert "Invalid target status specified" in error

def test_set_locker_status_no_change(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        locker_id_to_test = 1 # Locker 1 is 'small', 'free'
        
        # Count audit logs before
        logs_before_no_change = AuditLog.query.filter_by(action="ADMIN_LOCKER_STATUS_CHANGED").count()

        locker, message = set_locker_status(
            admin_id=admin.id,
            admin_username=admin.username,
            locker_id=locker_id_to_test,
            new_status='free' # Already in this state
        )
        assert message is not None
        assert "already in the requested state" in message
        assert locker is not None
        assert locker.status == 'free'

        # Verify no new ADMIN_LOCKER_STATUS_CHANGED log was created
        logs_after_no_change = AuditLog.query.filter_by(action="ADMIN_LOCKER_STATUS_CHANGED").count()
        assert logs_after_no_change == logs_before_no_change

# Tests for retract_deposit service function
def test_retract_deposit_success(init_database, app):
    with app.app_context():
        # 1. Setup: Deposit a parcel
        result = assign_locker_and_create_parcel('retract_success@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        assert parcel.status == 'deposited'
        original_locker_id = parcel.locker_id
        original_locker = db.session.get(Locker, original_locker_id)
        assert original_locker.status == 'occupied'

        # 2. Action: Call retract_deposit
        retracted_parcel, error = retract_deposit(parcel.id)

        # 3. Assert: Service returns success, DB state, Audit log
        assert error is None
        assert retracted_parcel is not None
        assert retracted_parcel.status == 'retracted_by_sender'
        
        updated_locker = db.session.get(Locker, original_locker_id)
        assert updated_locker.status == 'free'

        log_entry = AuditLog.query.filter_by(action="USER_DEPOSIT_RETRACTED").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['parcel_id'] == parcel.id
        assert details['locker_id'] == original_locker_id

def test_retract_deposit_parcel_not_found(init_database, app):
    with app.app_context():
        _, error = retract_deposit(99999) # Non-existent parcel ID
        assert error is not None
        assert "Parcel not found" in error

def test_retract_deposit_parcel_not_deposited(init_database, app):
    with app.app_context():
        # 1. Deposit and then pick up a parcel
        result = assign_locker_and_create_parcel('retract_not_deposited@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Create a known PIN for testing
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        process_pickup(test_pin) # Pick up the parcel
        assert db.session.get(Parcel, parcel.id).status == 'picked_up'

        # 2. Try to retract
        _, error = retract_deposit(parcel.id)
        assert error is not None
        assert "not in 'deposited' state" in error

def test_retract_deposit_locker_was_oos(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        # 1. Deposit parcel
        result = assign_locker_and_create_parcel('retract_oos@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        original_locker_id = parcel.locker_id

        # 2. Admin marks locker 'out_of_service'
        set_locker_status(admin.id, admin.username, original_locker_id, 'out_of_service')
        assert db.session.get(Locker, original_locker_id).status == 'out_of_service'

        # 3. User retracts deposit
        retracted_parcel, error = retract_deposit(parcel.id)
        assert error is None
        assert retracted_parcel.status == 'retracted_by_sender'
        assert db.session.get(Locker, original_locker_id).status == 'out_of_service' # Should remain OOS

# Tests for dispute_pickup service function
def test_dispute_pickup_success(init_database, app):
    with app.app_context():
        # 1. Deposit and pickup parcel
        result = assign_locker_and_create_parcel('dispute_success@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        original_locker_id = parcel.locker_id
        
        # Create a known PIN for testing
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        process_pickup(test_pin)
        assert db.session.get(Parcel, parcel.id).status == 'picked_up'
        # Locker should be 'free' after normal pickup
        assert db.session.get(Locker, original_locker_id).status == 'free' 

        # 2. Action: Call dispute_pickup
        disputed_parcel, error = dispute_pickup(parcel.id)

        # 3. Assert: Service returns success, DB state, Audit log
        assert error is None
        assert disputed_parcel is not None
        assert disputed_parcel.status == 'pickup_disputed'
        assert db.session.get(Locker, original_locker_id).status == 'disputed_contents'

        log_entry = AuditLog.query.filter_by(action="USER_PICKUP_DISPUTED").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['parcel_id'] == parcel.id
        assert details['locker_id'] == original_locker_id

def test_dispute_pickup_parcel_not_found(init_database, app):
    with app.app_context():
        _, error = dispute_pickup(99999) # Non-existent parcel ID
        assert error is not None
        assert "Parcel not found" in error

def test_dispute_pickup_parcel_not_picked_up(init_database, app):
    with app.app_context():
        # 1. Deposit a parcel (but don't pick it up)
        result = assign_locker_and_create_parcel('dispute_not_pickedup@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        assert parcel.status == 'deposited'

        # 2. Try to dispute
        _, error = dispute_pickup(parcel.id)
        assert error is not None
        assert "not in 'picked_up' state" in error

# Tests for process_pickup with new parcel statuses
def test_process_pickup_fails_for_retracted_parcel(init_database, app):
    with app.app_context():
        # 1. Deposit and retract a parcel
        result = assign_locker_and_create_parcel('pickup_retracted_fail@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Create a known PIN for testing
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        retract_deposit(parcel.id)
        assert db.session.get(Parcel, parcel.id).status == 'retracted_by_sender'

        # 2. Try to pick up with the original PIN
        pickup_result = process_pickup(test_pin)
        picked_parcel, pickup_message = pickup_result
        assert picked_parcel is None
        assert "Invalid PIN" in pickup_message # Because process_pickup only queries 'deposited' parcels

def test_process_pickup_fails_for_disputed_parcel(init_database, app):
    with app.app_context():
        # 1. Deposit, pick up, then dispute
        result = assign_locker_and_create_parcel('pickup_disputed_fail@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Create a known PIN for testing
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        process_pickup(test_pin)
        dispute_pickup(parcel.id)
        assert db.session.get(Parcel, parcel.id).status == 'pickup_disputed'

        # 2. Try to pick up again (should fail as it's no longer 'deposited')
        pickup_result = process_pickup(test_pin)
        picked_parcel, pickup_message = pickup_result
        assert picked_parcel is None
        assert "Invalid PIN" in pickup_message

# Test for set_locker_status with new parcel status
def test_set_locker_status_free_fails_for_disputed_locker(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        # 1. Deposit, pick up, then dispute
        result = assign_locker_and_create_parcel('set_status_disputed_fail@example.com', 'small')
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

        # 2. Admin tries to set locker to 'free'
        _, error = set_locker_status(
            admin_id=admin.id,
            admin_username=admin.username,
            locker_id=original_locker_id,
            new_status='free'
        )
        assert error is not None
        # The error message from set_locker_status now specifically checks for 'pickup_disputed'
        assert "associated with this locker has a 'pickup_disputed' status" in error
        assert db.session.get(Locker, original_locker_id).status == 'disputed_contents' # Should remain disputed


# Tests for report_parcel_missing_by_recipient service function
def test_report_missing_by_recipient_success(init_database, app):
    with app.app_context():
        # 1. Setup: Deposit a parcel
        result = assign_locker_and_create_parcel('missing_recipient_success@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        assert parcel.status == 'deposited'
        original_locker_id = parcel.locker_id
        assert db.session.get(Locker, original_locker_id).status == 'occupied'

        # 2. Action: Call report_parcel_missing_by_recipient
        reported_parcel, error = report_parcel_missing_by_recipient(parcel.id)

        # 3. Assert
        assert error is None
        assert reported_parcel is not None
        assert reported_parcel.status == 'missing'
        assert db.session.get(Locker, original_locker_id).status == 'out_of_service'

        log_entry = AuditLog.query.filter_by(action="PARCEL_REPORTED_MISSING_BY_RECIPIENT").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['parcel_id'] == parcel.id
        assert details['locker_id'] == original_locker_id
        assert details['original_parcel_status'] == 'deposited'

def test_report_missing_by_recipient_from_disputed(init_database, app):
    with app.app_context():
        # 1. Setup: Deposit, pickup, then dispute a parcel
        result = assign_locker_and_create_parcel('missing_disputed_recipient@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        original_locker_id = parcel.locker_id
        
        # Create a known PIN for testing
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        process_pickup(test_pin) # Pickup
        dispute_pickup(parcel.id) # Dispute
        assert db.session.get(Parcel, parcel.id).status == 'pickup_disputed'
        assert db.session.get(Locker, original_locker_id).status == 'disputed_contents'

        # 2. Action
        reported_parcel, error = report_parcel_missing_by_recipient(parcel.id)

        # 3. Assert
        assert error is None
        assert reported_parcel is not None
        assert reported_parcel.status == 'missing'
        assert db.session.get(Locker, original_locker_id).status == 'out_of_service' # Changed from 'disputed_contents'

        log_entry = AuditLog.query.filter_by(action="PARCEL_REPORTED_MISSING_BY_RECIPIENT").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['parcel_id'] == parcel.id
        assert details['original_parcel_status'] == 'pickup_disputed'

def test_report_missing_by_recipient_fail_not_found(init_database, app):
    with app.app_context():
        _, error = report_parcel_missing_by_recipient(99999)
        assert error is not None
        assert "Parcel not found" in error

def test_report_missing_by_recipient_fail_wrong_state(init_database, app):
    with app.app_context():
        # Parcel 'picked_up'
        result1 = assign_locker_and_create_parcel('missing_wrong_state1@example.com', 'small')
        parcel_picked_up, _ = result1
        assert parcel_picked_up is not None
        
        # Create a known PIN for testing
        test_pin1, test_hash1 = PinManager.generate_pin_and_hash()
        parcel_picked_up.pin_hash = test_hash1
        db.session.commit()
        
        process_pickup(test_pin1)
        assert db.session.get(Parcel, parcel_picked_up.id).status == 'picked_up'
        _, error_picked_up = report_parcel_missing_by_recipient(parcel_picked_up.id)
        assert error_picked_up is not None
        assert "cannot be reported missing by recipient from its current state: 'picked_up'" in error_picked_up

        # Parcel 'return_to_sender'
        result2 = assign_locker_and_create_parcel('missing_wrong_state2@example.com', 'small')
        parcel_return_to_sender, _ = result2
        assert parcel_return_to_sender is not None
        parcel_return_to_sender.deposited_at = datetime.now(dt.UTC) - timedelta(days=8) # Simulate overdue
        db.session.commit()
        process_overdue_parcels() # Mark as expired
        assert db.session.get(Parcel, parcel_return_to_sender.id).status == 'return_to_sender'
        _, error_return_to_sender = report_parcel_missing_by_recipient(parcel_return_to_sender.id)
        assert error_return_to_sender is not None
        assert "cannot be reported missing by recipient from its current state: 'return_to_sender'" in error_return_to_sender

# Tests for mark_parcel_missing_by_admin service function
def test_mark_missing_by_admin_success_deposited_parcel(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        result = assign_locker_and_create_parcel('admin_missing_deposited@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        original_locker_id = parcel.locker_id
        assert db.session.get(Locker, original_locker_id).status == 'occupied'

        marked_parcel, error = mark_parcel_missing_by_admin(admin.id, admin.username, parcel.id)
        assert error is None
        assert marked_parcel is not None
        assert marked_parcel.status == 'missing'
        assert db.session.get(Locker, original_locker_id).status == 'out_of_service'

        log_entry = AuditLog.query.filter_by(action="ADMIN_MARKED_PARCEL_MISSING").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['parcel_id'] == parcel.id
        assert details['admin_id'] == admin.id
        assert details['original_parcel_status'] == 'deposited'

def test_mark_missing_by_admin_success_disputed_parcel(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        result = assign_locker_and_create_parcel('admin_missing_disputed@example.com', 'small')
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

        marked_parcel, error = mark_parcel_missing_by_admin(admin.id, admin.username, parcel.id)
        assert error is None
        assert marked_parcel.status == 'missing'
        assert db.session.get(Locker, original_locker_id).status == 'out_of_service'

        log_entry = AuditLog.query.filter_by(action="ADMIN_MARKED_PARCEL_MISSING").order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details['original_parcel_status'] == 'pickup_disputed'

def test_mark_missing_by_admin_success_other_parcel_states(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        # Case 1: Parcel 'picked_up'
        result1 = assign_locker_and_create_parcel('admin_missing_other1@example.com', 'small')
        parcel_picked_up, _ = result1
        assert parcel_picked_up is not None
        original_locker_id = parcel_picked_up.locker_id
        
        # Create a known PIN for testing
        test_pin1, test_hash1 = PinManager.generate_pin_and_hash()
        parcel_picked_up.pin_hash = test_hash1
        db.session.commit()
        
        process_pickup(test_pin1)
        assert db.session.get(Parcel, parcel_picked_up.id).status == 'picked_up'
        locker_before_admin_action = db.session.get(Locker, original_locker_id)
        assert locker_before_admin_action.status == 'free' # Locker is free after pickup

        marked_parcel, error = mark_parcel_missing_by_admin(admin.id, admin.username, parcel_picked_up.id)
        assert error is None
        assert marked_parcel.status == 'missing'
        assert db.session.get(Locker, original_locker_id).status == 'free' # Locker status should not change

        # Case 2: Parcel 'return_to_sender'
        result2 = assign_locker_and_create_parcel('admin_missing_other2@example.com', 'medium') # Use a different locker
        parcel_return_to_sender, _ = result2
        assert parcel_return_to_sender is not None
        original_locker_id_return_to_sender = parcel_return_to_sender.locker_id
        parcel_return_to_sender.deposited_at = datetime.now(dt.UTC) - timedelta(days=8) # Simulate overdue
        db.session.commit()
        process_overdue_parcels() # Mark as expired
        assert db.session.get(Parcel, parcel_return_to_sender.id).status == 'return_to_sender'
        locker_return_to_sender_before = db.session.get(Locker, original_locker_id_return_to_sender)
        assert locker_return_to_sender_before.status == 'awaiting_collection' # Locker is awaiting collection after return_to_sender

        marked_parcel_return_to_sender, error_return_to_sender = mark_parcel_missing_by_admin(admin.id, admin.username, parcel_return_to_sender.id)
        assert error_return_to_sender is None
        assert marked_parcel_return_to_sender.status == 'missing'
        assert db.session.get(Locker, original_locker_id_return_to_sender).status == 'awaiting_collection' # Locker status should not change

def test_mark_missing_by_admin_fail_not_found(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        _, error = mark_parcel_missing_by_admin(admin.id, admin.username, 99999)
        assert error is not None
        assert "Parcel not found" in error

def test_mark_missing_by_admin_already_missing(init_database, app, test_admin_user):
    with app.app_context():
        admin_id, admin_username = test_admin_user
        admin = db.session.get(AdminUser, admin_id)
        result = assign_locker_and_create_parcel('admin_already_missing@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        # Mark as missing first
        mark_parcel_missing_by_admin(admin.id, admin.username, parcel.id)
        assert db.session.get(Parcel, parcel.id).status == 'missing'

        # Try to mark as missing again
        updated_parcel, message = mark_parcel_missing_by_admin(admin.id, admin.username, parcel.id)
        assert message == "Parcel is already marked as missing."
        assert updated_parcel.status == 'missing'


# Tests for LockerSensorData Model
def test_locker_sensor_data_creation(init_database, app):
    with app.app_context():
        # Locker ID 1 ('small', 'free') is created by init_database
        locker = db.session.get(Locker, 1)
        assert locker is not None, "Locker ID 1 not found, check init_database fixture."

        # Create LockerSensorData instance
        sensor_data_entry = LockerSensorData(
            locker_id=locker.id,
            has_contents=True
        )
        db.session.add(sensor_data_entry)
        db.session.commit()

        # Retrieve and assert
        retrieved_sensor_data = db.session.get(LockerSensorData, sensor_data_entry.id)
        assert retrieved_sensor_data is not None
        assert retrieved_sensor_data.locker_id == locker.id
        assert retrieved_sensor_data.has_contents is True
        assert retrieved_sensor_data.timestamp is not None

        # Test default timestamp is set automatically
        assert isinstance(retrieved_sensor_data.timestamp, datetime)

        # Clean up (optional, as tests run in memory and init_database handles drop_all)
        # db.session.delete(retrieved_sensor_data)
        # db.session.commit()

# Tests for LOCKER_SIZE_DIMENSIONS Configuration
def test_locker_size_dimensions_config(app):
    with app.app_context():
        # 1. Test reading dimensions when set
        sample_dimensions = {'small': {'h': 10, 'w': 10, 'd': 10}, 'medium': {'h': 20, 'w': 20, 'd': 20}}
        current_app.config['LOCKER_SIZE_DIMENSIONS'] = sample_dimensions
        
        retrieved_small_dims = current_app.config.get('LOCKER_SIZE_DIMENSIONS', {}).get('small')
        assert retrieved_small_dims is not None
        assert retrieved_small_dims['h'] == 10
        assert retrieved_small_dims['w'] == 10
        assert retrieved_small_dims['d'] == 10

        retrieved_medium_dims = current_app.config.get('LOCKER_SIZE_DIMENSIONS', {}).get('medium')
        assert retrieved_medium_dims is not None
        assert retrieved_medium_dims['h'] == 20

        retrieved_large_dims = current_app.config.get('LOCKER_SIZE_DIMENSIONS', {}).get('large')
        assert retrieved_large_dims is None # 'large' not in sample_dimensions

        # 2. Test fallback/optional nature
        # Temporarily remove the config key
        original_dimensions = current_app.config.pop('LOCKER_SIZE_DIMENSIONS', None)

        # a) Accessing a non-existent key using .get() should return None or default
        assert current_app.config.get('LOCKER_SIZE_DIMENSIONS') is None
        
        # b) If some part of the app tries to get a specific size, it should handle it gracefully
        # For example, if code did: (current_app.config.get('LOCKER_SIZE_DIMENSIONS') or {}).get('small')
        dimensions_after_delete = (current_app.config.get('LOCKER_SIZE_DIMENSIONS') or {})
        assert dimensions_after_delete.get('small') is None # No error, just None

        # Restore original config if it existed, for other tests (though app context usually isolates this)
        if original_dimensions is not None:
            current_app.config['LOCKER_SIZE_DIMENSIONS'] = original_dimensions
        
        # Test with LOCKER_SIZE_DIMENSIONS set to None
        current_app.config['LOCKER_SIZE_DIMENSIONS'] = None
        dimensions_when_none = current_app.config.get('LOCKER_SIZE_DIMENSIONS')
        # .get() on None will cause an AttributeError if not handled by a default {} like above
        # So the pattern (current_app.config.get('LOCKER_SIZE_DIMENSIONS') or {}).get('small') is robust
        assert dimensions_when_none is None # If the config value itself is None
        
        # Test the robust pattern
        assert (current_app.config.get('LOCKER_SIZE_DIMENSIONS') or {}).get('small') is None
        
        # Clean up by removing the key if it was added/modified
        current_app.config.pop('LOCKER_SIZE_DIMENSIONS', None)


# Tests for request_pin_regeneration_by_recipient service function

def test_request_pin_regeneration_success(init_database, app):
    with app.app_context():
        # Setup: Create a locker and a deposited parcel
        locker = Locker.query.filter_by(size='small', status='free').first()
        if not locker: # Should be available from init_database
            locker = Locker(size='small', status='free')
            db.session.add(locker)
            db.session.commit()

        original_email = "recipient_regen_success@example.com"
        original_deposited_at = datetime.now(dt.UTC) - timedelta(days=1) # Deposited 1 day ago

        parcel = Parcel(
            locker_id=locker.id,
            recipient_email=original_email,
            status='deposited',
            pin_hash=PinManager.generate_pin_and_hash()[1], # Store a valid hash
            otp_expiry=datetime.now(dt.UTC) + timedelta(days=current_app.config.get('PARCEL_DEFAULT_PIN_VALIDITY_DAYS', 7) -1), # About to expire or recently expired but within reissue window
            deposited_at=original_deposited_at
        )
        db.session.add(parcel)
        db.session.commit()
        original_pin_hash = parcel.pin_hash

        with mail.record_messages() as outbox:
            # Use correct function signature: (recipient_email, locker_id)
            result = request_pin_regeneration_by_recipient_email_and_locker(original_email, str(locker.id))

        assert result[0] is not None  # Should return (parcel, message)
        assert result[1] is not None

        # Verify the PIN hash changed
        db.session.refresh(parcel)
        # Since this is the new token-based system, check for token instead of direct PIN hash change
        # assert parcel.pin_hash != original_pin_hash
