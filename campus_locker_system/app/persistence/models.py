from app import db
from datetime import datetime
import bcrypt # Added bcrypt import

class Locker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(50), nullable=False)  # e.g., 'small', 'medium', 'large'
    status = db.Column(db.String(50), nullable=False, default='free')  # e.g., 'free', 'occupied', 'out_of_service'
    parcels = db.relationship('Parcel', backref='locker', lazy=True)

    def __repr__(self):
        return f'<Locker {self.id} ({self.size}) - {self.status}>'

class Parcel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    locker_id = db.Column(db.Integer, db.ForeignKey('locker.id'), nullable=False)
    pin_hash = db.Column(db.String(128), nullable=False)  # SHA-256 hash
    otp_expiry = db.Column(db.DateTime, nullable=False)
    recipient_email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='deposited')  # e.g., 'deposited', 'picked_up', 'missing', 'expired'

    def __repr__(self):
        return f'<Parcel {self.id} in Locker {self.locker_id} - Status: {self.status}>'

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # bcrypt hash

    def set_password(self, password):
        # Ensure password is bytes for bcrypt
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8') # Store as string

    def check_password(self, password):
        password_bytes = password.encode('utf-8')
        if self.password_hash:
            stored_hash_bytes = self.password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, stored_hash_bytes)
        return False

    def __repr__(self):
        return f'<AdminUser {self.username}>'

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    action = db.Column(db.String(120), nullable=False)
    details = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<AuditLog {self.id} [{self.timestamp}] - {self.action}>'
