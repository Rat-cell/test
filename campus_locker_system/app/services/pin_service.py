from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.business.pin import PinManager
from app.business.parcel import Parcel
from app.services.audit_service import AuditService

def reissue_pin(parcel_id: int):
    """Reissue a new PIN for a parcel"""
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return None, "Parcel not found."
        
        if parcel.status != 'deposited':
            return None, f"Parcel is not in 'deposited' state (current status: {parcel.status}). Cannot reissue PIN."
        
        # Generate new PIN and hash
        new_pin, new_pin_hash = PinManager.generate_pin_and_hash()
        
        # Update parcel with new PIN info
        parcel.pin_hash = new_pin_hash
        parcel.otp_expiry = PinManager.generate_expiry_time()
        
        db.session.commit()
        
        # Send new PIN via email using notification service
        from app.services.notification_service import NotificationService
        notification_success, notification_message = NotificationService.send_pin_reissue_notification(
            recipient_email=parcel.recipient_email,
            parcel_id=parcel.id,
            locker_id=parcel.locker_id,
            pin=new_pin,
            expiry_time=parcel.otp_expiry
        )
        
        # Log the reissue
        AuditService.log_event(f"PIN reissued for parcel {parcel.id} by admin")
        
        # Check notification result
        if notification_success:
            return parcel, f"New PIN issued and sent to {parcel.recipient_email}"
        else:
            current_app.logger.warning(f"PIN reissued but notification failed: {notification_message}")
            return parcel, f"New PIN issued for parcel {parcel.id}. Note: Email notification may have failed."
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error reissuing PIN for parcel {parcel_id}: {str(e)}")
        return None, "An error occurred while reissuing the PIN."

def request_pin_regeneration_by_recipient(parcel_id: int, provided_email: str):
    """Handle recipient request for PIN regeneration"""
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return None, "Parcel not found."
        
        if parcel.recipient_email.lower() != provided_email.lower():
            return None, "Email does not match parcel recipient."
        
        if parcel.status != 'deposited':
            return None, f"Parcel is not in 'deposited' state (current status: {parcel.status}). Cannot regenerate PIN."
        
        # Generate new PIN and hash
        new_pin, new_pin_hash = PinManager.generate_pin_and_hash()
        
        # Update parcel with new PIN info
        parcel.pin_hash = new_pin_hash
        parcel.otp_expiry = PinManager.generate_expiry_time()
        
        db.session.commit()
        
        # Send new PIN via email using notification service
        from app.services.notification_service import NotificationService
        notification_success, notification_message = NotificationService.send_pin_regeneration_notification(
            recipient_email=parcel.recipient_email,
            parcel_id=parcel.id,
            locker_id=parcel.locker_id,
            pin=new_pin,
            expiry_time=parcel.otp_expiry
        )
        
        # Log the regeneration
        AuditService.log_event(f"PIN regenerated for parcel {parcel.id} by recipient request")
        
        # Check notification result
        if notification_success:
            return parcel, f"New PIN generated and sent to {parcel.recipient_email}"
        else:
            current_app.logger.warning(f"PIN regenerated but notification failed: {notification_message}")
            return parcel, f"New PIN generated for parcel {parcel.id}. Note: Email notification may have failed."
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error regenerating PIN for parcel {parcel_id}: {str(e)}")
        return None, "An error occurred while regenerating the PIN." 