from app import db
from datetime import datetime
import bcrypt # Added bcrypt import
from app.business.parcel import Parcel
from app.business.locker import Locker

# Locker is only imported, not redefined here.

class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # bcrypt hash
    last_login = db.Column(db.DateTime, nullable=True)  # Track last login time

    def set_password(self, password):
        # Ensure password is bytes for bcrypt
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8') # Store as string

    def check_password(self, password):
        # Ensure password is bytes for bcrypt
        password_bytes = password.encode('utf-8')
        # Ensure stored hash is bytes for bcrypt
        stored_hash = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, stored_hash)

    def __repr__(self):
        return f'<AdminUser {self.username}>'

class AuditLog(db.Model):
    """
    SIMPLIFIED Audit Log - Essential fields only for test environment
    Tracks WHO did WHAT and WHEN with contextual details
    """
    __tablename__ = 'audit_log'
    __bind_key__ = 'audit'

    # ✅ ESSENTIAL FIELDS ONLY
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    action = db.Column(db.String(255), nullable=False)  # What happened
    details = db.Column(db.Text, nullable=True)  # JSON context/specifics
    admin_id = db.Column(db.Integer, nullable=True)  # WHO did it (ID)
    admin_username = db.Column(db.String(80), nullable=True)  # WHO did it (readable)
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action} by {self.admin_username} at {self.timestamp}>'

class LockerSensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    locker_id = db.Column(db.Integer, db.ForeignKey('locker.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    has_contents = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f'<LockerSensorData {self.locker_id}: {self.has_contents} at {self.timestamp}>'
