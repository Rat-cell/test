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
            # deposited_at will be set by default in model
            otp_expiry=datetime.utcnow() + timedelta(days=current_app.config.get('PARCEL_DEFAULT_PIN_VALIDITY_DAYS', 7)),
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

        # FR-03: Send email notification with PIN upon successful parcel deposit.
        # Send email notification (FR-03)
        msg = Message( # Define msg before try block so it's available in except
            subject="Your Campus Locker PIN",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[recipient_email]
        )
        msg.body = f"Hello,\n\nYour parcel has been deposited.\nLocker ID: {locker.id}\nYour PIN: {plain_pin}\n\nThis PIN will expire in {current_app.config.get('PARCEL_DEFAULT_PIN_VALIDITY_DAYS', 7)} days.\n\nThank you."
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

            # NEW CHECK: Check if any parcel associated with this locker is in 'pickup_disputed' status
            disputed_parcel = Parcel.query.filter_by(locker_id=locker_id, status='pickup_disputed').first()
            if disputed_parcel:
                return None, f"Cannot set locker to 'free'. Parcel ID {disputed_parcel.id} associated with this locker has a 'pickup_disputed' status. Please resolve the dispute."
            
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

def retract_deposit(parcel_id: int) -> tuple[Parcel | None, str | None]:
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return None, "Parcel not found."

        if parcel.status != 'deposited':
            return None, f"Parcel is not in 'deposited' state (current status: {parcel.status}). Cannot retract."

        locker = db.session.get(Locker, parcel.locker_id)
        if not locker:
            # Should not happen if data is consistent
            current_app.logger.error(f"Data inconsistency: Locker ID {parcel.locker_id} not found for parcel {parcel.id} during retraction.")
            return None, "Associated locker not found. Data inconsistency."
        
        original_locker_status = locker.status # e.g. 'occupied' or 'out_of_service' (if admin changed it)

        parcel.status = 'retracted_by_sender'
        
        if original_locker_status == 'occupied':
            locker.status = 'free'
        elif original_locker_status == 'out_of_service':
            # It was OOS with this parcel in it, now it's OOS and empty.
            locker.status = 'out_of_service' 
        else:
            # Unexpected locker state, log and potentially error or default to 'free'/'OOS'
            current_app.logger.warning(f"Locker {locker.id} had unexpected status '{original_locker_status}' during deposit retraction for parcel {parcel.id}. Setting to 'free'.")
            locker.status = 'free'


        db.session.add(parcel)
        db.session.add(locker)
        db.session.commit()

        log_audit_event("USER_DEPOSIT_RETRACTED", details={
            "parcel_id": parcel.id,
            "locker_id": locker.id,
            "reason": "Sender indicated mistake"
        })
        return parcel, None
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in retract_deposit for parcel {parcel_id}: {e}")
        return None, "A database error occurred while retracting deposit."

def dispute_pickup(parcel_id: int) -> tuple[Parcel | None, str | None]:
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return None, "Parcel not found."

        # Typically, a pickup would have just happened, so status would be 'picked_up'.
        # Allow dispute even if admin manually changed it, as long as it's not 'deposited'.
        if parcel.status != 'picked_up':
             return None, f"Parcel is not in 'picked_up' state (current status: {parcel.status}). Cannot dispute."

        locker = db.session.get(Locker, parcel.locker_id)
        if not locker:
            current_app.logger.error(f"Data inconsistency: Locker ID {parcel.locker_id} not found for parcel {parcel.id} during pickup dispute.")
            return None, "Associated locker not found. Data inconsistency."
        
        # The locker would have been set to 'free' or 'out_of_service' (if it was OOS before pickup).
        # Now it becomes 'disputed_contents'.
        # original_locker_status_after_pickup = locker.status 

        parcel.status = 'pickup_disputed'
        locker.status = 'disputed_contents' # New specific status for admin attention

        db.session.add(parcel)
        db.session.add(locker)
        db.session.commit()

        log_audit_event("USER_PICKUP_DISPUTED", details={
            "parcel_id": parcel.id,
            "locker_id": locker.id,
            "reason": "Recipient indicated issue post-pickup"
        })
        return parcel, None
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in dispute_pickup for parcel {parcel_id}: {e}")
        return None, "A database error occurred while disputing pickup."

def report_parcel_missing_by_recipient(parcel_id: int) -> tuple[Parcel | None, str | None]:
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return None, "Parcel not found."

        # Validate current parcel status - typically should be 'deposited' 
        # if a recipient is at the locker having just opened it.
        # Could also allow for 'pickup_disputed' to be escalated to 'missing'.
        if parcel.status not in ['deposited', 'pickup_disputed']:
            return None, f"Parcel cannot be reported missing by recipient from its current state: '{parcel.status}'."

        original_parcel_status = parcel.status
        parcel.status = 'missing'
        
        locker = db.session.get(Locker, parcel.locker_id)
        if not locker:
            current_app.logger.error(f"Data inconsistency: Locker ID {parcel.locker_id} not found for parcel {parcel.id} during recipient missing report.")
            # Proceed to mark parcel missing, but log locker issue.
        else:
            # If locker was 'occupied' (by this parcel) or 'disputed_contents' (due to this parcel),
            # it should now be taken out of service for admin check.
            if locker.status in ['occupied', 'disputed_contents']:
                 locker.status = 'out_of_service'
                 db.session.add(locker)

        db.session.add(parcel)
        db.session.commit()

        log_audit_event("PARCEL_REPORTED_MISSING_BY_RECIPIENT", details={
            "parcel_id": parcel.id,
            "locker_id": parcel.locker_id,
            "original_parcel_status": original_parcel_status,
            "reported_via": "API/LockerClient" 
        })
        return parcel, None
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in report_parcel_missing_by_recipient for parcel {parcel_id}: {e}")
        return None, "A database error occurred while reporting parcel missing."

def mark_parcel_missing_by_admin(admin_id: int, admin_username: str, parcel_id: int) -> tuple[Parcel | None, str | None]:
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return None, "Parcel not found."

        if parcel.status == 'missing':
            return parcel, "Parcel is already marked as missing." # No error, but no change

        original_parcel_status = parcel.status
        parcel.status = 'missing'
        db.session.add(parcel)

        # If the parcel was 'deposited' or 'pickup_disputed', its locker might need attention.
        if original_parcel_status in ['deposited', 'pickup_disputed']:
            locker = db.session.get(Locker, parcel.locker_id)
            if locker:
                # If locker was 'occupied' by this parcel or 'disputed_contents' because of it,
                # take it out of service.
                if locker.status in ['occupied', 'disputed_contents']:
                    locker.status = 'out_of_service'
                    db.session.add(locker)
            else:
                current_app.logger.warning(f"Locker ID {parcel.locker_id} not found for parcel {parcel.id} being marked missing by admin.")
        
        db.session.commit()

        log_audit_event("ADMIN_MARKED_PARCEL_MISSING", details={
            "admin_id": admin_id,
            "admin_username": admin_username,
            "parcel_id": parcel.id,
            "locker_id": parcel.locker_id, # Log current locker_id, even if it might be None for some old parcels
            "original_parcel_status": original_parcel_status
        })
        return parcel, None
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in mark_parcel_missing_by_admin for parcel {parcel_id}: {e}")
        return None, "A database error occurred while marking parcel missing."

def reissue_pin(parcel_id: int) -> tuple[Parcel | None, str | None]:
    # FR-05: Part of PIN recovery process (admin path).
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            log_audit_event("PIN_REISSUE_FAIL", {"parcel_id": parcel_id, "reason": "Parcel not found."})
            return None, "Parcel not found."

        if parcel.status != 'deposited':
            log_audit_event("PIN_REISSUE_FAIL", {
                "parcel_id": parcel_id, 
                "current_status": parcel.status,
                "reason": "PIN can only be reissued for deposited parcels."
            })
            return None, "PIN can only be reissued for deposited parcels."

        max_reissue_days = current_app.config.get('PARCEL_MAX_PIN_REISSUE_DAYS', 7)
        if parcel.deposited_at + timedelta(days=max_reissue_days) < datetime.utcnow():
            log_audit_event("PIN_REISSUE_FAIL", {
                "parcel_id": parcel_id,
                "deposited_at": parcel.deposited_at.isoformat(),
                "max_reissue_days": max_reissue_days,
                "reason": "PIN reissue period has expired."
            })
            return None, "PIN reissue period has expired."

        plain_pin, hashed_pin_with_salt = generate_pin_and_hash()
        parcel.pin_hash = hashed_pin_with_salt
        
        pin_validity_days = current_app.config.get('PARCEL_DEFAULT_PIN_VALIDITY_DAYS', 7)
        parcel.otp_expiry = datetime.utcnow() + timedelta(days=pin_validity_days)

        db.session.add(parcel)
        db.session.commit()

        # FR-03: Send email notification with new PIN upon admin-initiated PIN reissue.
        # Send email notification
        email_subject = "Your New Campus Locker PIN"
        email_body = (
            f"Hello,\n\n"
            f"A new PIN has been issued for your parcel in Locker ID: {parcel.locker_id}.\n"
            f"Your new PIN: {plain_pin}\n\n"
            f"This PIN will expire in {pin_validity_days} days.\n\n"
            f"If you did not request this change, please contact support immediately.\n\n"
            f"Thank you."
        )
        msg = Message(
            subject=email_subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[parcel.recipient_email]
        )
        msg.body = email_body
        try:
            mail.send(msg)
            log_audit_event("EMAIL_NOTIFICATION_SENT", {
                "recipient_email": parcel.recipient_email,
                "subject": email_subject,
                "parcel_id": parcel.id,
                "reason": "PIN Reissue"
            })
        except Exception as e:
            current_app.logger.error(f"Failed to send new PIN email to {parcel.recipient_email} for parcel {parcel.id}: {e}")
            log_audit_event("EMAIL_NOTIFICATION_FAIL", {
                "recipient_email": parcel.recipient_email,
                "subject": email_subject,
                "parcel_id": parcel.id,
                "reason": "PIN Reissue",
                "error": str(e)
            })
            # Proceed with PIN reissue even if email fails, but the error message should reflect this.
            # For this subtask, the primary success is PIN reissue, email is secondary.
            # However, the problem description implies a general success message if PIN is reissued.

        log_audit_event("PIN_REISSUED_SUCCESS", {
            "parcel_id": parcel.id,
            "new_otp_expiry": parcel.otp_expiry.isoformat(),
            "pin_validity_days": pin_validity_days
        })
        return parcel, "New PIN issued and notification sent."

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in reissue_pin for parcel {parcel_id}: {e}")
        # Attempt to log failure if parcel_id is known, even if parcel object couldn't be fetched
        log_audit_event("PIN_REISSUE_FAIL", {
            "parcel_id": parcel_id,
            "reason": f"System error during PIN reissue: {str(e)}"
        })
        return None, "A system error occurred while reissuing the PIN."

def process_overdue_parcels():
    # Imports are already at the top of the file:
    # from datetime import datetime, timedelta
    # from flask import current_app
    # from app import db
    # from app.persistence.models import Parcel, Locker
    # log_audit_event is already in this file

    max_pickup_days = current_app.config.get('PARCEL_MAX_PICKUP_DAYS', 7)
    # Query for parcels that are 'deposited' and have a non-null 'deposited_at'
    deposited_parcels = Parcel.query.filter(
        Parcel.status == 'deposited',
        Parcel.deposited_at.isnot(None) 
    ).all()
    
    processed_count = 0
    items_to_update_in_session = [] # Use a different name to avoid conflict if this function is called inside another with similar var

    for parcel in deposited_parcels:
        # Ensure deposited_at is a datetime object before comparison
        if not isinstance(parcel.deposited_at, datetime):
            log_audit_event("PROCESS_OVERDUE_FAIL_INVALID_DEPOSITED_AT", {
                "parcel_id": parcel.id, 
                "deposited_at_type": str(type(parcel.deposited_at)),
                "reason": "Parcel has invalid or missing deposited_at timestamp."
            })
            continue # Skip this parcel

        if datetime.utcnow() > parcel.deposited_at + timedelta(days=max_pickup_days):
            try:
                locker = parcel.locker # Fetch associated locker via backref
                if not locker:
                    log_audit_event("PROCESS_OVERDUE_FAIL_NO_LOCKER", {
                        "parcel_id": parcel.id, 
                        "reason": "Locker not found for deposited parcel."
                    })
                    continue # Skip this parcel

                old_parcel_status = parcel.status
                old_locker_status = locker.status

                parcel.status = 'awaiting_return'
                # Regardless of previous state (occupied, out_of_service), if it has an overdue parcel,
                # it's now awaiting collection of that overdue item.
                locker.status = 'awaiting_collection'

                items_to_update_in_session.append(parcel)
                # Always add locker to session as its status is definitively changing to 'awaiting_collection'
                # unless it was already 'awaiting_collection' (which is unlikely for a 'deposited' parcel becoming overdue).
                if old_locker_status != 'awaiting_collection':
                    items_to_update_in_session.append(locker)
                
                log_audit_event("PARCEL_MARKED_OVERDUE_FOR_RETURN", {
                    "parcel_id": parcel.id,
                    "locker_id": locker.id,
                    "old_parcel_status": old_parcel_status,
                    "new_parcel_status": parcel.status, # 'awaiting_return'
                    "old_locker_status": old_locker_status,
                    "new_locker_status": locker.status, # 'awaiting_collection'
                    "max_pickup_days_configured": max_pickup_days
                })
                processed_count += 1
            except Exception as e:
                # Log error for this specific parcel.
                # For this implementation, we'll log and continue, not stopping the whole batch.
                # No rollback here means other successful changes in this loop will be part of the batch.
                current_app.logger.error(f"Error processing parcel ID {parcel.id} for overdue status: {str(e)}")
                log_audit_event("PROCESS_OVERDUE_PARCEL_ERROR", {
                    "parcel_id": parcel.id, 
                    "error": str(e),
                    "action": "Skipped this parcel, continued with batch."
                })
                # Continue to the next parcel

    if items_to_update_in_session:
        try:
            db.session.add_all(items_to_update_in_session)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error committing batch of overdue parcels: {str(e)}")
            log_audit_event("PROCESS_OVERDUE_BATCH_COMMIT_ERROR", {
                "error": str(e), 
                "num_parcels_intended_for_update_in_batch": processed_count
            })
            return 0, f"Error committing batch of overdue parcels: {str(e)}" # Return error for the batch
            
    return processed_count, f"{processed_count} overdue parcels processed."

def mark_locker_as_emptied(locker_id: int, admin_id: int, admin_username: str) -> tuple[Locker | None, str]:
    # Imports: Locker, db, log_audit_event are available at module level
    
    locker = db.session.get(Locker, locker_id)
    if not locker:
        log_audit_event("MARK_LOCKER_EMPTIED_FAIL", {"locker_id": locker_id, "admin_id": admin_id, "admin_username": admin_username, "reason": "Locker not found."})
        return None, "Locker not found."

    if locker.status != 'awaiting_collection':
        log_audit_event("MARK_LOCKER_EMPTIED_FAIL", {
            "locker_id": locker_id, 
            "admin_id": admin_id,
            "admin_username": admin_username, 
            "current_locker_status": locker.status,
            "reason": "Locker is not in 'awaiting_collection' state."
        })
        return locker, "Locker is not awaiting collection."

    old_locker_status = locker.status
    locker.status = 'free'
    
    try:
        db.session.add(locker) # Good practice to add modified object to session
        db.session.commit()
        log_audit_event("LOCKER_MARKED_EMPTIED_AFTER_RETURN", {
            "locker_id": locker_id,
            "admin_id": admin_id,
            "admin_username": admin_username,
            "old_locker_status": old_locker_status,
            "new_locker_status": locker.status # Should be 'free'
        })
        return locker, "Locker successfully marked as free."
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in mark_locker_as_emptied for locker {locker_id}: {str(e)}")
        log_audit_event("MARK_LOCKER_EMPTIED_ERROR", {
            "locker_id": locker_id, 
            "admin_id": admin_id,
            "admin_username": admin_username,
            "error": str(e)
        })
        # Returning the locker object here allows the caller to see its state before rollback, if needed,
        # though its status in the DB will be rolled back.
        return locker, f"Database error marking locker as emptied: {str(e)}"

def request_pin_regeneration_by_recipient(recipient_email_attempt: str, locker_id_attempt: int) -> bool:
    # FR-05: Implements recipient PIN recovery mechanism.
    # All necessary imports are assumed to be at the top of the file.
    # log_audit_event and generate_pin_and_hash are in this file.
    # flask.render_template is needed for email bodies
    from flask import render_template

    try:
        # Convert locker_id_attempt to integer if it's passed as string from form
        try:
            locker_id_int = int(locker_id_attempt)
        except ValueError:
            log_audit_event("RECIPIENT_PIN_REGEN_FAIL", {
                "recipient_email_attempt": recipient_email_attempt,
                "locker_id_attempt": locker_id_attempt,
                "reason": "Invalid Locker ID format."
            })
            return False

        parcel = Parcel.query.filter_by(
            recipient_email=recipient_email_attempt,
            locker_id=locker_id_int,
            status='deposited'
        ).first()

        if not parcel:
            log_audit_event("RECIPIENT_PIN_REGEN_NO_MATCH", {
                "recipient_email_attempt": recipient_email_attempt,
                "locker_id_attempt": locker_id_attempt,
                "reason": "No matching active parcel found for details provided."
            })
            return False

        max_reissue_days = current_app.config.get('PARCEL_MAX_PIN_REISSUE_DAYS', 7)
        # Ensure parcel.deposited_at is not None before comparison
        if parcel.deposited_at is None:
            log_audit_event("RECIPIENT_PIN_REGEN_FAIL", {
                "parcel_id": parcel.id,
                "recipient_email_attempt": recipient_email_attempt,
                "locker_id_attempt": locker_id_attempt,
                "reason": "Parcel has no deposit timestamp."
            })
            return False
            
        if datetime.utcnow() > parcel.deposited_at + timedelta(days=max_reissue_days):
            log_audit_event("RECIPIENT_PIN_REGEN_FAIL_TOO_LATE", {
                "parcel_id": parcel.id,
                "recipient_email_attempt": recipient_email_attempt,
                "locker_id_attempt": locker_id_attempt,
                "deposited_at": parcel.deposited_at.isoformat(),
                "max_reissue_days": max_reissue_days,
                "reason": "PIN reissue period has expired."
            })
            return False

        plain_pin, hashed_pin_with_salt = generate_pin_and_hash()
        parcel.pin_hash = hashed_pin_with_salt
        
        pin_validity_days = current_app.config.get('PARCEL_DEFAULT_PIN_VALIDITY_DAYS', 7)
        parcel.otp_expiry = datetime.utcnow() + timedelta(days=pin_validity_days)

        db.session.add(parcel)
        db.session.commit() # Commit changes to parcel (new PIN and expiry)

        # FR-03: Send email notification with new PIN upon recipient-initiated PIN regeneration.
        # Send email notification
        email_subject = "Your New Campus Locker PIN (Recipient Request)"
        email_body = (
            f"Hello,\n\n"
            f"As requested, a new PIN has been issued for your parcel in Locker ID: {parcel.locker_id}.\n"
            f"Your new PIN: {plain_pin}\n\n"
            f"This PIN will expire in {pin_validity_days} days.\n\n"
            f"If you did not request this change, please contact support immediately.\n\n"
            f"Thank you."
        )
        msg = Message(
            subject=email_subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[parcel.recipient_email] # Use email from DB
        )
        msg.body = email_body
        try:
            mail.send(msg)
            log_audit_event("RECIPIENT_PIN_REGEN_EMAIL_SENT", {
                "recipient_email": parcel.recipient_email,
                "subject": email_subject,
                "parcel_id": parcel.id
            })
        except Exception as e:
            current_app.logger.error(f"Failed to send new PIN email (recipient request) to {parcel.recipient_email} for parcel {parcel.id}: {e}")
            log_audit_event("RECIPIENT_PIN_REGEN_EMAIL_FAIL", {
                "recipient_email": parcel.recipient_email,
                "subject": email_subject,
                "parcel_id": parcel.id,
                "error": str(e)
            })
            # Even if email fails, PIN was updated, so an attempt was made.
        
        log_audit_event("RECIPIENT_PIN_REGENERATION_SUCCESS", {
            "parcel_id": parcel.id,
            "recipient_email": parcel.recipient_email,
            "locker_id": parcel.locker_id,
            "new_otp_expiry": parcel.otp_expiry.isoformat()
        })
        return True # Email dispatch was attempted

    except Exception as e:
        # This catches errors in DB commit or other unexpected issues
        db.session.rollback()
        current_app.logger.error(f"Error in request_pin_regeneration_by_recipient for email '{recipient_email_attempt}', locker '{locker_id_attempt}': {e}")
        log_audit_event("RECIPIENT_PIN_REGEN_SYSTEM_ERROR", {
            "recipient_email_attempt": recipient_email_attempt,
            "locker_id_attempt": locker_id_attempt,
            "error": str(e)
        })
        return False

def send_scheduled_reminder_notifications():
    # Imports are at the top or added in the diff block above
    # from datetime import datetime, timedelta
    # from flask import current_app, render_template
    # from app import db, mail
    # from app.persistence.models import Parcel
    # from flask_mail import Message
    # log_audit_event is already in this file

    reminder_schedule_hours = current_app.config.get('REMINDER_NOTIFICATION_SCHEDULE_HOURS', [])
    pre_return_hours = current_app.config.get('PRE_RETURN_NOTIFICATION_HOURS', 24)
    max_pickup_days = current_app.config.get('PARCEL_MAX_PICKUP_DAYS', 7)
    # pin_validity_days = current_app.config.get('PARCEL_DEFAULT_PIN_VALIDITY_DAYS', 7) # Not directly used for sending, but for context in email

    parcels_to_notify = Parcel.query.filter_by(status='deposited').all()
    
    sent_scheduled_reminders = 0
    sent_pre_return_reminders = 0
    parcels_updated_in_session = []

    now = datetime.utcnow()

    for parcel in parcels_to_notify:
        if not parcel.deposited_at:
            current_app.logger.warning(f"Parcel ID {parcel.id} has no deposited_at timestamp. Skipping reminder.")
            log_audit_event("REMINDER_SEND_FAIL", {
                "parcel_id": parcel.id, 
                "reason": "Missing deposited_at timestamp."
            })
            continue
        
        parcel_updated_this_run = False

        # --- Scheduled Reminders ---
        # Sort schedule to process earliest reminder first if multiple are due
        sorted_schedule_hours = sorted(reminder_schedule_hours) 
        for hour_offset in sorted_schedule_hours:
            reminder_time = parcel.deposited_at + timedelta(hours=hour_offset)
            
            # Check if this reminder window is active and if a reminder for this window hasn't been sent
            # A simple check: if now is past reminder_time, and last_reminder_sent_at is before this reminder_time
            if now >= reminder_time:
                if parcel.last_reminder_sent_at is None or parcel.last_reminder_sent_at < reminder_time:
                    try:
                        # Render email body
                        email_body = render_template(
                            'email/scheduled_reminder_email.txt',
                            recipient_email=parcel.recipient_email,
                            locker_id=parcel.locker_id,
                            # PIN is not included as per updated requirement
                            otp_expiry_formatted=parcel.otp_expiry.strftime('%Y-%m-%d %H:%M:%S UTC') if parcel.otp_expiry else 'N/A'
                        )
                        msg = Message(
                            subject="Reminder: Your Parcel is Waiting for Pickup at Campus Locker", # Subject from template
                            sender=current_app.config['MAIL_DEFAULT_SENDER'],
                            recipients=[parcel.recipient_email],
                            body=email_body
                        )
                        mail.send(msg)
                        
                        parcel.last_reminder_sent_at = now
                        if not parcel_updated_this_run:
                            parcels_updated_in_session.append(parcel)
                            parcel_updated_this_run = True
                        
                        sent_scheduled_reminders += 1
                        log_audit_event('SCHEDULED_REMINDER_SENT', {
                            "parcel_id": parcel.id,
                            "recipient_email": parcel.recipient_email,
                            "reminder_hour_offset": hour_offset
                        })
                        # Break after sending one scheduled reminder per parcel per run
                        # This prevents sending multiple scheduled reminders if the job runs late
                        # and crosses several hour_offset thresholds.
                        break 
                    except Exception as e:
                        current_app.logger.error(f"Failed to send scheduled reminder for parcel {parcel.id}: {e}")
                        log_audit_event('SCHEDULED_REMINDER_FAIL', {
                            "parcel_id": parcel.id,
                            "recipient_email": parcel.recipient_email,
                            "reminder_hour_offset": hour_offset,
                            "error": str(e)
                        })
                        # Potentially break here too, or try next schedule if one email server error
                        break 
            # If now < reminder_time, subsequent scheduled reminders are also not due yet.
            else:
                 break


        # --- Pre-Return Reminder ---
        max_pickup_datetime = parcel.deposited_at + timedelta(days=max_pickup_days)
        pre_return_window_start = max_pickup_datetime - timedelta(hours=pre_return_hours)

        if now >= pre_return_window_start and not parcel.pre_return_reminder_sent:
            try:
                otp_expiry_formatted_str = parcel.otp_expiry.strftime('%Y-%m-%d %H:%M:%S UTC') if parcel.otp_expiry else 'N/A'
                max_pickup_deadline_formatted_str = max_pickup_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')

                email_body_pre_return = render_template(
                    'email/pre_return_reminder_email.txt',
                    recipient_email=parcel.recipient_email,
                    locker_id=parcel.locker_id,
                    # PIN is not included
                    otp_expiry_formatted=otp_expiry_formatted_str,
                    max_pickup_deadline_formatted=max_pickup_deadline_formatted_str
                )
                msg_pre_return = Message(
                    subject="Important: Action Required - Your Parcel Pickup Deadline is Approaching", # Subject from template
                    sender=current_app.config['MAIL_DEFAULT_SENDER'],
                    recipients=[parcel.recipient_email],
                    body=email_body_pre_return
                )
                mail.send(msg_pre_return)

                parcel.pre_return_reminder_sent = True
                if not parcel_updated_this_run: # Add to list only if not already added
                    parcels_updated_in_session.append(parcel)
                    # parcel_updated_this_run = True # Not strictly needed to set here as it's the last update type for this parcel
                
                sent_pre_return_reminders += 1
                log_audit_event('PRE_RETURN_REMINDER_SENT', {
                    "parcel_id": parcel.id,
                    "recipient_email": parcel.recipient_email,
                    "max_pickup_deadline": max_pickup_datetime.isoformat()
                })
            except Exception as e:
                current_app.logger.error(f"Failed to send pre-return reminder for parcel {parcel.id}: {e}")
                log_audit_event('PRE_RETURN_REMINDER_FAIL', {
                    "parcel_id": parcel.id,
                    "recipient_email": parcel.recipient_email,
                    "error": str(e)
                })

    if parcels_updated_in_session:
        try:
            db.session.add_all(parcels_updated_in_session)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error committing reminder updates to DB: {str(e)}")
            log_audit_event("REMINDER_BATCH_COMMIT_ERROR", {
                "error": str(e),
                "num_parcels_intended_for_update": len(parcels_updated_in_session)
            })
            # Return counts of what was attempted before commit error
            return sent_scheduled_reminders, sent_pre_return_reminders, f"DB commit error. Attempted: {sent_scheduled_reminders} scheduled, {sent_pre_return_reminders} pre-return."

    summary_message = f"Scheduled reminders sent: {sent_scheduled_reminders}. Pre-return reminders sent: {sent_pre_return_reminders}."
    return sent_scheduled_reminders, sent_pre_return_reminders, summary_message
