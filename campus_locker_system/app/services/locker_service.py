from app import db
from app.business.locker import Locker
from app.business.parcel import Parcel
from app.services.audit_service import AuditService
from flask import current_app

# FR-08: Out of Service - Admin locker status management
def set_locker_status(admin_id: int, admin_username: str, locker_id: int, new_status: str):
    # FR-08: Allow out_of_service, free, and occupied status changes for maintenance
    if new_status not in ['out_of_service', 'free', 'occupied']:
        return None, "Invalid target status specified. Allowed: 'out_of_service', 'free', 'occupied'."
    locker = db.session.get(Locker, locker_id)
    if not locker:
        return None, "Locker not found."
    old_status = locker.status
    if old_status == new_status:
        return locker, "Locker is already in the requested state."
    try:
        if new_status == 'out_of_service':
            # FR-08: Disable locker to skip during assignment
            locker.status = 'out_of_service'
        elif new_status == 'free':
            disputed_parcel = Parcel.query.filter_by(locker_id=locker_id, status='pickup_disputed').first()
            if disputed_parcel:
                return None, f"Cannot set locker to 'free'. Parcel ID {disputed_parcel.id} associated with this locker has a 'pickup_disputed' status. Please resolve the dispute."
            if old_status not in ['out_of_service', 'maintenance']:
                return None, f"Locker must be 'out_of_service' or 'maintenance' to be set to 'free'. Current status: '{old_status}'."
            active_parcel = Parcel.query.filter_by(locker_id=locker_id, status='deposited').first()
            if active_parcel:
                return None, f"Cannot set locker to 'free'. Parcel ID {active_parcel.id} is still marked as 'deposited' in this locker."
            
            # Handle missing parcels - detach them from locker but keep record
            missing_parcels = Parcel.query.filter_by(locker_id=locker_id, status='missing').all()
            if missing_parcels:
                from datetime import datetime
                for missing_parcel in missing_parcels:
                    # Generate reference number for tracking
                    ref_date = datetime.utcnow().strftime('%Y%m%d')
                    reference_number = f"MISSING-{missing_parcel.id}-{ref_date}"
                    
                    # Detach parcel from locker but keep the record
                    missing_parcel.locker_id = None
                    db.session.add(missing_parcel)
                    
                    # Log the detachment for audit trail
                    AuditService.log_event("MISSING_PARCEL_DETACHED_FROM_LOCKER", details={
                        "admin_id": admin_id,
                        "admin_username": admin_username,
                        "parcel_id": missing_parcel.id,
                        "locker_id": locker_id,
                        "reference_number": reference_number,
                        "recipient_email_domain": missing_parcel.recipient_email.split('@')[1] if '@' in missing_parcel.recipient_email else 'unknown'
                    })
            
            # FR-08: Return locker to service after maintenance
            locker.status = 'free'
        elif new_status == 'occupied':
            # Allow transition from out_of_service to occupied if there's an active parcel
            if old_status not in ['out_of_service']:
                return None, f"Locker can only be set to 'occupied' from 'out_of_service'. Current status: '{old_status}'."
            active_parcel = Parcel.query.filter_by(locker_id=locker_id, status='deposited').first()
            if not active_parcel:
                return None, f"Cannot set locker to 'occupied'. No active parcel found in this locker."
            locker.status = 'occupied'
        db.session.add(locker)
        db.session.commit()
        
        # FR-07: Audit Trail - Record admin override action with timestamp and admin identity
        # FR-08: Log locker status changes for maintenance tracking
        AuditService.log_event("ADMIN_LOCKER_STATUS_CHANGED", details={
            "locker_id": locker_id,
            "old_status": old_status,
            "new_status": new_status,
            "admin_id": admin_id,
            "admin_username": admin_username
        })
        return locker, None
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in set_locker_status for locker {locker_id}: {e}")
        return None, "A database error occurred while updating locker status."

def mark_locker_as_emptied(locker_id: int, admin_id: int, admin_username: str):
    locker = db.session.get(Locker, locker_id)
    if not locker:
        AuditService.log_event("MARK_LOCKER_EMPTIED_FAIL", {"locker_id": locker_id, "admin_id": admin_id, "admin_username": admin_username, "reason": "Locker not found."})
        return None, "Locker not found."
    if locker.status != 'awaiting_collection':
        AuditService.log_event("MARK_LOCKER_EMPTIED_FAIL", {
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
        db.session.add(locker)
        db.session.commit()
        AuditService.log_event("LOCKER_MARKED_EMPTIED_AFTER_RETURN", {
            "locker_id": locker_id,
            "admin_id": admin_id,
            "admin_username": admin_username,
            "old_locker_status": old_locker_status,
            "new_locker_status": locker.status
        })
        return locker, "Locker successfully marked as free."
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in mark_locker_as_emptied for locker {locker_id}: {str(e)}")
        AuditService.log_event("MARK_LOCKER_EMPTIED_ERROR", {
            "locker_id": locker_id, 
            "admin_id": admin_id,
            "admin_username": admin_username,
            "error": str(e)
        })
        return locker, f"Database error marking locker as emptied: {str(e)}" 