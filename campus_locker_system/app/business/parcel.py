from datetime import datetime
from app import db

class Parcel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    locker_id = db.Column(db.Integer, db.ForeignKey('locker.id'), nullable=False)
    pin_hash = db.Column(db.String(128), nullable=False)  # SHA-256 hash
    otp_expiry = db.Column(db.DateTime, nullable=False)
    recipient_email = db.Column(db.String(120), nullable=False)
    # Possible statuses: 'deposited', 'picked_up', 'missing', 'expired', 'retracted_by_sender', 'pickup_disputed', 'awaiting_return', 'return_to_sender'
    status = db.Column(db.String(50), nullable=False, default='deposited')
    deposited_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) # New field

    def __repr__(self):
        return f'<Parcel {self.id} in Locker {self.locker_id} - Status: {self.status}>'

def is_valid_parcel_status(status: str) -> bool:
    allowed_statuses = {
        'deposited', 'picked_up', 'missing', 'expired',
        'retracted_by_sender', 'pickup_disputed', 'awaiting_return', 'return_to_sender'
    }
    return status in allowed_statuses 