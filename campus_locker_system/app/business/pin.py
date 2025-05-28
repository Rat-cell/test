# PIN domain business rules and logic
import hashlib
import os
from datetime import datetime, timedelta
from flask import current_app

class PinManager:
    """Business logic for PIN management"""
    
    @staticmethod
    def generate_pin_and_hash():
        """Generate a 6-digit PIN and return both plain PIN and salted hash"""
        pin = "{:06d}".format(int.from_bytes(os.urandom(3), 'big') % 1000000)  # Generate 6-digit PIN
        salt = os.urandom(16)
        hashed_pin = hashlib.pbkdf2_hmac('sha256', pin.encode('utf-8'), salt, 100000, dklen=64)
        return pin, salt.hex() + ":" + hashed_pin.hex()
    
    @staticmethod
    def verify_pin(stored_pin_hash_with_salt, provided_pin):
        """Verify a provided PIN against the stored hash"""
        try:
            salt_hex, stored_hash_hex = stored_pin_hash_with_salt.split(":")
            salt = bytes.fromhex(salt_hex)
            stored_hash = bytes.fromhex(stored_hash_hex)
            provided_hash = hashlib.pbkdf2_hmac('sha256', provided_pin.encode('utf-8'), salt, 100000, dklen=64)
            return provided_hash == stored_hash
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def is_pin_expired(otp_expiry):
        """Check if a PIN has expired"""
        if otp_expiry is None:
            return True  # Treat None expiry as expired
        return datetime.utcnow() > otp_expiry
    
    @staticmethod
    def generate_expiry_time(hours=None):
        """Generate expiry time for a PIN using configurable hours from app config"""
        if hours is None:
            # Get from Flask app config, default to 24 hours if not configured
            hours = current_app.config.get('PIN_EXPIRY_HOURS', 24)
        return datetime.utcnow() + timedelta(hours=hours)
    
    @staticmethod
    def get_pin_expiry_hours():
        """Get the configured PIN expiry hours from app config"""
        return current_app.config.get('PIN_EXPIRY_HOURS', 24)
    
    @staticmethod
    def is_valid_pin_format(pin):
        """Validate PIN format (6 digits)"""
        if not pin:
            return False
        if not isinstance(pin, str):
            return False
        if len(pin) != 6:
            return False
        if not pin.isdigit():
            return False
        return True 