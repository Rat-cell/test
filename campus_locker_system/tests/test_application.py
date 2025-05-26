from app.application.services import assign_locker_and_create_parcel, generate_pin_and_hash, verify_pin, process_pickup, log_audit_event
from app.persistence.models import Locker, Parcel, AuditLog # Add AuditLog
from app import db # Import db for direct session manipulation if needed
from flask import current_app # Add current_app for logger
import pytest # Import pytest to use fixtures
import json # Add this import
from datetime import datetime, timedelta # For expired PIN test

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
        
        test_email = 'test_deposit_audit@example.com'
        parcel, pin, error = assign_locker_and_create_parcel('small', test_email)

        assert error is None
        assert parcel is not None
        assert parcel.id is not None
        assert parcel.recipient_email == test_email # Use the variable
        assert parcel.status == 'deposited'
        assert pin is not None
        assert len(pin) == 6

        assigned_locker = db.session.get(Locker, parcel.locker_id)
        assert assigned_locker is not None
        assert assigned_locker.status == 'occupied'
        assert assigned_locker.size == 'small'
        # Ensure it's the same locker that was initially free
        assert assigned_locker.id == initial_free_small_locker.id

        # Check for USER_DEPOSIT_INITIATED
        init_log = AuditLog.query.filter(AuditLog.action == "USER_DEPOSIT_INITIATED").order_by(AuditLog.timestamp.desc()).first()
        assert init_log is not None
        init_details = json.loads(init_log.details)
        assert init_details.get("recipient_email") == test_email
        assert init_details.get("parcel_size_requested") == 'small'

        # Check for USER_DEPOSIT_SUCCESS
        success_log = AuditLog.query.filter(AuditLog.action == "USER_DEPOSIT_SUCCESS", AuditLog.details.like(f'%"parcel_id": {parcel.id}%')).first()
        assert success_log is not None
        success_details = json.loads(success_log.details)
        assert success_details.get("locker_id") == assigned_locker.id
        assert success_details.get("recipient_email") == test_email

        # Check for either EMAIL_NOTIFICATION_SENT or EMAIL_NOTIFICATION_FAIL
        email_audit_log = AuditLog.query.filter(
            AuditLog.details.like(f'%"parcel_id": {parcel.id}%')
        ).filter(
            db.or_(
                AuditLog.action == "EMAIL_NOTIFICATION_SENT",
                AuditLog.action == "EMAIL_NOTIFICATION_FAIL"
            )
        ).order_by(AuditLog.timestamp.desc()).first()

        assert email_audit_log is not None, "No email notification audit log (SENT or FAIL) found for the parcel."
        
        email_details = json.loads(email_audit_log.details)
        assert email_details.get("parcel_id") == parcel.id
        assert email_details.get("recipient_email") == test_email # Use the variable

        # Optionally, if the email failed, you could check if the error detail is present
        if email_audit_log.action == "EMAIL_NOTIFICATION_FAIL":
            assert "error" in email_details # Or a more specific check if possible
            current_app.logger.warning(f"Test captured an EMAIL_NOTIFICATION_FAIL event: {email_details.get('error')}")
        else: # EMAIL_NOTIFICATION_SENT
            # No specific extra check needed here unless there are success-specific details
            pass

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

def test_assign_locker_invalid_parcel_size(app): # Added app fixture
    with app.app_context(): # Context for consistency
        parcel, pin, error = assign_locker_and_create_parcel('xlarge', 'test@example.com')
        assert parcel is None
        assert pin is None
        assert error == "Invalid parcel size. Allowed sizes are 'small', 'medium', 'large'."

        parcel, pin, error = assign_locker_and_create_parcel('', 'test@example.com') # Test empty size
        assert parcel is None
        assert pin is None
        assert error == "Invalid parcel size. Allowed sizes are 'small', 'medium', 'large'."

def test_assign_locker_invalid_email(app): # Added app fixture
    with app.app_context():
        # Test empty email
        parcel, pin, error = assign_locker_and_create_parcel('small', '')
        assert parcel is None
        assert pin is None
        assert error == "Invalid recipient email. Please provide a valid email address."

        # Test email without @
        parcel, pin, error = assign_locker_and_create_parcel('small', 'testexample.com')
        assert parcel is None
        assert pin is None
        assert error == "Invalid recipient email. Please provide a valid email address."

        # Test email too long
        long_email = 'a' * 250 + '@example.com' # 250 + 1 + 11 = 262, which is > 254
        parcel, pin, error = assign_locker_and_create_parcel('small', long_email)
        assert parcel is None
        assert pin is None
        assert error == "Invalid recipient email. Please provide a valid email address."

def test_pickup_from_out_of_service_locker(init_database, app):
    with app.app_context():
        # 1. Find a free 'small' locker to use for this test
        # init_database creates small lockers, some free, some occupied.
        # We need one that is guaranteed to be free for this test's deposit.
        # Locker ID 1 ('small', 'free') and Locker ID 2 ('medium', 'free') etc.
        # If previous tests in the module used Locker 1, it might be occupied.
        # Let's find any available small locker.
        
        free_small_locker_for_test = Locker.query.filter_by(size='small', status='free').first()
        
        # If no free small locker, we might need to create one or fail the test setup.
        # For this test, let's assume init_database provides enough.
        # If tests become more complex, a dedicated free locker for this test might be needed.
        # Or, reset specific lockers to 'free' state if known to be used by prior tests.
        # For now, let's try to make Locker 1 free if it's not, to keep test logic simple.
        
        target_locker_for_test = db.session.get(Locker, 1) # Still target Locker 1 for simplicity
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
            locker_to_use_for_deposit = Locker.query.filter_by(size='small', status='free').first()
            if not locker_to_use_for_deposit:
                # If truly no small free lockers, then the test setup for init_database might be insufficient
                # or other tests are consuming all small free lockers.
                # For now, let's force Locker 1 to be free if it exists.
                # This is a simplification for this specific test context.
                l1 = db.session.get(Locker, 1)
                if l1: # If locker 1 exists
                    l1.status = 'free'
                    # Remove any parcel that might have been in it from a previous test
                    Parcel.query.filter_by(locker_id=1).delete()
                    db.session.commit()
                else: # Should not happen if init_database works
                    pytest.fail("Locker ID 1 not found for test setup.")

            assert db.session.get(Locker, 1).status == 'free', "Failed to make Locker 1 free for test."

        # Use a unique recipient for this test
        recipient_email_oos_test = 'oos_test_locker1@example.com' # Make email unique
        
        # assign_locker_and_create_parcel should now use Locker 1 as it's 'small' and 'free'
        parcel, plain_pin, error = assign_locker_and_create_parcel('small', recipient_email_oos_test)
        assert error is None
        assert parcel is not None
        assert plain_pin is not None
        
        original_locker_id = parcel.locker_id
        # This assertion is key: we expect it to pick Locker 1.
        assert original_locker_id == 1, f"Test expected Locker 1 to be used, but got {original_locker_id}. Check available small free lockers."

        locker_to_modify = db.session.get(Locker, original_locker_id)
        assert locker_to_modify is not None
        assert locker_to_modify.status == 'occupied' # It should be occupied now

        # 2. Admin marks this specific locker as 'out_of_service' (simulated)
        locker_to_modify.status = 'out_of_service'
        db.session.add(locker_to_modify)
        db.session.commit()

        # Verify it's marked OOS
        assert db.session.get(Locker, original_locker_id).status == 'out_of_service'

        # 3. Attempt to pick up the parcel
        picked_parcel, result_locker, pickup_error = process_pickup(plain_pin)

        assert pickup_error is None
        assert picked_parcel is not None
        assert picked_parcel.id == parcel.id
        assert picked_parcel.status == 'picked_up'
        
        # 4. Assert the locker status is now 'out_of_service' (and empty)
        assert result_locker is not None
        assert result_locker.id == original_locker_id
        assert result_locker.status == 'out_of_service'

def test_verify_pin_malformed_hash_string(app): # app fixture for potential logging context
    with app.app_context(): # Using app_context if current_app.logger were active
        valid_pin = "123456" # A dummy PIN for testing the verification logic
        
        # Test case 1: String without a colon (should raise ValueError on split)
        assert verify_pin("invalidformathash", valid_pin) is False
        
        # Test case 2: Empty string (should raise ValueError on split)
        assert verify_pin("", valid_pin) is False
        
        # Test case 3: String with too many parts (should raise ValueError on split)
        assert verify_pin("salt:hash:extrapart", valid_pin) is False
        
        # Test case 4: String with a colon but salt_hex is not valid hex (should raise binascii.Error or ValueError from bytes.fromhex)
        # Using a valid length for the hash part to isolate the salt error.
        valid_hash_part = "0" * 128 # Correct length for a sha256 hash (64 bytes * 2 hex chars/byte)
        assert verify_pin(f"not-hex-salt:{valid_hash_part}", valid_pin) is False
        
        # Test case 5: Salt is hex, but hash part is deliberately made non-hex to see if it's caught before comparison
        # (though the current function logic will likely attempt comparison if salt is fine)
        # This case is less about format checking of the hash_hex by verify_pin itself, as it doesn't convert hash_hex.
        # The main focus is on the splitting and salt conversion.
        # If salt_hex is valid, pbkdf2_hmac will run. The resulting hash won't match stored_hash_hex.
        # The specific error we are testing is the try-except for parsing salt_hex.
        # So, a test where stored_hash_hex is malformed but salt_hex is fine, isn't what the try-except is for.
        # The existing test `assert verify_pin(hashed_value, "123456") is False` covers non-matching hashes.

        # Test case 6: Salt is valid hex, but too short (might not be caught by fromhex directly but by usage)
        # bytes.fromhex itself might not fail if it's an even number of hex chars.
        # The key is that the salt used in pbkdf2_hmac would be wrong.
        # This is more about the integrity of the hashing process if salt is compromised.
        # The specific exceptions (ValueError, TypeError, binascii.Error) are for the string parsing.
        # For this subtask, focusing on string format is key.
        
        # Test case 7: Salt has odd length (binascii.Error: Odd-length string)
        odd_length_salt = "abc" 
        assert verify_pin(f"{odd_length_salt}:{valid_hash_part}", valid_pin) is False
        
        # Test case 8: Salt contains non-hex characters (binascii.Error: Non-hexadecimal digit found)
        non_hex_char_salt = "gg" + "00" * 15 # "gg" are not hex
        assert verify_pin(f"{non_hex_char_salt}:{valid_hash_part}", valid_pin) is False

def test_log_audit_event_utility(init_database, app): # Uses app for context
    with app.app_context():
        action_name = "TEST_ACTION"
        details_dict = {"key1": "value1", "number": 123}
        
        log_audit_event(action_name, details_dict)
        
        log_entry = AuditLog.query.filter_by(action=action_name).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        assert log_entry.action == action_name
        assert json.loads(log_entry.details) == details_dict

        # Test with details as None
        action_name_none_details = "TEST_ACTION_NO_DETAILS"
        log_audit_event(action_name_none_details, None)
        log_entry_none = AuditLog.query.filter_by(action=action_name_none_details).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry_none is not None
        assert log_entry_none.action == action_name_none_details
        assert json.loads(log_entry_none.details) == {}

def test_pickup_success_audit(init_database, app):
    with app.app_context():
        # 1. Deposit a parcel to get a PIN and an occupied locker
        test_email_pickup_success = 'pickup_success_audit@example.com'
        # Ensure a free small locker is available (Locker ID 1 should be free by init_database or made free by previous tests)
        l1 = db.session.get(Locker, 1)
        if l1 and l1.status != 'free': # If used by test_assign_locker_and_create_parcel_success
            l1.status = 'free'
            Parcel.query.filter_by(locker_id=1).delete()
            db.session.commit()
        
        parcel, plain_pin, error = assign_locker_and_create_parcel('small', test_email_pickup_success)
        assert error is None and parcel is not None and plain_pin is not None
        original_locker_id = parcel.locker_id
        
        # 2. Process pickup
        picked_parcel, result_locker, pickup_error = process_pickup(plain_pin)
        assert pickup_error is None
        assert picked_parcel is not None

        # 3. Check audit logs
        init_log = AuditLog.query.filter(
            AuditLog.action == "USER_PICKUP_INITIATED", 
            AuditLog.details.like(f'%"{plain_pin[:3]}XXX"%') # Check for masked PIN
        ).order_by(AuditLog.timestamp.desc()).first()
        assert init_log is not None

        success_log = AuditLog.query.filter(
            AuditLog.action == "USER_PICKUP_SUCCESS",
            AuditLog.details.like(f'%"parcel_id": {picked_parcel.id}%')
        ).order_by(AuditLog.timestamp.desc()).first()
        assert success_log is not None
        success_details = json.loads(success_log.details)
        assert success_details.get("locker_id") == original_locker_id

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
        l1_expired = db.session.get(Locker, 1)
        if l1_expired and l1_expired.status != 'free':
             l1_expired.status = 'free'
             Parcel.query.filter_by(locker_id=1).delete() # Clear any parcel from previous tests
             db.session.commit()
        
        parcel, plain_pin, error = assign_locker_and_create_parcel('small', test_email_expired)
        assert error is None and parcel is not None

        # 2. Manually expire the parcel's OTP
        parcel_to_expire = db.session.get(Parcel, parcel.id)
        assert parcel_to_expire is not None
        parcel_to_expire.otp_expiry = datetime.utcnow() - timedelta(days=1) # Set expiry to yesterday
        db.session.add(parcel_to_expire)
        db.session.commit()

        # 3. Attempt pickup
        process_pickup(plain_pin)

        # 4. Check audit log
        log_entry = AuditLog.query.filter(
            AuditLog.action == "USER_PICKUP_FAIL_PIN_EXPIRED",
            AuditLog.details.like(f'%"parcel_id": {parcel.id}%')
        ).order_by(AuditLog.timestamp.desc()).first()
        assert log_entry is not None
        details = json.loads(log_entry.details)
        assert details.get("provided_pin_pattern") == plain_pin[:3] + "XXX"
