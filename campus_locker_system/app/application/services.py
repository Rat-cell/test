import hashlib
import os
from datetime import datetime, timedelta
from flask import current_app # Add current_app
from flask_mail import Message # Add Message
from app import db, mail # Add mail instance
from app.persistence.models import Locker, Parcel, AdminUser, AuditLog # Assuming models are in persistence.models
import binascii # Add this import
import json # Add this import

def generate_pin_and_hash():
    pin = "{:06d}".format(int.from_bytes(os.urandom(3), 'big') % 1000000) # Generate 6-digit PIN
    salt = os.urandom(16)
    hashed_pin = hashlib.pbkdf2_hmac('sha256', pin.encode('utf-8'), salt, 100000, dklen=64)
    return pin, salt.hex() + ":" + hashed_pin.hex()

def verify_pin(stored_pin_hash_with_salt, provided_pin):
    try:
        salt_hex, stored_hash_hex = stored_pin_hash_with_salt.split(':')
        salt = bytes.fromhex(salt_hex)
    except (ValueError, TypeError, binascii.Error) as e:
        # Log this error for diagnostics if needed
        # current_app.logger.warning(f"Malformed pin_hash_with_salt encountered: {e}")
        return False # Malformed stored hash or salt

    # Hash the provided PIN using the extracted salt
    # Ensure dklen matches what was used in generate_pin_and_hash (e.g., 64)
    hashed_provided_pin = hashlib.pbkdf2_hmac(
        'sha256',
        provided_pin.encode('utf-8'),
        salt,
        100000,
        dklen=64 
    )
    return hashed_provided_pin.hex() == stored_hash_hex

def assign_locker_and_create_parcel(parcel_size: str, recipient_email: str):
    log_audit_event("USER_DEPOSIT_INITIATED", {
        "parcel_size_requested": parcel_size, 
        "recipient_email": recipient_email
    })

    ALLOWED_PARCEL_SIZES = ['small', 'medium', 'large']
    if parcel_size not in ALLOWED_PARCEL_SIZES:
        reason = "Invalid parcel size. Allowed sizes are 'small', 'medium', 'large'."
        log_audit_event("USER_DEPOSIT_FAIL", {
            "parcel_size_requested": parcel_size,
            "recipient_email": recipient_email,
            "reason": reason
        })
        return None, None, reason

    MAX_EMAIL_LENGTH = 254
    if not recipient_email or '@' not in recipient_email or len(recipient_email) > MAX_EMAIL_LENGTH:
        reason = "Invalid recipient email. Please provide a valid email address."
        log_audit_event("USER_DEPOSIT_FAIL", {
            "parcel_size_requested": parcel_size,
            "recipient_email": recipient_email,
            "reason": reason
        })
        return None, None, reason

    try:
        # Find Locker (FR-01)
        locker = Locker.query.filter_by(size=parcel_size, status='free').first()

        if not locker:
            reason = "No available locker of the specified size."
            log_audit_event("USER_DEPOSIT_FAIL", {
                "parcel_size_requested": parcel_size,
                "recipient_email": recipient_email,
                "reason": reason
            })
            return None, None, reason

        # Generate PIN (FR-02)
        plain_pin, hashed_pin_with_salt = generate_pin_and_hash()

        # Create Parcel Record
        new_parcel = Parcel(
            locker_id=locker.id,
            pin_hash=hashed_pin_with_salt,
            otp_expiry=datetime.utcnow() + timedelta(hours=24), # OTP expiry 24h
            recipient_email=recipient_email,
            status='deposited'
        )
        db.session.add(new_parcel)

        # Update Locker Status
        locker.status = 'occupied'
        db.session.add(locker)

        # Commit Changes
        db.session.commit()

        log_audit_event("USER_DEPOSIT_SUCCESS", {
            "parcel_id": new_parcel.id,
            "locker_id": locker.id, 
            "recipient_email": new_parcel.recipient_email,
            "pin_generated": True 
        })

        # Send email notification (FR-03)
        msg = Message( # Define msg before try block so it's available in except
            subject="Your Campus Locker PIN",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[recipient_email]
        )
        msg.body = f"Hello,\n\nYour parcel has been deposited.\nLocker ID: {locker.id}\nYour PIN: {plain_pin}\n\nThis PIN will expire in 24 hours.\n\nThank you."
        try:
            mail.send(msg)
            log_audit_event("EMAIL_NOTIFICATION_SENT", {
                "recipient_email": recipient_email,
                "subject": msg.subject, 
                "parcel_id": new_parcel.id 
            })
        except Exception as e:
            current_app.logger.error(f"Failed to send PIN email to {recipient_email}: {e}")
            log_audit_event("EMAIL_NOTIFICATION_FAIL", {
                "recipient_email": recipient_email,
                "subject": msg.subject, 
                "parcel_id": new_parcel.id,
                "error": str(e) 
            })
            # Optionally, flash a message to the sender that email failed if this is critical feedback

        return new_parcel, plain_pin, None  # Success
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in assign_locker_and_create_parcel: {e}") # Use current_app.logger
        log_audit_event("USER_DEPOSIT_FAIL", {
            "parcel_size_requested": parcel_size,
            "recipient_email": recipient_email,
            "reason": f"Error processing request: {str(e)}"
        })
        return None, None, "Error processing request."

def process_pickup(provided_pin: str) -> tuple[Parcel | None, Locker | None, str | None]:
    pin_pattern = provided_pin[:3] + "XXX" if provided_pin and len(provided_pin) == 6 else "INVALID_PIN_FORMAT"
    log_audit_event("USER_PICKUP_INITIATED", {"provided_pin_pattern": pin_pattern})
    
    try:
        # Iterate through all Parcel records with status='deposited'
        deposited_parcels = Parcel.query.filter_by(status='deposited').all()

        current_parcel = None
        for parcel_attempt in deposited_parcels:
            if verify_pin(parcel_attempt.pin_hash, provided_pin):
                current_parcel = parcel_attempt
                break
        
        if not current_parcel:
            log_audit_event("USER_PICKUP_FAIL_INVALID_PIN", {"provided_pin_pattern": pin_pattern})
            return None, None, "Invalid PIN."

        # Check if PIN has expired
        if current_parcel.otp_expiry < datetime.utcnow():
            current_parcel.status = 'expired'
            db.session.add(current_parcel)
            db.session.commit()
            log_audit_event("USER_PICKUP_FAIL_PIN_EXPIRED", {
                "parcel_id": current_parcel.id, 
                "provided_pin_pattern": pin_pattern 
            })
            return None, None, "PIN has expired."

        # PIN is valid and not expired
        
        locker = db.session.get(Locker, current_parcel.locker_id)
        if not locker:
            # This should ideally not happen if data is consistent
            db.session.rollback()
            current_app.logger.error(f"Consistency error: Locker ID {current_parcel.locker_id} not found for parcel {current_parcel.id}")
            return None, None, "Error processing request due to data inconsistency."

        # Check if the locker was marked 'out_of_service' by an admin while this parcel was in it.
        # A locker containing a parcel should normally be 'occupied'.
        # If it's 'out_of_service', it means an admin overrode its status.
        locker_was_out_of_service_while_occupied = (locker.status == 'out_of_service')

        current_parcel.status = 'picked_up'
        db.session.add(current_parcel) # Add to session before commit

        if locker_was_out_of_service_while_occupied:
            locker.status = 'out_of_service' # It was OOS with a parcel, now it's OOS and empty
        else:
            locker.status = 'free' # It was 'occupied', now it's free and empty
        
        db.session.add(locker) # Add to session before commit
        db.session.commit()
        
        log_audit_event("USER_PICKUP_SUCCESS", {
            "parcel_id": current_parcel.id,
            "locker_id": locker.id 
        })
        return current_parcel, locker, None  # Success

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in process_pickup: {e}") # Use current_app.logger
        log_audit_event("USER_PICKUP_FAIL", { # Using USER_PICKUP_FAIL as per refined instruction
            "provided_pin_pattern": pin_pattern,
            "reason": f"System error during pickup: {str(e)}"
        })
        return None, None, "Error processing pickup request."

def verify_admin_credentials(username, password) -> AdminUser | None:
    admin_user = AdminUser.query.filter_by(username=username).first()
    if admin_user and admin_user.check_password(password):
        return admin_user
    return None

# Potentially other service functions will be added here later

def log_audit_event(action: str, details: dict = None):
    """
    Logs an audit event to the AuditLog table.
    :param action: The action string (e.g., 'USER_DEPOSIT_SUCCESS').
    :param details: A dictionary of details to be stored as a JSON string.
    """
    if details is None:
        details_to_store = {}
    else:
        details_to_store = details

    try:
        json_details = json.dumps(details_to_store)
    except TypeError as e:
        current_app.logger.error(f"AUDIT LOGGING ERROR: Could not serialize details to JSON for action '{action}'. Details: {details_to_store}. Error: {e}")
        # Optionally, log a placeholder indicating serialization failure
        json_details = json.dumps({"error": "Failed to serialize audit details.", "original_action": action})


    audit_log_entry = AuditLog(
        action=action,
        details=json_details
        # timestamp is defaulted in model
    )

    try:
        db.session.add(audit_log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"AUDIT LOGGING ERROR: Failed to save audit log for action '{action}'. Details: {json_details}. Error: {e}")

def set_locker_status(admin_id: int, admin_username: str, locker_id: int, new_status: str) -> tuple[Locker | None, str | None]:
    if new_status not in ['out_of_service', 'free']:
        return None, "Invalid target status specified. Allowed: 'out_of_service', 'free'."

    locker = db.session.get(Locker, locker_id)
    if not locker:
        return None, "Locker not found."

    old_status = locker.status

    if old_status == new_status:
        return locker, "Locker is already in the requested state." # No error, but no change

    try:
        if new_status == 'out_of_service':
            locker.status = 'out_of_service'
        elif new_status == 'free':
            if old_status != 'out_of_service':
                # This also implicitly handles if it was 'occupied' and not 'out_of_service'
                return None, "Locker must currently be 'out_of_service' to be set to 'free'."
            
            # Check if any parcel is currently 'deposited' in this locker
            active_parcel = Parcel.query.filter_by(locker_id=locker_id, status='deposited').first()
            if active_parcel:
                return None, f"Cannot set locker to 'free'. Parcel ID {active_parcel.id} is still marked as 'deposited' in this locker."
            locker.status = 'free'
        # No 'else' needed due to initial new_status validation

        db.session.add(locker) # Good practice to add, even if just modifying
        db.session.commit()

        log_audit_event("ADMIN_LOCKER_STATUS_CHANGED", details={
            "admin_id": admin_id,
            "admin_username": admin_username,
            "locker_id": locker_id,
            "old_status": old_status,
            "new_status": new_status
        })
        return locker, None
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in set_locker_status for locker {locker_id}: {e}")
        return None, "A database error occurred while updating locker status."
