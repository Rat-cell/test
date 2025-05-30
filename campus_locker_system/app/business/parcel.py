from datetime import datetime
from app import db
import secrets
import re

class Parcel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    locker_id = db.Column(db.Integer, db.ForeignKey('locker.id'), nullable=False)
    pin_hash = db.Column(db.String(128), nullable=True)  # SHA-256 hash - now nullable for email-based PIN generation
    otp_expiry = db.Column(db.DateTime, nullable=True)  # Now nullable for email-based PIN generation
    recipient_email = db.Column(db.String(120), nullable=False)
    # Possible statuses: 'deposited', 'picked_up', 'missing', 'expired', 'retracted_by_sender', 'pickup_disputed', 'awaiting_return', 'return_to_sender'
    status = db.Column(db.String(50), nullable=False, default='deposited')
    deposited_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # New field
    picked_up_at = db.Column(db.DateTime, nullable=True)  # Pickup timestamp
    
    # Email-based PIN generation fields
    pin_generation_token = db.Column(db.String(128), nullable=True)  # Unique token for PIN generation
    pin_generation_token_expiry = db.Column(db.DateTime, nullable=True)  # Token expiry time
    pin_generation_count = db.Column(db.Integer, nullable=False, default=0)  # Track PIN generation attempts
    last_pin_generation = db.Column(db.DateTime, nullable=True)  # Last PIN generation timestamp
    
    # FR-04: Send Reminder After 24h of Occupancy - Track reminder sent status
    reminder_sent_at = db.Column(db.DateTime, nullable=True)  # When the 24h reminder was sent

    def __repr__(self):
        return f'<Parcel {self.id} in Locker {self.locker_id} - Status: {self.status}>'
    
    def generate_pin_token(self):
        """Generate a secure token for PIN generation"""
        self.pin_generation_token = secrets.token_urlsafe(32)
        # Token expires in 24 hours by default
        from datetime import timedelta
        from flask import current_app
        expiry_hours = current_app.config.get('PIN_GENERATION_TOKEN_EXPIRY_HOURS', 24)
        self.pin_generation_token_expiry = datetime.utcnow() + timedelta(hours=expiry_hours)
        return self.pin_generation_token
    
    def is_pin_token_valid(self):
        """Check if the PIN generation token is still valid"""
        if not self.pin_generation_token or not self.pin_generation_token_expiry:
            return False
        return datetime.utcnow() < self.pin_generation_token_expiry
    
    def can_generate_pin(self, max_daily_generations: int):
        """Check if user can generate another PIN today"""
        if not self.last_pin_generation:
            return True
        
        # Check if it's been a day since last generation
        if (datetime.utcnow() - self.last_pin_generation).days >= 1:
            # Reset count for new day
            self.pin_generation_count = 0
            return True
        
        return self.pin_generation_count < max_daily_generations


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
        return (datetime.utcnow() - deposited_at).days
    
    @staticmethod
    def is_overdue(deposited_at: datetime, max_pickup_days: int) -> bool:
        """Check if parcel is overdue for pickup"""
        return ParcelManager.get_parcel_age_days(deposited_at) > max_pickup_days 