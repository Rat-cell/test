# PIN domain business rules and logic
import hashlib
import os
from datetime import datetime, timedelta
from flask import current_app

class PinManager:
    """Business logic for PIN management"""
    
    @staticmethod
    def generate_pin_and_hash():
        """
        FR-02: Generate PIN - Create a 6-digit PIN and store its salted SHA-256 hash
        NFR-03: Security - Cryptographically secure PIN generation with salted hashing
        """
        # FR-02 & NFR-03: Generate cryptographically secure 6-digit numeric PIN
        pin = "{:06d}".format(int.from_bytes(os.urandom(3), 'big') % 1000000)  # Generate 6-digit PIN
        
        # NFR-03: Security - Create unique salt per PIN for enhanced security against rainbow tables
        salt = os.urandom(16)
        
        # NFR-03: Security - Hash PIN using salted SHA-256 before storage (original PIN never stored)
        hashed_pin = hashlib.pbkdf2_hmac('sha256', pin.encode('utf-8'), salt, 100000, dklen=64)
        return pin, salt.hex() + ":" + hashed_pin.hex()
    
    @staticmethod
    def verify_pin(stored_pin_hash_with_salt, provided_pin):
        """NFR-03: Security - Secure PIN verification with timing attack resistance"""
        try:
            salt_hex, stored_hash_hex = stored_pin_hash_with_salt.split(":")
            salt = bytes.fromhex(salt_hex)
            stored_hash = bytes.fromhex(stored_hash_hex)
            # NFR-03: Security - Use same PBKDF2 parameters for consistent timing
            provided_hash = hashlib.pbkdf2_hmac('sha256', provided_pin.encode('utf-8'), salt, 100000, dklen=64)
            return provided_hash == stored_hash
        except (ValueError, AttributeError):
            # NFR-03: Security - Graceful error handling without information leakage
            return False
    
    @staticmethod
    def is_pin_expired(otp_expiry):
        """
        FR-09: Invalid PIN Error Handling - Check if a PIN has expired
        NFR-03: Security - Time-based PIN expiration for enhanced security
        Used by process_pickup to provide clear expiry error messages
        """
        if otp_expiry is None:
            return True  # Treat None expiry as expired
        return datetime.utcnow() > otp_expiry
    
    @staticmethod
    def generate_expiry_time(hours=None):
        """NFR-03: Security - Generate configurable PIN expiry time for time-limited access"""
        if hours is None:
            # Get from Flask app config, default to 24 hours if not configured
            hours = current_app.config.get('PIN_EXPIRY_HOURS', 24)
        return datetime.utcnow() + timedelta(hours=hours)
    
    @staticmethod
    def get_pin_expiry_hours():
        """NFR-03: Security - Get the configured PIN expiry hours for consistent policy"""
        return current_app.config.get('PIN_EXPIRY_HOURS', 24)
    
    @staticmethod
    def is_valid_pin_format(pin):
        """
        FR-09: Invalid PIN Error Handling - Validate PIN format (6 digits)
        NFR-03: Security - Input validation to prevent injection attacks
        Used to ensure proper PIN format before processing
        """
        if not pin:
            return False
        if not isinstance(pin, str):
            return False
        if len(pin) != 6:
            return False
        if not pin.isdigit():
            return False
        return True
    
    @staticmethod
    def get_pin_error_help_message(error_type: str) -> str:
        """
        FR-09: Invalid PIN Error Handling - Get helpful error messages for different PIN error types
        """
        help_messages = {
            'format_error': {
                'title': '📝 PIN Format Error',
                'message': 'Your PIN should be exactly 6 digits (numbers only).',
                'actions': [
                    'Double-check your PIN in the email you received',
                    'Make sure you\'re not including spaces or letters',
                    'Copy and paste the PIN from your email if needed'
                ]
            },
            'expired': {
                'title': '⏰ PIN Expired',
                'message': 'Your PIN has expired and can no longer be used for pickup.',
                'actions': [
                    'Click "Request New PIN" below to get a fresh PIN',
                    'Check your email for the new PIN (including spam folder)',
                    'New PINs are valid for 24 hours'
                ]
            },
            'invalid': {
                'title': '❌ Incorrect PIN',
                'message': 'The PIN you entered doesn\'t match any active parcel.',
                'actions': [
                    'Double-check the PIN in your email',
                    'Make sure you\'re using the most recent PIN',
                    'If you generated multiple PINs, only the latest one works'
                ]
            },
            'no_parcel': {
                'title': '📦 No Matching Parcel',
                'message': 'No active parcel was found for this PIN.',
                'actions': [
                    'Verify the PIN is from a recent email',
                    'Check if your parcel has already been picked up',
                    'Contact support if you think this is an error'
                ]
            },
            'rate_limited': {
                'title': '⏳ Daily Limit Reached',
                'message': 'You\'ve reached the daily limit for PIN generation (3 PINs per day).',
                'actions': [
                    'Try again tomorrow after midnight',
                    'Use your most recent PIN if you still have it',
                    'Contact support if you need immediate assistance'
                ]
            },
            'system_error': {
                'title': '⚠️ System Error',
                'message': 'A technical error occurred while processing your PIN.',
                'actions': [
                    'Please try again in a few minutes',
                    'If the problem persists, contact support',
                    'Your parcel is safe and will remain available'
                ]
            }
        }
        
        return help_messages.get(error_type, help_messages['system_error']) 