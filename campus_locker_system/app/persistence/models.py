from app import db
from datetime import datetime, timedelta
import datetime as dt
import bcrypt # Added bcrypt import
import uuid
from sqlalchemy import TypeDecorator, DateTime
# Removed imports of Parcel and Locker from business layer, as they will be defined here.
# from app.business.parcel import Parcel 
# from app.business.locker import Locker

# --- UTC DateTime Type for Proper Timezone Handling ---
class UTCDateTime(TypeDecorator):
    """
    Custom SQLAlchemy type for proper UTC timezone handling
    Follows hexagonal architecture: Persistence layer handles data conversion
    """
    impl = DateTime
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        """Convert timezone-aware datetime to naive UTC for storage"""
        if value is not None:
            if value.tzinfo is not None:
                # Convert to UTC and make naive for storage
                value = value.utctimetuple()
                value = datetime(*value[:6])
        return value
    
    def process_result_value(self, value, dialect):
        """Convert stored naive datetime back to timezone-aware UTC"""
        if value is not None:
            # Assume stored datetime is UTC and make it timezone-aware
            value = value.replace(tzinfo=dt.timezone.utc)
        return value

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
    otp_expiry = db.Column(UTCDateTime, nullable=True)  # Now nullable for email-based PIN generation
    recipient_email = db.Column(db.String(120), nullable=False)
    # Possible statuses: 'deposited', 'picked_up', 'missing', 'expired', 'retracted_by_sender', 'pickup_disputed', 'awaiting_return', 'return_to_sender'
    status = db.Column(db.String(50), nullable=False, default='deposited')
    deposited_at = db.Column(UTCDateTime, nullable=False, default=datetime.now(dt.UTC)) # New field
    picked_up_at = db.Column(UTCDateTime, nullable=True)  # Pickup timestamp
    
    # Email-based PIN generation fields
    pin_generation_token = db.Column(db.String(128), nullable=True)  # Unique token for PIN generation
    pin_generation_token_expiry = db.Column(UTCDateTime, nullable=True)  # Token expiry time
    pin_generation_count = db.Column(db.Integer, nullable=False, default=0)  # Track PIN generation attempts
    last_pin_generation = db.Column(UTCDateTime, nullable=True)  # Last PIN generation timestamp
    
    # FR-04: Send Reminder After 24h of Occupancy - Track reminder sent status
    reminder_sent_at = db.Column(UTCDateTime, nullable=True)  # When the 24h reminder was sent

    def __repr__(self):
        return f'<Parcel {self.id} in Locker {self.locker_id} - Status: {self.status}>'
    
    def generate_pin_token(self, expiry_hours=1):
        """
        Generate new PIN generation token with expiry
        Follows hexagonal architecture: Domain model generates and returns business value
        """
        self.pin_generation_token = str(uuid.uuid4())
        self.pin_generation_token_expiry = datetime.now(dt.UTC) + timedelta(hours=expiry_hours)
        return self.pin_generation_token
    
    def is_pin_token_valid(self):
        """Check if PIN generation token is still valid"""
        if not self.pin_generation_token or not self.pin_generation_token_expiry:
            return False
        return datetime.now(dt.UTC) < self.pin_generation_token_expiry
    
    def can_reissue_pin(self):
        """Check if PIN can be reissued based on business rules"""
        if not self.last_pin_generation:
            return True
        # Allow reissue after 24 hours
        if (datetime.now(dt.UTC) - self.last_pin_generation).days >= 1:
            return True
        return False
    
    def can_generate_pin(self, max_daily_generations: int = 3):
        """
        Domain business rule: Check if PIN generation is allowed based on daily limits
        Follows hexagonal architecture: Business rules contained in domain model
        """
        # If it's a new day, reset is allowed
        if self.last_pin_generation and (datetime.now(dt.UTC) - self.last_pin_generation).days >= 1:
            return True
        # Check if within daily generation limit (handle None values)
        current_count = self.pin_generation_count or 0
        return current_count < max_daily_generations

# --- AdminUser Model Definition ---
class AdminUser(db.Model):
    __tablename__ = 'admin_user' # Explicit table name
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # bcrypt hash
    last_login = db.Column(UTCDateTime, nullable=True)  # Track last login time

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
    timestamp = db.Column(UTCDateTime, nullable=False, default=datetime.now(dt.UTC))
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
    timestamp = db.Column(UTCDateTime, nullable=False, default=datetime.now(dt.UTC))
    has_contents = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f'<LockerSensorData {self.locker_id}: {self.has_contents} at {self.timestamp}>'
