from app import db
from datetime import datetime
import bcrypt # Added bcrypt import
# Removed imports of Parcel and Locker from business layer, as they will be defined here.
# from app.business.parcel import Parcel 
# from app.business.locker import Locker

# --- Locker Model Definition ---
class Locker(db.Model):
    __tablename__ = 'locker' # Explicit table name is good practice
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)  # Physical location of the locker
    size = db.Column(db.String(50), nullable=False)  # e.g., 'small', 'medium', 'large'
    # Possible statuses: 'free', 'occupied', 'out_of_service', 'disputed_contents', 'awaiting_collection'
    status = db.Column(db.String(50), nullable=False, default='free')
    parcels = db.relationship('Parcel', backref='locker', lazy=True)
    # Relationship to LockerSensorData (one-to-many)
    sensor_data = db.relationship('LockerSensorData', backref='locker_info', lazy='dynamic')

    def __repr__(self):
        return f'<Locker {self.id} at {self.location} ({self.size}) - {self.status}>'

# --- Parcel Model Definition ---
class Parcel(db.Model):
    __tablename__ = 'parcel' # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    locker_id = db.Column(db.Integer, db.ForeignKey('locker.id'), nullable=True)  # Allow null for detached missing parcels
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
        """Generate a secure token for PIN generation. Moved from business.parcel for model cohesion."""
        import secrets # Keep import local if only used here
        from datetime import timedelta # Keep import local
        from flask import current_app # Keep import local

        self.pin_generation_token = secrets.token_urlsafe(32)
        expiry_hours = current_app.config.get('PIN_GENERATION_TOKEN_EXPIRY_HOURS', 24)
        self.pin_generation_token_expiry = datetime.utcnow() + timedelta(hours=expiry_hours)
        return self.pin_generation_token
    
    def is_pin_token_valid(self):
        """Check if the PIN generation token is still valid. Moved from business.parcel."""
        if not self.pin_generation_token or not self.pin_generation_token_expiry:
            return False
        return datetime.utcnow() < self.pin_generation_token_expiry
    
    def can_generate_pin(self, max_daily_generations: int):
        """Check if user can generate another PIN today. Moved from business.parcel."""
        if not self.last_pin_generation:
            return True
        # Check if it's been a day since last generation
        if (datetime.utcnow() - self.last_pin_generation).days >= 1:
            self.pin_generation_count = 0 # Reset count for new day
            return True
        return self.pin_generation_count < max_daily_generations

# --- AdminUser Model Definition ---
class AdminUser(db.Model):
    __tablename__ = 'admin_user' # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # bcrypt hash
    last_login = db.Column(db.DateTime, nullable=True)  # Track last login time

    def set_password(self, password):
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def check_password(self, password):
        password_bytes = password.encode('utf-8')
        stored_hash = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, stored_hash)

    def __repr__(self):
        return f'<AdminUser {self.username}>'

# --- AuditLog Model Definition ---
class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    __bind_key__ = 'audit'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    admin_id = db.Column(db.Integer, nullable=True)
    admin_username = db.Column(db.String(80), nullable=True)
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.action} by {self.admin_username} at {self.timestamp}>'

# --- LockerSensorData Model Definition ---
class LockerSensorData(db.Model):
    __tablename__ = 'locker_sensor_data' # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    locker_id = db.Column(db.Integer, db.ForeignKey('locker.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    has_contents = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f'<LockerSensorData {self.locker_id}: {self.has_contents} at {self.timestamp}>'
