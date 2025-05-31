from app import db # Will be removed once LockerRepository is fully integrated
from app.business.locker import Locker as BusinessLocker # Assuming this is the business object
from app.persistence.models import Locker as PersistenceLocker, Parcel as PersistenceParcel
from app.persistence.repositories.locker_repository import LockerRepository
from app.persistence.repositories.parcel_repository import ParcelRepository as PclRepo # Alias to avoid confusion
from app.services.audit_service import AuditService
from flask import current_app
from datetime import datetime # Added for missing parcel reference date
import datetime as dt
from typing import List, Dict, Any # Added for type hinting

# FR-08: Out of Service - Admin locker status management
def set_locker_status(admin_id: int, admin_username: str, locker_id: int, new_status: str):
    if new_status not in ['out_of_service', 'free', 'occupied']:
        return None, "Invalid target status specified. Allowed: 'out_of_service', 'free', 'occupied'."
    
    locker = LockerRepository.get_by_id(locker_id)
    if not locker:
        return None, "Locker not found."
    
    old_status = locker.status
    if old_status == new_status:
        return locker, "Locker is already in the requested state."
    
    parcels_to_update_in_session = []

    try:
        if new_status == 'out_of_service':
            locker.status = 'out_of_service'
        elif new_status == 'free':
            # Use ParcelRepository for these checks
            disputed_parcel = PclRepo.get_all_by_locker_id_and_status(locker_id, 'pickup_disputed')
            if disputed_parcel: # Check if list is not empty
                return None, f"Cannot set locker to 'free'. Parcel ID {disputed_parcel[0].id} associated with this locker has a 'pickup_disputed' status. Please resolve the dispute."
            
            if old_status not in ['out_of_service', 'maintenance']:
                return None, f"Locker must be 'out_of_service' or 'maintenance' to be set to 'free'. Current status: '{old_status}'."
            
            active_parcels = PclRepo.get_all_by_locker_id_and_status(locker_id, 'deposited')
            if active_parcels: # Check if list is not empty
                return None, f"Cannot set locker to 'free'. Parcel ID {active_parcels[0].id} is still marked as 'deposited' in this locker."
            
            missing_parcels = PclRepo.get_all_by_locker_id_and_status(locker_id, 'missing')
            if missing_parcels:
                for missing_parcel in missing_parcels:
                    ref_date = datetime.now(dt.UTC).strftime('%Y%m%d')
                    reference_number = f"MISSING-{missing_parcel.id}-{ref_date}"
                    missing_parcel.locker_id = None
                    # PclRepo.add_to_session(missing_parcel) # Add to a list for batch save later
                    parcels_to_update_in_session.append(missing_parcel)
                    
                    AuditService.log_event("MISSING_PARCEL_DETACHED_FROM_LOCKER", details={
                        "admin_id": admin_id,
                        "admin_username": admin_username,
                        "parcel_id": missing_parcel.id,
                        "locker_id": locker_id,
                        "reference_number": reference_number,
                        "recipient_email_domain": missing_parcel.recipient_email.split('@')[1] if '@' in missing_parcel.recipient_email else 'unknown'
                    })
            locker.status = 'free'
        elif new_status == 'occupied':
            if old_status not in ['out_of_service']:
                return None, f"Locker can only be set to 'occupied' from 'out_of_service'. Current status: '{old_status}'."
            
            active_parcels = PclRepo.get_all_by_locker_id_and_status(locker_id, 'deposited')
            if not active_parcels:
                return None, f"Cannot set locker to 'occupied'. No active parcel found in this locker."
            locker.status = 'occupied'
        
        # Save the locker
        if not LockerRepository.save(locker):
            current_app.logger.error(f"Failed to save locker {locker_id} status via repository.")
            return None, "A database error occurred while updating locker status (locker save)."

        # Save any updated parcels (e.g., detached missing parcels)
        if parcels_to_update_in_session:
            if not PclRepo.save_all(parcels_to_update_in_session):
                current_app.logger.error(f"Failed to save updated parcels for locker {locker_id} via repository.")
                # This is a partial success/failure; locker status might have changed.
                # Decide on overall return status. For now, indicate parcel save issue.
                return locker, "Locker status updated, but failed to save associated parcel changes."

        AuditService.log_event("ADMIN_LOCKER_STATUS_CHANGED", details={
            "locker_id": locker_id,
            "old_status": old_status,
            "new_status": new_status,
            "admin_id": admin_id,
            "admin_username": admin_username
        })
        return locker, None # Success

    except Exception as e:
        # db.session.rollback() # Repositories handle their own rollback on save errors
        current_app.logger.error(f"Error in set_locker_status for locker {locker_id}: {e}")
        return None, "A database error occurred while updating locker status."

def mark_locker_as_emptied(locker_id: int, admin_id: int, admin_username: str):
    locker = LockerRepository.get_by_id(locker_id)
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
    
    if LockerRepository.save(locker):
        AuditService.log_event("LOCKER_MARKED_EMPTIED_AFTER_RETURN", {
            "locker_id": locker_id,
            "admin_id": admin_id,
            "admin_username": admin_username,
            "old_locker_status": old_locker_status,
            "new_locker_status": locker.status
        })
        return locker, "Locker successfully marked as free."
    else:
        # Rollback handled by repository
        current_app.logger.error(f"Error in mark_locker_as_emptied (save failed) for locker {locker_id}")
        AuditService.log_event("MARK_LOCKER_EMPTIED_ERROR_REPO_SAVE", {
            "locker_id": locker_id, 
            "admin_id": admin_id,
            "admin_username": admin_username,
            "error": "LockerRepository.save failed"
        })
        return locker, f"Database error marking locker as emptied (save failed)." 

def get_all_lockers_with_parcel_counts() -> List[Dict[str, Any]]:
    """
    Retrieves all lockers with their associated parcels for the admin dashboard.
    Returns a list of dictionaries, where each dictionary contains locker and parcel objects.
    """
    lockers_data = []
    try:
        all_persistence_lockers = LockerRepository.get_all()
        for p_locker in all_persistence_lockers:
            # Get parcels in various relevant statuses for this locker
            # Include deposited, missing, pickup_disputed, and other non-final statuses
            relevant_statuses = ['deposited', 'missing', 'pickup_disputed']
            associated_parcel = None
            
            for status in relevant_statuses:
                parcels = PclRepo.get_all_by_locker_id_and_status(p_locker.id, status)
                if parcels:
                    associated_parcel = parcels[0]  # Take the first one found
                    break
            
            lockers_data.append({
                "locker": p_locker,
                "parcel": associated_parcel
            })
        return lockers_data
    except Exception as e:
        current_app.logger.error(f"Error in get_all_lockers_with_parcel_counts: {str(e)}")
        return [] # Return empty list on error 

def generate_reference_number(self, parcel_id):
    """Generate a reference number for tracking purposes"""
    ref_date = datetime.now(dt.UTC).strftime('%Y%m%d')
    return f"PKG-{parcel_id:06d}-{ref_date}" 