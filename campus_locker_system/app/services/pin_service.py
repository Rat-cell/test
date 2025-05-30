from datetime import datetime, timedelta
from flask import current_app, url_for
from app import db
from app.business.pin import PinManager
from app.business.parcel import Parcel
from app.services.audit_service import AuditService
from typing import Tuple, Optional

def generate_pin_by_token(token: str) -> Tuple[Optional[Parcel], str]:
    """
    FR-02: Generate PIN - Create a 6-digit PIN and store its salted SHA-256 hash (email-based system)
    NFR-03: Security - Token-based PIN generation with rate limiting and audit logging
    """
    try:
        # Find parcel with matching token
        parcel = Parcel.query.filter_by(pin_generation_token=token).first()
        
        if not parcel:
            # NFR-03: Security - Log invalid token attempts for security monitoring
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
        
        # NFR-03: Security - Check rate limiting to prevent abuse
        max_daily_generations = current_app.config.get('MAX_PIN_GENERATIONS_PER_DAY', 3)
        if not parcel.can_generate_pin(max_daily_generations):
            AuditService.log_event("PIN_GENERATION_FAIL_RATE_LIMIT", details={
                "parcel_id": parcel.id,
                "generation_count": parcel.pin_generation_count,
                "max_allowed": max_daily_generations
            })
            return None, f"Daily PIN generation limit reached ({max_daily_generations} per day). Please try again tomorrow."
        
        # FR-02 & NFR-03: Generate new 6-digit PIN with salted SHA-256 hash
        new_pin, new_pin_hash = PinManager.generate_pin_and_hash()
        
        # NFR-03: Security - Store salted hash (invalidates previous PIN for same parcel)
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
        # FR-07: Audit Trail - Record PIN generation event with timestamp and security details
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

def regenerate_pin_token(parcel_id: int, recipient_email: str, admin_reset: bool = False) -> Tuple[bool, str]:
    """
    FR-05: Re-issue PIN - Regenerate PIN generation token for expired links
    """
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
        
        # Reset generation count if it's a new day OR if admin is resetting
        if admin_reset:
            parcel.pin_generation_count = 0  # Admin reset always resets the limit
        elif parcel.last_pin_generation and (datetime.utcnow() - parcel.last_pin_generation).days >= 1:
            parcel.pin_generation_count = 0  # Natural daily reset
        
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
            "notification_sent": notification_success,
            "admin_reset": admin_reset
        })
        
        if notification_success:
            return True, f"New PIN generation link sent to {recipient_email}"
        else:
            return True, f"New PIN generation link created. Note: Email notification may have failed."
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error regenerating PIN token: {str(e)}")
        return False, "An error occurred while regenerating the PIN token."

def request_pin_regeneration_by_recipient_email_and_locker(recipient_email: str, locker_id: str, admin_override_parcel_id: int = None):
    """
    FR-05: Re-issue PIN - User form handler for PIN regeneration requests
    """
    try:
        # Find the parcel by email and locker ID, or by admin override parcel ID
        if admin_override_parcel_id:
            # Admin override - find parcel by ID directly
            parcel = Parcel.query.filter(
                Parcel.id == admin_override_parcel_id,
                Parcel.status == 'deposited'
            ).first()
        else:
            # Normal user request - find by email and locker ID
            parcel = Parcel.query.filter(
                Parcel.recipient_email.ilike(recipient_email),
                Parcel.locker_id == int(locker_id),
                Parcel.status == 'deposited'
            ).first()
        
        if not parcel:
            # Return generic message for security (prevent fishing)
            return None, "If your details matched an active parcel, a new PIN would have been sent."
        
        # Use email-based PIN regeneration (admin override means admin is resetting)
        success, message = regenerate_pin_token(parcel.id, parcel.recipient_email, admin_reset=(admin_override_parcel_id is not None))
        
        if success:
            return parcel, "PIN generation link has been regenerated and sent to your email."
        else:
            return None, message
            
    except ValueError:
        # Invalid locker_id conversion
        return None, "Invalid locker ID format."
    except Exception as e:
        current_app.logger.error(f"Error in request_pin_regeneration_by_recipient_email_and_locker: {str(e)}")
        return None, "An error occurred while processing your request." 