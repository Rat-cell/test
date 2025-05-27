from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.persistence.models import Locker
from app.business.parcel import Parcel
from app.business.pin import PinManager
import hashlib
import os
import binascii
import json

def assign_locker_and_create_parcel(recipient_email: str, preferred_size: str = None):
    from app.application.services import log_audit_event
    try:
        # Find an available locker
        query = Locker.query.filter_by(status='free')
        if preferred_size:
            query = query.filter_by(size=preferred_size)
        locker = query.first()
        
        if not locker:
            return None, "No available lockers found."
        
        # Generate PIN and hash using PinManager
        pin, pin_hash = PinManager.generate_pin_and_hash()
        
        # Set OTP expiry (24 hours from now)
        otp_expiry = PinManager.generate_expiry_time()
        
        # Create parcel
        parcel = Parcel(
            locker_id=locker.id,
            pin_hash=pin_hash,
            otp_expiry=otp_expiry,
            recipient_email=recipient_email
        )
        
        # Update locker status
        locker.status = 'occupied'
        
        # Commit to database
        db.session.add(parcel)
        db.session.commit()
        
        # Send PIN via email using notification service
        from app.services.notification_service import NotificationService
        notification_success, notification_message = NotificationService.send_parcel_deposit_notification(
            recipient_email=recipient_email,
            parcel_id=parcel.id,
            locker_id=locker.id,
            pin=pin,
            expiry_time=otp_expiry
        )
        
        # Log the deposit
        log_audit_event(f"Parcel {parcel.id} deposited in locker {locker.id} for {recipient_email}", "deposit")
        
        # Check notification result and adjust message
        if notification_success:
            return parcel, f"Parcel deposited in locker {locker.id}. PIN sent to {recipient_email}."
        else:
            current_app.logger.warning(f"Parcel deposited but notification failed: {notification_message}")
            return parcel, f"Parcel deposited in locker {locker.id}. Note: Email notification may have failed."
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning locker and creating parcel: {str(e)}")
        return None, "An error occurred while processing the deposit."

def process_pickup(provided_pin: str):
    from app.application.services import log_audit_event
    try:
        # Find parcel with matching PIN
        parcels = Parcel.query.filter_by(status='deposited').all()
        
        for parcel in parcels:
            if PinManager.verify_pin(parcel.pin_hash, provided_pin):
                # Check if PIN has expired
                if PinManager.is_pin_expired(parcel.otp_expiry):
                    # Log the expired PIN attempt
                    log_audit_event("USER_PICKUP_FAIL_PIN_EXPIRED", details={
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
                    # Only set to free if not out of service
                    if locker.status != 'out_of_service':
                        locker.status = 'free'
                    # If it was out of service, leave it as out of service
                
                db.session.commit()
                
                # Log the pickup
                log_audit_event(f"Parcel {parcel.id} picked up from locker {parcel.locker_id}", "pickup")
                
                return parcel, f"Parcel successfully picked up from locker {parcel.locker_id}."
        
        # Log the invalid PIN attempt
        log_audit_event("USER_PICKUP_FAIL_INVALID_PIN", details={
            "provided_pin_pattern": provided_pin[:3] + "XXX",
            "reason": "No matching deposited parcel found"
        })
        
        return None, "Invalid PIN or no matching parcel found."
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing pickup: {str(e)}")
        return None, "An error occurred while processing the pickup."

def retract_deposit(parcel_id: int):
    from app.application.services import log_audit_event
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

def dispute_pickup(parcel_id: int):
    from app.application.services import log_audit_event
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

def report_parcel_missing_by_recipient(parcel_id: int):
    from app.application.services import log_audit_event
    try:
        parcel = db.session.get(Parcel, parcel_id)
        if not parcel:
            return None, "Parcel not found."
        if parcel.status not in ['deposited', 'pickup_disputed']:
            return None, f"Parcel cannot be reported missing by recipient from its current state: '{parcel.status}'."
        original_parcel_status = parcel.status
        parcel.status = 'missing'
        locker = db.session.get(Locker, parcel.locker_id)
        if not locker:
            current_app.logger.error(f"Data inconsistency: Locker ID {parcel.locker_id} not found for parcel {parcel.id} during recipient missing report.")
        else:
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
    """Admin function to mark a parcel as missing"""
    from app.application.services import log_audit_event
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

def process_overdue_parcels():
    from app.application.services import log_audit_event
    max_pickup_days = current_app.config.get('PARCEL_MAX_PICKUP_DAYS', 7)
    deposited_parcels = Parcel.query.filter(
        Parcel.status == 'deposited',
        Parcel.deposited_at.isnot(None)
    ).all()
    processed_count = 0
    items_to_update_in_session = []
    for parcel in deposited_parcels:
        if not isinstance(parcel.deposited_at, datetime):
            log_audit_event("PROCESS_OVERDUE_FAIL_INVALID_DEPOSITED_AT", {
                "parcel_id": parcel.id, 
                "deposited_at_type": str(type(parcel.deposited_at)),
                "reason": "Parcel has invalid or missing deposited_at timestamp."
            })
            continue
        if datetime.utcnow() > parcel.deposited_at + timedelta(days=max_pickup_days):
            try:
                locker = parcel.locker
                if not locker:
                    log_audit_event("PROCESS_OVERDUE_FAIL_NO_LOCKER", {
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
                log_audit_event("PARCEL_MARKED_RETURN_TO_SENDER", {
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
                log_audit_event("PROCESS_OVERDUE_PARCEL_ERROR", {
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
            log_audit_event("PROCESS_OVERDUE_BATCH_COMMIT_ERROR", {
                "error": str(e), 
                "num_parcels_intended_for_update_in_batch": processed_count
            })
            return 0, f"Error committing batch of overdue parcels: {str(e)}"
    return processed_count, f"{processed_count} overdue parcels processed." 