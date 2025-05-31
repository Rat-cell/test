from datetime import datetime, timedelta
import datetime as dt
from flask import current_app, url_for
from app import db
from app.business.pin import PinManager
from app.persistence.models import Parcel as PersistenceParcel
from app.persistence.repositories.parcel_repository import ParcelRepository
from app.services.audit_service import AuditService
from typing import Tuple, Optional

def _safe_token_prefix(token: str) -> str:
    """
    Helper function to safely create token prefix for logging
    Maintains security by not logging full tokens while handling None values
    """
    if not token:
        return "None or empty"
    return token[:8] + "..." if len(token) > 8 else token

def get_pin_expiry_hours() -> int:
    """
    Returns the PIN expiry duration in hours from PinManager.
    """
    # NFR-01: Performance - Accessing a class variable is efficient
    # This keeps the presentation layer from directly accessing the business layer.
    return PinManager.get_pin_expiry_hours()

def generate_pin_by_token(token: str) -> Tuple[Optional[PersistenceParcel], str]:
    """
    FR-02: Generate PIN - Generate PIN using email-based token system
    NFR-03: Security - Cryptographically secure PIN generation with audit logging
    Follows hexagonal architecture: Service layer coordinates between business logic and repositories
    """
    try:
        # Validate token input (business rule validation)
        if not token:
            current_app.logger.warning("PIN generation attempted with empty or None token")
            AuditService.log_event("PIN_GENERATION_FAIL_INVALID_TOKEN", details={
                "token_prefix": _safe_token_prefix(token),
                "reason": "Invalid token format"
            })
            return None, "Invalid token provided."
        
        # Repository layer: Fetch parcel by PIN generation token
        parcel = ParcelRepository.get_by_pin_generation_token(token)
        
        if not parcel:
            # NFR-03: Security - Log invalid token attempts for security monitoring
            AuditService.log_event("PIN_GENERATION_FAIL_INVALID_TOKEN", details={
                "token_prefix": _safe_token_prefix(token),
                "reason": "Token not found"
            })
            return None, "Invalid or expired token."
        
        # Business rule: Check if parcel is in correct status
        if parcel.status != 'deposited':
            AuditService.log_event("PIN_GENERATION_FAIL_INVALID_STATUS", details={
                "parcel_id": parcel.id,
                "status": parcel.status,
                "token_prefix": _safe_token_prefix(token)
            })
            return None, f"Parcel is not available for pickup (status: {parcel.status})."
        
        # Business rule: Check if token is still valid
        if not parcel.is_pin_token_valid():
            AuditService.log_event("PIN_GENERATION_FAIL_TOKEN_EXPIRED", details={
                "parcel_id": parcel.id,
                "token_expiry": parcel.pin_generation_token_expiry.isoformat() if parcel.pin_generation_token_expiry else None,
                "token_prefix": _safe_token_prefix(token)
            })
            return None, "Token has expired. Please request a new PIN generation link."
        
        # Business rule: Check rate limiting to prevent abuse
        max_daily_generations = current_app.config.get('MAX_PIN_GENERATIONS_PER_DAY', 3)
        if not parcel.can_generate_pin(max_daily_generations):
            AuditService.log_event("PIN_GENERATION_FAIL_RATE_LIMIT", details={
                "parcel_id": parcel.id,
                "generation_count": parcel.pin_generation_count,
                "max_allowed": max_daily_generations
            })
            return None, f"Daily PIN generation limit reached ({max_daily_generations} per day). Please try again tomorrow."
        
        # Business layer: Generate new 6-digit PIN with salted SHA-256 hash
        new_pin, new_pin_hash = PinManager.generate_pin_and_hash()
        
        # Update domain model with new PIN data
        parcel.pin_hash = new_pin_hash
        parcel.otp_expiry = PinManager.generate_expiry_time()
        parcel.pin_generation_count += 1
        parcel.last_pin_generation = datetime.now(dt.UTC)
        
        # Repository layer: Persist changes
        if not ParcelRepository.save(parcel):
            # Rollback handled by repository if save fails
            current_app.logger.error(f"Failed to save parcel {parcel.id} during PIN generation via repository.")
            AuditService.log_event("PIN_GENERATION_FAIL_DB_SAVE", {
                "parcel_id": parcel.id, 
                "token_prefix": _safe_token_prefix(token)
            })
            return None, "Database error saving PIN details."
        
        # Generate PIN generation URL for regeneration link
        try:
            pin_generation_url = url_for('main.generate_pin_by_token_route', 
                                       token=parcel.pin_generation_token, 
                                       _external=True)
        except RuntimeError:
            # Not in request context (e.g., during testing) - use a placeholder URL
            pin_generation_url = f"http://localhost/generate-pin/{parcel.pin_generation_token}"
        
        # External adapter: Send PIN via email using notification service
        from app.services.notification_service import NotificationService
        notification_success, notification_message = NotificationService.send_pin_generation_notification(
            recipient_email=parcel.recipient_email,
            parcel_id=parcel.id,
            locker_id=parcel.locker_id,
            pin=new_pin,
            expiry_time=parcel.otp_expiry,
            pin_generation_url=pin_generation_url
        )
        
        # Audit logging: Record PIN generation event with timestamp and security details
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
        current_app.logger.error(f"Error generating PIN by token: {str(e)}")
        AuditService.log_event("PIN_GENERATION_ERROR", details={
            "error": str(e),
            "token_prefix": _safe_token_prefix(token)
        })
        return None, "An error occurred while generating the PIN."

def regenerate_pin_token(parcel_id: int, recipient_email: str, admin_reset: bool = False) -> Tuple[bool, str]:
    """
    FR-05: Re-issue PIN - Regenerate PIN generation token for expired links
    """
    try:
        # Fetch parcel using repository
        parcel = ParcelRepository.get_by_id(parcel_id)
        
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
        elif parcel.last_pin_generation and (datetime.now(dt.UTC) - parcel.last_pin_generation).days >= 1:
            parcel.pin_generation_count = 0  # Natural daily reset
        
        # Save parcel using repository
        if not ParcelRepository.save(parcel):
            # Rollback handled by repository if save fails
            current_app.logger.error(f"Failed to save parcel {parcel.id} during PIN token regeneration via repository.")
            return False, "Database error updating PIN token details."
        
        # Generate new PIN generation URL
        try:
            pin_generation_url = url_for('main.generate_pin_by_token_route', 
                                       token=token, 
                                       _external=True)
        except RuntimeError:
            # Not in request context (e.g., during testing) - use a placeholder URL
            pin_generation_url = f"http://localhost/generate-pin/{token}"
        
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
        current_app.logger.error(f"Error regenerating PIN token: {str(e)}")
        return False, "An error occurred while regenerating the PIN token."

def request_pin_regeneration_by_recipient_email_and_locker(recipient_email: str, locker_id: str, admin_override_parcel_id: int = None):
    """
    FR-05: Re-issue PIN - User form handler for PIN regeneration requests
    """
    try:
        # Find the parcel by email and locker ID, or by admin override parcel ID
        parcel = None
        if admin_override_parcel_id:
            # Admin override - find parcel by ID directly using repository
            parcel = ParcelRepository.get_by_id(admin_override_parcel_id)
            # Additional check for status, though repository could be enhanced to include this
            if parcel and parcel.status != 'deposited': 
                parcel = None # Not the parcel we are looking for
        else:
            # Normal user request - find by email and locker ID, status 'deposited'
            parcel = ParcelRepository.get_by_email_and_locker_and_status(recipient_email, int(locker_id), 'deposited')
        
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