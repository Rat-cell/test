from datetime import datetime, timedelta
from flask import current_app, url_for
from app import db
from app.business.pin import PinManager
from app.business.parcel import Parcel
from app.services.audit_service import AuditService
from typing import Tuple, Optional

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
        
        # Generate PIN generation URL for regeneration link
        pin_generation_url = url_for('main.generate_pin_by_token_route', 
                                   token=parcel.pin_generation_token, 
                                   _external=True)
        
        # Send new PIN via email using notification service
        from app.services.notification_service import NotificationService
        notification_success, notification_message = NotificationService.send_pin_reissue_notification(
            recipient_email=parcel.recipient_email,
            parcel_id=parcel.id,
            locker_id=parcel.locker_id,
            pin=new_pin,
            expiry_time=parcel.otp_expiry,
            pin_generation_url=pin_generation_url
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
        
        # Generate PIN generation URL for regeneration link
        pin_generation_url = url_for('main.generate_pin_by_token_route', 
                                   token=parcel.pin_generation_token, 
                                   _external=True)
        
        # Send new PIN via email using notification service
        from app.services.notification_service import NotificationService
        notification_success, notification_message = NotificationService.send_pin_regeneration_notification(
            recipient_email=parcel.recipient_email,
            parcel_id=parcel.id,
            locker_id=parcel.locker_id,
            pin=new_pin,
            expiry_time=parcel.otp_expiry,
            pin_generation_url=pin_generation_url
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

def generate_pin_by_token(token: str) -> Tuple[Optional[Parcel], str]:
    """Generate a PIN using a valid email token (email-based PIN system)"""
    try:
        # Find parcel with matching token
        parcel = Parcel.query.filter_by(pin_generation_token=token).first()
        
        if not parcel:
            AuditService.log_event("PIN_GENERATION_FAIL_INVALID_TOKEN", details={
                "token_prefix": token[:8] + "..." if len(token) > 8 else token,
                "reason": "Token not found"
            })
            return None, "Invalid or expired token."
        
        # Check if parcel is in correct status
        if parcel.status != 'deposited':
            AuditService.log_event("PIN_GENERATION_FAIL_INVALID_STATUS", details={
                "parcel_id": parcel.id,
                "status": parcel.status,
                "token_prefix": token[:8] + "..."
            })
            return None, f"Parcel is not available for pickup (status: {parcel.status})."
        
        # Check if token is still valid
        if not parcel.is_pin_token_valid():
            AuditService.log_event("PIN_GENERATION_FAIL_TOKEN_EXPIRED", details={
                "parcel_id": parcel.id,
                "token_expiry": parcel.pin_generation_token_expiry.isoformat() if parcel.pin_generation_token_expiry else None,
                "token_prefix": token[:8] + "..."
            })
            return None, "Token has expired. Please request a new PIN generation link."
        
        # Check rate limiting
        max_daily_generations = current_app.config.get('MAX_PIN_GENERATIONS_PER_DAY', 3)
        if not parcel.can_generate_pin(max_daily_generations):
            AuditService.log_event("PIN_GENERATION_FAIL_RATE_LIMIT", details={
                "parcel_id": parcel.id,
                "generation_count": parcel.pin_generation_count,
                "max_allowed": max_daily_generations
            })
            return None, f"Daily PIN generation limit reached ({max_daily_generations} per day). Please try again tomorrow."
        
        # Generate new PIN
        new_pin, new_pin_hash = PinManager.generate_pin_and_hash()
        
        # Update parcel with new PIN
        parcel.pin_hash = new_pin_hash
        parcel.otp_expiry = PinManager.generate_expiry_time()
        parcel.pin_generation_count += 1
        parcel.last_pin_generation = datetime.utcnow()
        
        db.session.commit()
        
        # Generate PIN generation URL for regeneration link
        pin_generation_url = url_for('main.generate_pin_by_token_route', 
                                   token=parcel.pin_generation_token, 
                                   _external=True)
        
        # Send PIN via email using notification service
        from app.services.notification_service import NotificationService
        notification_success, notification_message = NotificationService.send_pin_generation_notification(
            recipient_email=parcel.recipient_email,
            parcel_id=parcel.id,
            locker_id=parcel.locker_id,
            pin=new_pin,
            expiry_time=parcel.otp_expiry,
            pin_generation_url=pin_generation_url
        )
        
        # Log the PIN generation
        AuditService.log_event("PIN_GENERATED_VIA_EMAIL", details={
            "parcel_id": parcel.id,
            "locker_id": parcel.locker_id,
            "generation_count": parcel.pin_generation_count,
            "notification_sent": notification_success
        })
        
        if notification_success:
            return parcel, f"PIN generated successfully and sent to {parcel.recipient_email}"
        else:
            current_app.logger.warning(f"PIN generated but notification failed: {notification_message}")
            return parcel, f"PIN generated successfully. Note: Email notification may have failed."
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error generating PIN by token: {str(e)}")
        AuditService.log_event("PIN_GENERATION_ERROR", details={
            "error": str(e),
            "token_prefix": token[:8] + "..." if len(token) > 8 else token
        })
        return None, "An error occurred while generating the PIN."

def regenerate_pin_token(parcel_id: int, recipient_email: str) -> Tuple[bool, str]:
    """Regenerate PIN generation token for a parcel (admin or recipient function)"""
    try:
        parcel = db.session.get(Parcel, parcel_id)
        
        if not parcel:
            return False, "Parcel not found."
        
        if parcel.recipient_email.lower() != recipient_email.lower():
            return False, "Email does not match parcel recipient."
        
        if parcel.status != 'deposited':
            return False, f"Parcel is not in 'deposited' state (current status: {parcel.status})."
        
        # Generate new token
        token = parcel.generate_pin_token()
        
        # Reset generation count if it's a new day
        if parcel.last_pin_generation and (datetime.utcnow() - parcel.last_pin_generation).days >= 1:
            parcel.pin_generation_count = 0
        
        db.session.commit()
        
        # Generate new PIN generation URL
        pin_generation_url = url_for('main.generate_pin_by_token_route', 
                                   token=token, 
                                   _external=True)
        
        # Send new parcel ready notification via notification service
        from app.services.notification_service import NotificationService
        notification_success, notification_message = NotificationService.send_parcel_ready_notification(
            recipient_email=recipient_email,
            parcel_id=parcel.id,
            locker_id=parcel.locker_id,
            deposited_time=parcel.deposited_at,
            pin_generation_url=pin_generation_url
        )
        
        # Log the token regeneration
        AuditService.log_event("PIN_TOKEN_REGENERATED", details={
            "parcel_id": parcel.id,
            "recipient_email": recipient_email,
            "notification_sent": notification_success
        })
        
        if notification_success:
            return True, f"New PIN generation link sent to {recipient_email}"
        else:
            return True, f"New PIN generation link created. Note: Email notification may have failed."
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error regenerating PIN token: {str(e)}")
        return False, "An error occurred while regenerating the PIN token."

def request_pin_regeneration_by_recipient_email_and_locker(recipient_email: str, locker_id: str):
    """Handle recipient request for PIN regeneration using email and locker ID"""
    try:
        # Find the parcel by email and locker ID
        parcel = Parcel.query.filter(
            Parcel.recipient_email.ilike(recipient_email),
            Parcel.locker_id == int(locker_id),
            Parcel.status == 'deposited'
        ).first()
        
        if not parcel:
            # Return generic message for security (prevent fishing)
            return None, "If your details matched an active parcel, a new PIN would have been sent."
        
        # Check if email-based PIN generation is enabled
        use_email_pin = current_app.config.get('ENABLE_EMAIL_BASED_PIN_GENERATION', True)
        
        if use_email_pin and parcel.pin_generation_token:
            # Use email-based PIN regeneration (regenerate token)
            success, message = regenerate_pin_token(parcel.id, recipient_email)
            
            # Log the regeneration request
            AuditService.log_event("PIN_TOKEN_REGENERATION_REQUESTED", details={
                "parcel_id": parcel.id,
                "recipient_email": recipient_email,
                "locker_id": locker_id,
                "success": success
            })
            
            if success:
                return parcel, "If your details matched an active parcel, a new PIN generation link has been sent to your email."
            else:
                return None, "If your details matched an active parcel, a new PIN would have been sent."
        else:
            # Use traditional PIN regeneration
            return request_pin_regeneration_by_recipient(parcel.id, recipient_email)
        
    except ValueError:
        # Invalid locker_id (not a number)
        return None, "If your details matched an active parcel, a new PIN would have been sent."
    except Exception as e:
        current_app.logger.error(f"Error in recipient PIN regeneration request: {str(e)}")
        return None, "If your details matched an active parcel, a new PIN would have been sent." 