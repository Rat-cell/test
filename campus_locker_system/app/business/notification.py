# Notification domain business rules and logic
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import Enum

class NotificationType(Enum):
    """Types of notifications supported by the system"""
    PARCEL_DEPOSIT = "parcel_deposit"
    PIN_REISSUE = "pin_reissue"
    PIN_REGENERATION = "pin_regeneration"
    OVERDUE_NOTICE = "overdue_notice"
    PICKUP_CONFIRMATION = "pickup_confirmation"

@dataclass
class EmailTemplate:
    """Business object representing an email template"""
    subject: str
    body: str
    notification_type: NotificationType
    
    def format_with_data(self, data: dict) -> 'FormattedEmail':
        """Apply template data to create a formatted email"""
        formatted_subject = self.subject.format(**data)
        formatted_body = self.body.format(**data)
        return FormattedEmail(
            subject=formatted_subject,
            body=formatted_body,
            notification_type=self.notification_type
        )

@dataclass
class FormattedEmail:
    """Business object representing a formatted email ready to send"""
    subject: str
    body: str
    notification_type: NotificationType

class NotificationManager:
    """Business logic for notification management"""
    
    # Email templates defined as business rules
    TEMPLATES = {
        NotificationType.PARCEL_DEPOSIT: EmailTemplate(
            subject="Parcel Deposited - Pickup PIN",
            body="Your parcel has been deposited in locker {locker_id}.\nPickup PIN: {pin}\nExpires: {expiry_time}",
            notification_type=NotificationType.PARCEL_DEPOSIT
        ),
        NotificationType.PIN_REISSUE: EmailTemplate(
            subject="New Pickup PIN for Parcel #{parcel_id}",
            body="Your new pickup PIN is: {pin}\nLocker ID: {locker_id}\nExpires: {expiry_time}",
            notification_type=NotificationType.PIN_REISSUE
        ),
        NotificationType.PIN_REGENERATION: EmailTemplate(
            subject="New Pickup PIN for Parcel #{parcel_id}",
            body="Your new pickup PIN is: {pin}\nLocker ID: {locker_id}\nExpires: {expiry_time}",
            notification_type=NotificationType.PIN_REGENERATION
        )
    }
    
    @classmethod
    def create_parcel_deposit_email(cls, parcel_id: int, locker_id: int, pin: str, expiry_time: datetime) -> FormattedEmail:
        """Create email for parcel deposit notification"""
        template = cls.TEMPLATES[NotificationType.PARCEL_DEPOSIT]
        data = {
            'parcel_id': parcel_id,
            'locker_id': locker_id,
            'pin': pin,
            'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
        }
        return template.format_with_data(data)
    
    @classmethod
    def create_pin_reissue_email(cls, parcel_id: int, locker_id: int, pin: str, expiry_time: datetime) -> FormattedEmail:
        """Create email for PIN reissue notification"""
        template = cls.TEMPLATES[NotificationType.PIN_REISSUE]
        data = {
            'parcel_id': parcel_id,
            'locker_id': locker_id,
            'pin': pin,
            'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
        }
        return template.format_with_data(data)
    
    @classmethod
    def create_pin_regeneration_email(cls, parcel_id: int, locker_id: int, pin: str, expiry_time: datetime) -> FormattedEmail:
        """Create email for PIN regeneration notification"""
        template = cls.TEMPLATES[NotificationType.PIN_REGENERATION]
        data = {
            'parcel_id': parcel_id,
            'locker_id': locker_id,
            'pin': pin,
            'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
        }
        return template.format_with_data(data)
    
    @staticmethod
    def validate_email_address(email: str) -> bool:
        """Basic email validation business rule"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_delivery_allowed(recipient_email: str) -> bool:
        """Business rule to determine if email delivery is allowed"""
        # Basic validation - can be extended for blacklists, rate limiting, etc.
        if not NotificationManager.validate_email_address(recipient_email):
            return False
        
        # Add additional business rules here (e.g., check blocklist, rate limits)
        return True 