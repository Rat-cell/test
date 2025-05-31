from datetime import datetime
import datetime as dt
# from app import db # db import no longer needed here for model definition
# import secrets # Moved to Parcel model in models.py
import re # Used by ParcelManager.is_valid_email
from app.business.pin import PinManager

# --- Parcel SQLAlchemy Model definition and its methods (generate_pin_token, etc.) moved to app/persistence/models.py --- 
# class Parcel(db.Model):
#     ...

class ParcelManager:
    """Business logic for parcel management"""
    
    # Valid parcel statuses
    VALID_STATUSES = [
        'deposited', 'picked_up', 'missing', 'expired', 
        'retracted_by_sender', 'pickup_disputed', 
        'awaiting_return', 'return_to_sender'
    ]
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email address format"""
        if not email or not isinstance(email, str):
            return False
        
        # Basic email validation pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_status(status: str) -> bool:
        """Validate parcel status"""
        return status in ParcelManager.VALID_STATUSES
    
    @staticmethod
    def can_transition_status(current_status: str, new_status: str) -> bool:
        """Business rules for status transitions"""
        valid_transitions = {
            'deposited': ['picked_up', 'missing', 'retracted_by_sender', 'return_to_sender', 'pickup_disputed'],
            'picked_up': ['pickup_disputed'],
            'pickup_disputed': ['missing', 'picked_up'],
            'missing': [],  # Terminal state
            'retracted_by_sender': [],  # Terminal state
            'return_to_sender': [],  # Terminal state
            'expired': ['return_to_sender'],
            'awaiting_return': ['return_to_sender']
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    @staticmethod
    def get_parcel_age_days(deposited_at: datetime) -> int:
        """Calculate age of parcel in days"""
        if not deposited_at:
            return 0
        return (datetime.now(dt.UTC) - deposited_at).days
    
    @staticmethod
    def is_overdue(deposited_at: datetime, max_pickup_days: int) -> bool:
        """Check if parcel is overdue for pickup"""
        return ParcelManager.get_parcel_age_days(deposited_at) > max_pickup_days 