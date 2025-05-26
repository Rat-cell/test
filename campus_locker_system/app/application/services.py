import hashlib
import os
from datetime import datetime, timedelta
from flask import current_app # Add current_app
from flask_mail import Message # Add Message
from app import db, mail # Add mail instance
from app.persistence.models import Locker, Parcel, AdminUser # Assuming models are in persistence.models

def generate_pin_and_hash():
    pin = "{:06d}".format(int.from_bytes(os.urandom(3), 'big') % 1000000) # Generate 6-digit PIN
    salt = os.urandom(16)
    hashed_pin = hashlib.pbkdf2_hmac('sha256', pin.encode('utf-8'), salt, 100000, dklen=64)
    return pin, salt.hex() + ":" + hashed_pin.hex()

def verify_pin(stored_pin_hash_with_salt, provided_pin):
    try:
        salt_hex, stored_hash_hex = stored_pin_hash_with_salt.split(':')
        salt = bytes.fromhex(salt_hex)
        hashed_provided_pin = hashlib.pbkdf2_hmac('sha256', provided_pin.encode('utf-8'), salt, 100000, dklen=64)
        return hashed_provided_pin.hex() == stored_hash_hex
    except Exception: # Handle cases like incorrect format or other errors
        return False

def assign_locker_and_create_parcel(parcel_size: str, recipient_email: str):
    try:
        # Find Locker (FR-01)
        locker = Locker.query.filter_by(size=parcel_size, status='free').first()

        if not locker:
            return None, None, "No available locker of the specified size."

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

        # Send email notification (FR-03)
        try:
            msg = Message(
                subject="Your Campus Locker PIN",
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[recipient_email]
            )
            msg.body = f"Hello,\n\nYour parcel has been deposited.\nLocker ID: {locker.id}\nYour PIN: {plain_pin}\n\nThis PIN will expire in 24 hours.\n\nThank you."
            mail.send(msg)
        except Exception as e:
            # Log email sending failure, but don't make the whole deposit fail
            current_app.logger.error(f"Failed to send PIN email to {recipient_email}: {e}")
            # Optionally, flash a message to the sender that email failed if this is critical feedback

        return new_parcel, plain_pin, None  # Success
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in assign_locker_and_create_parcel: {e}") # Use current_app.logger
        return None, None, "Error processing request."

def process_pickup(provided_pin: str) -> tuple[Parcel | None, Locker | None, str | None]:
    try:
        # Iterate through all Parcel records with status='deposited'
        deposited_parcels = Parcel.query.filter_by(status='deposited').all()

        current_parcel = None
        for parcel_attempt in deposited_parcels:
            if verify_pin(parcel_attempt.pin_hash, provided_pin):
                current_parcel = parcel_attempt
                break
        
        if not current_parcel:
            return None, None, "Invalid PIN."

        # Check if PIN has expired
        if current_parcel.otp_expiry < datetime.utcnow():
            current_parcel.status = 'expired'
            db.session.add(current_parcel)
            db.session.commit()
            # (Later: Add to AuditLog FR-07 for expired attempt)
            return None, None, "PIN has expired."

        # PIN is valid and not expired
        current_parcel.status = 'picked_up'
        
        locker = Locker.query.get(current_parcel.locker_id)
        if not locker:
            # This should ideally not happen if data integrity is maintained
            db.session.rollback() # Rollback status change on parcel if locker not found
            return None, None, "Associated locker not found. Data integrity issue."

        locker.status = 'free'
        
        db.session.add(current_parcel)
        db.session.add(locker)
        db.session.commit()
        
        # (Later: Add to AuditLog FR-07 for successful pickup)
        return current_parcel, locker, None  # Success

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in process_pickup: {e}") # Use current_app.logger
        return None, None, "Error processing pickup request."

def verify_admin_credentials(username, password) -> AdminUser | None:
    admin_user = AdminUser.query.filter_by(username=username).first()
    if admin_user and admin_user.check_password(password):
        return admin_user
    return None

# Potentially other service functions will be added here later
