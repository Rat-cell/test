# PIN domain business rules and logic
import hashlib
import os
from datetime import datetime, timedelta

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
        return datetime.utcnow() > otp_expiry
    
    @staticmethod
    def generate_expiry_time(hours=24):
        """Generate expiry time for a PIN (default 24 hours from now)"""
        return datetime.utcnow() + timedelta(hours=hours) 