from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.persistence.models import Locker
from app.business.parcel import Parcel, ParcelManager
from app.business.locker import LockerManager
from app.business.pin import PinManager
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
import hashlib
import os
import binascii
import json
from typing import Optional, Tuple

def assign_locker_and_create_parcel(recipient_email: str, preferred_size: str):
    """
    FR-01: Assign Locker - Find available locker and create parcel
    NFR-01: Performance - Optimized for sub-200ms assignment with efficient queries
    """
    try:
        # NFR-01: Performance - Fast in-memory validation before database access
        if not ParcelManager.is_valid_email(recipient_email):
            return None, "Invalid email address format."
        
        if not LockerManager.is_valid_size(preferred_size):
            return None, f"Invalid parcel size: {preferred_size}. Valid sizes: {', '.join(LockerManager.VALID_SIZES)}"
        
        # FR-01: Find available locker matching preferred size
        # NFR-01: Performance - Single database query for optimal response time
        locker = LockerManager.find_available_locker(preferred_size)
        if not locker:
            return None, f"No available {preferred_size} lockers. Please try again later or choose a different size."
        
        # NFR-01: Performance - Immediate status update to prevent race conditions
        locker.status = 'occupied'
        db.session.commit()
        
        # Create parcel with email-based PIN generation (no immediate PIN)
        parcel = Parcel(
            locker_id=locker.id,
            recipient_email=recipient_email,
            status='deposited',
            deposited_at=datetime.utcnow()
        )
        
        # Generate PIN generation token
        token = parcel.generate_pin_token()
        
        db.session.add(parcel)
        db.session.commit()
        
        # Generate PIN generation URL
        from flask import url_for
        pin_generation_url = url_for('main.generate_pin_by_token_route', 
                                   token=token, 
                                   _external=True)
        
        # Send parcel ready notification with PIN generation link
        notification_success, notification_message = NotificationService.send_parcel_ready_notification(
            recipient_email=recipient_email,
            parcel_id=parcel.id,
            locker_id=locker.id,
            deposited_time=parcel.deposited_at,
            pin_generation_url=pin_generation_url
        )
        
        # Log the parcel creation
        # FR-07: Audit Trail - Record parcel deposit event with timestamp and details
        AuditService.log_event("PARCEL_CREATED_EMAIL_PIN", details={
            "parcel_id": parcel.id,
            "locker_id": locker.id,
            "recipient_email": recipient_email,
            "notification_sent": notification_success
        })
        
        if notification_success:
            return parcel, f"Parcel deposited successfully. PIN generation link sent to {recipient_email}."
        else:
            current_app.logger.warning(f"Parcel created but notification failed: {notification_message}")
            return parcel, f"Parcel deposited successfully. Note: Email notification may have failed."
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in assign_locker_and_create_parcel: {str(e)}")
        return None, "An error occurred while assigning the locker. Please try again."

def process_pickup(provided_pin: str):
    """NFR-03: Security - Secure PIN verification process with audit logging"""
    try:
        # Find parcel with matching PIN
        parcels = Parcel.query.filter_by(status='deposited').all()
        
        for parcel in parcels:
            # Skip parcels without PIN hash (email-based PIN not yet generated)
            if not parcel.pin_hash:
                continue
                
            # NFR-03: Security - Verify PIN using cryptographically secure comparison
            if PinManager.verify_pin(parcel.pin_hash, provided_pin):
                # Check if PIN has expired
                if PinManager.is_pin_expired(parcel.otp_expiry):
                    # FR-07: Audit Trail - Record failed pickup attempt with timestamp and reason
                    # FR-09: Invalid PIN Error Handling - Provide clear expired PIN error message
                    # NFR-03: Security - Log expired PIN attempts for security monitoring
                    AuditService.log_event("USER_PICKUP_FAIL_PIN_EXPIRED", details={
                        "parcel_id": parcel.id,
                        "provided_pin_pattern": provided_pin[:3] + "XXX",
                        "expiry_time": parcel.otp_expiry.isoformat() if parcel.otp_expiry else None
                    })
                    return None, "PIN has expired. Please request a new PIN."
                
                # Update parcel status
                parcel.status = 'picked_up'
                parcel.picked_up_at = datetime.utcnow()
                
                # Update locker status
                locker = db.session.get(Locker, parcel.locker_id)
                if locker:
                    # FR-08: Only set to free if not out of service
                    if locker.status != 'out_of_service':
                        locker.status = 'free'
                    # FR-08: If it was out of service, leave it as out of service
                
                db.session.commit()
                
                # FR-07: Audit Trail - Record successful pickup event with timestamp and PIN verification details
                # Log the pickup
                AuditService.log_event(f"Parcel {parcel.id} picked up from locker {parcel.locker_id}")
                
                return parcel, f"Parcel successfully picked up from locker {parcel.locker_id}."
        
        # FR-07: Audit Trail - Record failed pickup attempt with timestamp and reason (invalid PIN)
        # FR-09: Invalid PIN Error Handling - Provide clear invalid PIN error message
        # Log the invalid PIN attempt
        AuditService.log_event("USER_PICKUP_FAIL_INVALID_PIN", details={
            "provided_pin_pattern": provided_pin[:3] + "XXX",
            "reason": "No matching deposited parcel found"
        })
        
        return None, "Invalid PIN or no matching parcel found."
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing pickup: {str(e)}")
        # FR-09: Invalid PIN Error Handling - Provide system error message
        return None, "An error occurred while processing the pickup."

def retract_deposit(parcel_id: int):
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return None, "Parcel not found."
        if parcel.status != 'deposited':
            return None, f"Parcel is not in 'deposited' state (current status: {parcel.status}). Cannot retract."
        locker = db.session.get(Locker, parcel.locker_id)
        if not locker:
            current_app.logger.error(f"Data inconsistency: Locker ID {parcel.locker_id} not found for parcel {parcel.id} during retraction.")
            return None, "Associated locker not found. Data inconsistency."
        original_locker_status = locker.status
        parcel.status = 'retracted_by_sender'
        if original_locker_status == 'occupied':
            locker.status = 'free'
        elif original_locker_status == 'out_of_service':
            locker.status = 'out_of_service'
        else:
            current_app.logger.warning(f"Locker {locker.id} had unexpected status '{original_locker_status}' during deposit retraction for parcel {parcel.id}. Setting to 'free'.")
            locker.status = 'free'
        db.session.add(parcel)
        db.session.add(locker)
        db.session.commit()
        AuditService.log_event("USER_DEPOSIT_RETRACTED", details={
            "parcel_id": parcel.id,
            "locker_id": locker.id,
            "reason": "Sender indicated mistake"
        })
        return parcel, None
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in retract_deposit for parcel {parcel_id}: {e}")
        return None, "A database error occurred while retracting deposit."

def dispute_pickup(parcel_id: int):
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return None, "Parcel not found."
        if parcel.status != 'picked_up':
            return None, f"Parcel is not in 'picked_up' state (current status: {parcel.status}). Cannot dispute."
        locker = db.session.get(Locker, parcel.locker_id)
        if not locker:
            current_app.logger.error(f"Data inconsistency: Locker ID {parcel.locker_id} not found for parcel {parcel.id} during pickup dispute.")
            return None, "Associated locker not found. Data inconsistency."
        parcel.status = 'pickup_disputed'
        locker.status = 'disputed_contents'
        db.session.add(parcel)
        db.session.add(locker)
        db.session.commit()
        AuditService.log_event("USER_PICKUP_DISPUTED", details={
            "parcel_id": parcel.id,
            "locker_id": locker.id,
            "reason": "Recipient indicated issue post-pickup"
        })
        return parcel, None
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in dispute_pickup for parcel {parcel_id}: {e}")
        return None, "A database error occurred while disputing pickup."

# FR-06: Report Missing Item - Business logic implementation
def report_parcel_missing_by_recipient(parcel_id: int) -> Tuple[Optional[Parcel], Optional[str]]:
    """
    FR-06: Report Missing Item - Core business logic for recipient reporting parcel as missing
    """
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return None, "Parcel not found."
        
        # FR-06: Enhanced business rule - allow reporting missing from pickup success scenarios
        current_status = parcel.status.strip() if parcel.status else "None"
        
        # Allow missing reports from:
        # - 'deposited': parcel never picked up but reported missing
        # - 'picked_up': pickup success but parcel was actually missing from locker
        allowed_statuses = ['deposited', 'picked_up']
        
        if current_status not in allowed_statuses:
            # Enhanced error message for debugging
            current_app.logger.warning(f"FR-06: Missing report rejected for parcel {parcel_id}. Status: '{current_status}' (type: {type(parcel.status)}), allowed: {allowed_statuses}")
            return None, f"Parcel cannot be reported missing by recipient from its current state: '{current_status}'. Allowed states: {', '.join(allowed_statuses)}."
        
        # Get the locker before updating parcel
        locker = db.session.get(Locker, parcel.locker_id) if parcel.locker_id else None
        
        # Store original status for audit logging
        original_status = current_status
        
        # FR-06: Update parcel status to missing as required
        parcel.status = 'missing'
        
        # FR-06: Take locker out of service for inspection as specified in requirements
        if locker:
            locker.status = 'out_of_service'
        
        db.session.commit()
        
        # FR-06: Enhanced audit logging for missing report event
        AuditService.log_event("PARCEL_REPORTED_MISSING_BY_RECIPIENT", details={
            "parcel_id": parcel_id,
            "previous_status": original_status,
            "new_status": "missing",
            "locker_id": parcel.locker_id,
            "locker_set_to": "out_of_service" if locker else "no_locker",
            "reported_by": "recipient",
            "reported_from_pickup_success": original_status == 'picked_up'
        })
        
        current_app.logger.info(f"FR-06: Parcel {parcel_id} successfully reported missing by recipient. Previous status: '{original_status}'")
        
        return parcel, None
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error reporting parcel {parcel_id} as missing by recipient: {str(e)}")
        return None, f"Database error occurred while reporting parcel as missing."

def mark_parcel_missing_by_admin(admin_id: int, admin_username: str, parcel_id: int) -> tuple[Parcel | None, str | None]:
    """Admin function to mark a parcel as missing"""
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return None, "Parcel not found."

        if parcel.status == 'missing':
            return parcel, "Parcel is already marked as missing." # No error, but no change

        original_parcel_status = parcel.status
        parcel.status = 'missing'
        db.session.add(parcel)

        # ALWAYS set locker to out_of_service when marking parcel as missing
        # This ensures investigation can take place
        if parcel.locker_id:
            locker = db.session.get(Locker, parcel.locker_id)
            if locker:
                original_locker_status = locker.status
                locker.status = 'out_of_service'
                db.session.add(locker)
                
                AuditService.log_event("LOCKER_SET_OUT_OF_SERVICE_FOR_MISSING_PARCEL", details={
                    "admin_id": admin_id,
                    "admin_username": admin_username,
                    "parcel_id": parcel.id,
                    "locker_id": parcel.locker_id,
                    "original_locker_status": original_locker_status,
                    "reason": "Parcel marked as missing - investigation required"
                })
            else:
                current_app.logger.warning(f"Locker ID {parcel.locker_id} not found for parcel {parcel.id} being marked missing by admin.")
        
        db.session.commit()

        AuditService.log_event("ADMIN_MARKED_PARCEL_MISSING", details={
            "admin_id": admin_id,
            "admin_username": admin_username,
            "parcel_id": parcel.id,
            "locker_id": parcel.locker_id,
            "original_parcel_status": original_parcel_status
        })
        return parcel, None
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in mark_parcel_missing_by_admin for parcel {parcel_id}: {e}")
        return None, "A database error occurred while marking parcel missing."

def process_overdue_parcels():
    max_pickup_days = current_app.config.get('PARCEL_MAX_PICKUP_DAYS', 7)
    deposited_parcels = Parcel.query.filter(
        Parcel.status == 'deposited',
        Parcel.deposited_at.isnot(None)
    ).all()
    processed_count = 0
    items_to_update_in_session = []
    for parcel in deposited_parcels:
        if not isinstance(parcel.deposited_at, datetime):
            AuditService.log_event("PROCESS_OVERDUE_FAIL_INVALID_DEPOSITED_AT", {
                "parcel_id": parcel.id, 
                "deposited_at_type": str(type(parcel.deposited_at)),
                "reason": "Parcel has invalid or missing deposited_at timestamp."
            })
            continue
        if datetime.utcnow() > parcel.deposited_at + timedelta(days=max_pickup_days):
            try:
                locker = parcel.locker
                if not locker:
                    AuditService.log_event("PROCESS_OVERDUE_FAIL_NO_LOCKER", {
                        "parcel_id": parcel.id, 
                        "reason": "Locker not found for deposited parcel."
                    })
                    continue
                old_parcel_status = parcel.status
                old_locker_status = locker.status
                parcel.status = 'return_to_sender'
                if locker.status in ['occupied', 'out_of_service']:
                    locker.status = 'awaiting_collection'
                else:
                    locker.status = 'free'
                items_to_update_in_session.append(parcel)
                if old_locker_status != locker.status:
                    items_to_update_in_session.append(locker)
                AuditService.log_event("PARCEL_MARKED_RETURN_TO_SENDER", {
                    "parcel_id": parcel.id,
                    "locker_id": locker.id,
                    "old_parcel_status": old_parcel_status,
                    "new_parcel_status": parcel.status, # 'return_to_sender'
                    "old_locker_status": old_locker_status,
                    "new_locker_status": locker.status,
                    "max_pickup_days_configured": max_pickup_days
                })
                processed_count += 1
            except Exception as e:
                current_app.logger.error(f"Error processing parcel ID {parcel.id} for overdue status: {str(e)}")
                AuditService.log_event("PROCESS_OVERDUE_PARCEL_ERROR", {
                    "parcel_id": parcel.id, 
                    "error": str(e),
                    "action": "Skipped this parcel, continued with batch."
                })
                continue
    if items_to_update_in_session:
        try:
            db.session.add_all(items_to_update_in_session)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error committing batch of overdue parcels: {str(e)}")
            AuditService.log_event("PROCESS_OVERDUE_BATCH_COMMIT_ERROR", {
                "error": str(e), 
                "num_parcels_intended_for_update_in_batch": processed_count
            })
            return 0, f"Error committing batch of overdue parcels: {str(e)}"
    return processed_count, f"{processed_count} overdue parcels processed."

# FR-04: Send Reminder After 24h of Occupancy - Main processing function
def process_reminder_notifications():
    """
    FR-04: Send Reminder After 24h of Occupancy - Process and send reminder notifications for parcels
    """
    try:
        # FR-04: Get configurable reminder timing from environment
        from flask import current_app
        reminder_hours = current_app.config.get('REMINDER_HOURS_AFTER_DEPOSIT', 24)
        
        # FR-04: Find parcels that need reminder notifications
        from datetime import datetime, timedelta
        from app.persistence.models import Parcel
        
        # FR-04: Calculate cutoff time for eligible parcels
        cutoff_time = datetime.utcnow() - timedelta(hours=reminder_hours)
        
        # FR-04: Query for parcels that need reminders
        # - Status must be 'deposited' (not picked up yet)
        # - Deposited before cutoff time (older than configured hours)
        # - No reminder sent yet (reminder_sent_at is NULL)
        eligible_parcels = Parcel.query.filter(
            Parcel.status == 'deposited',
            Parcel.deposited_at <= cutoff_time,
            Parcel.reminder_sent_at.is_(None)  # FR-04: No reminder sent yet
        ).all()
        
        # FR-04: Process each eligible parcel
        processed_count = 0
        error_count = 0
        
        for parcel in eligible_parcels:
            try:
                # FR-04: Generate PIN regeneration URL for the reminder email
                pin_generation_url = f"http://localhost/generate-pin/{parcel.pin_generation_token}" if parcel.pin_generation_token else "http://localhost/request-new-pin"
                
                # FR-04: Send individual reminder notification
                success, message = NotificationService.send_24h_reminder_notification(
                    recipient_email=parcel.recipient_email,
                    parcel_id=parcel.id,
                    locker_id=parcel.locker_id,
                    deposited_time=parcel.deposited_at,
                    pin_generation_url=pin_generation_url
                )
                
                if success:
                    # FR-04: Mark reminder as sent to prevent duplicates
                    parcel.reminder_sent_at = datetime.utcnow()
                    db.session.commit()
                    processed_count += 1
                    
                    # FR-04: Log successful reminder for audit trail
                    AuditService.log_event("FR-04_REMINDER_SENT_SUCCESS", {
                        "parcel_id": parcel.id,
                        "locker_id": parcel.locker_id,
                        "recipient_email_domain": parcel.recipient_email.split('@')[1] if '@' in parcel.recipient_email else 'unknown',
                        "deposited_hours_ago": int((datetime.utcnow() - parcel.deposited_at).total_seconds() / 3600),
                        "configured_reminder_hours": reminder_hours
                    })
                else:
                    error_count += 1
                    # FR-04: Log failed reminder attempt
                    AuditService.log_event("FR-04_REMINDER_SENT_FAILED", {
                        "parcel_id": parcel.id,
                        "error_message": message,
                        "recipient_email_domain": parcel.recipient_email.split('@')[1] if '@' in parcel.recipient_email else 'unknown'
                    })
                    
            except Exception as e:
                error_count += 1
                current_app.logger.error(f"FR-04: Error processing reminder for parcel {parcel.id}: {str(e)}")
                continue
        
        # FR-04: Log overall processing results
        AuditService.log_event("FR-04_BULK_REMINDER_PROCESSING_COMPLETED", {
            "total_eligible_parcels": len(eligible_parcels),
            "processed_count": processed_count,
            "error_count": error_count,
            "configured_reminder_hours": reminder_hours,
            "cutoff_time": cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        return processed_count, error_count
        
    except Exception as e:
        current_app.logger.error(f"FR-04: Critical error in reminder processing: {str(e)}")
        return 0, 1

# FR-04: Send Individual Reminder - Admin action for specific parcel
def send_individual_reminder(parcel_id: int, admin_id: int, admin_username: str):
    """
    FR-04: Send Reminder After 24h of Occupancy - Send reminder notification for a specific parcel (admin-initiated)
    """
    try:
        # FR-04: Validate parcel exists and is eligible for reminder
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return False, "Parcel not found"
        
        # FR-04: Check if parcel is in a state where reminder makes sense
        if parcel.status != 'deposited':
            return False, f"Parcel is not in 'deposited' status (current: {parcel.status}). Reminders are only sent for deposited parcels."
        
        # FR-04: Generate PIN regeneration URL for the reminder email
        pin_generation_url = f"http://localhost/generate-pin/{parcel.pin_generation_token}" if parcel.pin_generation_token else "http://localhost/request-new-pin"
        
        # FR-04: Send individual reminder notification
        success, message = NotificationService.send_24h_reminder_notification(
            recipient_email=parcel.recipient_email,
            parcel_id=parcel.id,
            locker_id=parcel.locker_id,
            deposited_time=parcel.deposited_at,
            pin_generation_url=pin_generation_url
        )
        
        if success:
            # FR-04: Update reminder sent timestamp (admin can override automatic reminders)
            parcel.reminder_sent_at = datetime.utcnow()
            db.session.commit()
            
            # FR-04: Log admin-initiated individual reminder for audit trail
            AuditService.log_event("FR-04_ADMIN_INDIVIDUAL_REMINDER_SENT", {
                "admin_id": admin_id,
                "admin_username": admin_username,
                "parcel_id": parcel.id,
                "locker_id": parcel.locker_id,
                "recipient_email_domain": parcel.recipient_email.split('@')[1] if '@' in parcel.recipient_email else 'unknown',
                "deposited_hours_ago": int((datetime.utcnow() - parcel.deposited_at).total_seconds() / 3600),
                "reminder_type": "admin_initiated_individual"
            })
            
            return True, f"Reminder sent successfully to {parcel.recipient_email}"
        else:
            # FR-04: Log failed admin reminder attempt
            AuditService.log_event("FR-04_ADMIN_INDIVIDUAL_REMINDER_FAILED", {
                "admin_id": admin_id,
                "admin_username": admin_username,
                "parcel_id": parcel.id,
                "error_message": message,
                "recipient_email_domain": parcel.recipient_email.split('@')[1] if '@' in parcel.recipient_email else 'unknown'
            })
            
            return False, f"Failed to send reminder: {message}"
            
    except Exception as e:
        current_app.logger.error(f"FR-04: Error sending individual reminder for parcel {parcel_id}: {str(e)}")
        
        # FR-04: Log exception in admin individual reminder
        AuditService.log_event("FR-04_ADMIN_INDIVIDUAL_REMINDER_EXCEPTION", {
            "admin_id": admin_id,
            "admin_username": admin_username,
            "parcel_id": parcel_id,
            "error_details": str(e)
        })
        
        return False, f"An unexpected error occurred: {str(e)}" 