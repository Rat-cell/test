# Notification domain business rules and logic
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import Enum

class NotificationType(Enum):
    """Types of notifications supported by the system"""
    PARCEL_DEPOSIT = "parcel_deposit"
    PARCEL_READY_FOR_PICKUP = "parcel_ready_for_pickup"  # New: Initial notification without PIN
    PIN_GENERATION = "pin_generation"  # New: PIN generated via email link
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
            subject="📦 Parcel Deposited - Pickup PIN",
            body="Your parcel has been deposited in locker {locker_id}.\nPickup PIN: {pin}\nExpires: {expiry_time}",
            notification_type=NotificationType.PARCEL_DEPOSIT
        ),
        NotificationType.PARCEL_READY_FOR_PICKUP: EmailTemplate(
            subject="📦 Your Parcel is Ready for Pickup",
            body="""Hello!

Your parcel has been deposited and is ready for pickup.

PICKUP DETAILS:
• Locker: #{locker_id}
• Deposited: {deposited_time}

GENERATE YOUR PIN:
To get your pickup PIN, click the link below:
{pin_generation_url}

HOW IT WORKS:
1. Click the link above
2. A secure PIN will be generated and emailed to you
3. Use the PIN to open locker #{locker_id}
4. Collect your parcel

IMPORTANT:
• PIN generation link expires in 24 hours
• Each PIN is valid for 24 hours after generation
• You can generate up to 3 PINs per day
• Each new PIN replaces the previous one

Need help? Contact support or visit the pickup location.

Campus Locker System""",
            notification_type=NotificationType.PARCEL_READY_FOR_PICKUP
        ),
        NotificationType.PIN_GENERATION: EmailTemplate(
            subject="🔑 Your Pickup PIN - Locker #{locker_id}",
            body="""Your pickup PIN has been generated!

PICKUP PIN: {pin}

PICKUP DETAILS:
• Locker: #{locker_id}
• PIN expires: {expiry_time}

TO COLLECT YOUR PARCEL:
1. Go to the pickup location
2. Enter PIN: {pin}
3. Open locker #{locker_id}
4. Collect your parcel and close the locker

SECURITY NOTES:
• This PIN is valid for 24 hours only
• Keep your PIN secure and don't share it
• If expired, generate a new PIN using your original email link

Campus Locker System""",
            notification_type=NotificationType.PIN_GENERATION
        ),
        NotificationType.PIN_REISSUE: EmailTemplate(
            subject="🔄 New Pickup PIN - Locker #{locker_id}",
            body="""A new pickup PIN has been issued for your parcel.

PICKUP PIN: {pin}

PICKUP DETAILS:
• Locker: #{locker_id}
• PIN expires: {expiry_time}

This PIN replaces any previous PIN for this parcel.

Campus Locker System""",
            notification_type=NotificationType.PIN_REISSUE
        ),
        NotificationType.PIN_REGENERATION: EmailTemplate(
            subject="🔄 New Pickup PIN - Locker #{locker_id}",
            body="""Your new pickup PIN has been generated.

PICKUP PIN: {pin}

PICKUP DETAILS:
• Locker: #{locker_id}
• PIN expires: {expiry_time}

This PIN replaces any previous PIN for this parcel.

Campus Locker System""",
            notification_type=NotificationType.PIN_REGENERATION
        )
    }
    
    @classmethod
    def create_parcel_deposit_email(cls, parcel_id: int, locker_id: int, pin: str, expiry_time: datetime) -> FormattedEmail:
        """Create email for parcel deposit notification"""
        # Get configuration values
        from flask import current_app
        pin_expiry_hours = current_app.config.get('PIN_EXPIRY_HOURS', 24)
        parcel_max_pickup_days = current_app.config.get('PARCEL_MAX_PICKUP_DAYS', 7)
        
        # Create dynamic template with configurable PIN expiry and parcel lifecycle
        dynamic_template = EmailTemplate(
            subject="📦 Parcel Deposited - Pickup PIN",
            body=f"""Hello!

Your parcel has been deposited and is ready for pickup.

PICKUP PIN: {{pin}}

PICKUP DETAILS:
• Locker: #{{locker_id}}
• PIN expires: {{expiry_time}}
• Parcel pickup deadline: {parcel_max_pickup_days} days from deposit

TO COLLECT YOUR PARCEL:
1. Go to the pickup location
2. Enter PIN: {{pin}}
3. Open locker #{{locker_id}}
4. Collect your parcel and close the locker

SECURITY NOTES:
• This PIN is valid for {pin_expiry_hours} hours only
• Keep your PIN secure and don't share it
• Parcel must be collected within {parcel_max_pickup_days} days of deposit

Campus Locker System""",
            notification_type=NotificationType.PARCEL_DEPOSIT
        )
        
        data = {
            'parcel_id': parcel_id,
            'locker_id': locker_id,
            'pin': pin,
            'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
        }
        return dynamic_template.format_with_data(data)
    
    @classmethod
    def create_parcel_ready_email(cls, parcel_id: int, locker_id: int, deposited_time: datetime, pin_generation_url: str) -> FormattedEmail:
        """Create email for parcel ready notification (without PIN)"""
        # Get configuration values
        from flask import current_app
        pin_expiry_hours = current_app.config.get('PIN_EXPIRY_HOURS', 24)
        parcel_max_pickup_days = current_app.config.get('PARCEL_MAX_PICKUP_DAYS', 7)
        
        # Create dynamic template with configurable PIN expiry and parcel lifecycle
        dynamic_template = EmailTemplate(
            subject="📦 Your Parcel is Ready for Pickup",
            body=f"""Hello!

Your parcel has been deposited and is ready for pickup.

PICKUP DETAILS:
• Locker: #{{locker_id}}
• Deposited: {{deposited_time}}
• Pickup deadline: You have {parcel_max_pickup_days} days from deposit to collect your parcel

GENERATE YOUR PIN:
To get your pickup PIN, click the link below:
{{pin_generation_url}}

HOW IT WORKS:
1. Click the link above
2. A secure PIN will be generated and emailed to you
3. Use the PIN to open locker #{{locker_id}}
4. Collect your parcel

IMPORTANT:
• PIN generation link expires in {pin_expiry_hours} hours
• Each PIN is valid for {pin_expiry_hours} hours after generation
• You can generate up to 3 PINs per day
• Each new PIN replaces the previous one
• Parcel must be collected within {parcel_max_pickup_days} days of deposit

Need help? Contact support or visit the pickup location.

Campus Locker System""",
            notification_type=NotificationType.PARCEL_READY_FOR_PICKUP
        )
        
        data = {
            'parcel_id': parcel_id,
            'locker_id': locker_id,
            'deposited_time': deposited_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC',
            'pin_generation_url': pin_generation_url
        }
        return dynamic_template.format_with_data(data)
    
    @classmethod
    def create_pin_generation_email(cls, parcel_id: int, locker_id: int, pin: str, expiry_time: datetime, pin_generation_url: str) -> FormattedEmail:
        """Create email for PIN generation notification"""
        # Get configuration values
        from flask import current_app
        pin_expiry_hours = current_app.config.get('PIN_EXPIRY_HOURS', 24)
        parcel_max_pickup_days = current_app.config.get('PARCEL_MAX_PICKUP_DAYS', 7)
        
        # Create dynamic template with configurable PIN expiry and parcel lifecycle
        dynamic_template = EmailTemplate(
            subject="🔑 Your Pickup PIN - Locker #{locker_id}",
            body=f"""Your pickup PIN has been generated!

PICKUP PIN: {{pin}}

PICKUP DETAILS:
• Locker: #{{locker_id}}
• PIN expires: {{expiry_time}}
• Parcel pickup deadline: {parcel_max_pickup_days} days from deposit

TO COLLECT YOUR PARCEL:
1. Go to the pickup location
2. Enter PIN: {{pin}}
3. Open locker #{{locker_id}}
4. Collect your parcel and close the locker

🔄 NEED A NEW PIN?
If this PIN expires, you can generate a new one:
{{pin_generation_url}}

SECURITY NOTES:
• This PIN is valid for {pin_expiry_hours} hours only
• Keep your PIN secure and don't share it
• You can generate up to 3 PINs per day
• Parcel must be collected within {parcel_max_pickup_days} days of deposit

Campus Locker System""",
            notification_type=NotificationType.PIN_GENERATION
        )
        
        data = {
            'parcel_id': parcel_id,
            'locker_id': locker_id,
            'pin': pin,
            'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC',
            'pin_generation_url': pin_generation_url
        }
        return dynamic_template.format_with_data(data)
    
    @classmethod
    def create_pin_reissue_email(cls, parcel_id: int, locker_id: int, pin: str, expiry_time: datetime, pin_generation_url: str) -> FormattedEmail:
        """Create email for PIN reissue notification"""
        # Get configuration values
        from flask import current_app
        pin_expiry_hours = current_app.config.get('PIN_EXPIRY_HOURS', 24)
        parcel_max_pickup_days = current_app.config.get('PARCEL_MAX_PICKUP_DAYS', 7)
        
        # Create dynamic template with configurable PIN expiry and parcel lifecycle
        dynamic_template = EmailTemplate(
            subject="🔄 New Pickup PIN - Locker #{locker_id}",
            body=f"""A new pickup PIN has been issued for your parcel.

PICKUP PIN: {{pin}}

PICKUP DETAILS:
• Locker: #{{locker_id}}
• PIN expires: {{expiry_time}}
• Parcel pickup deadline: {parcel_max_pickup_days} days from deposit

TO COLLECT YOUR PARCEL:
1. Go to the pickup location
2. Enter PIN: {{pin}}
3. Open locker #{{locker_id}}
4. Collect your parcel and close the locker

🔄 NEED A NEW PIN?
If this PIN expires, you can generate a new one:
{{pin_generation_url}}

SECURITY NOTES:
• This PIN is valid for {pin_expiry_hours} hours only
• This PIN replaces any previous PIN for this parcel
• You can generate up to 3 PINs per day
• Parcel must be collected within {parcel_max_pickup_days} days of deposit

Campus Locker System""",
            notification_type=NotificationType.PIN_REISSUE
        )
        
        data = {
            'parcel_id': parcel_id,
            'locker_id': locker_id,
            'pin': pin,
            'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC',
            'pin_generation_url': pin_generation_url
        }
        return dynamic_template.format_with_data(data)
    
    @classmethod
    def create_pin_regeneration_email(cls, parcel_id: int, locker_id: int, pin: str, expiry_time: datetime, pin_generation_url: str) -> FormattedEmail:
        """Create email for PIN regeneration notification"""
        # Get configuration values
        from flask import current_app
        pin_expiry_hours = current_app.config.get('PIN_EXPIRY_HOURS', 24)
        parcel_max_pickup_days = current_app.config.get('PARCEL_MAX_PICKUP_DAYS', 7)
        
        # Create dynamic template with configurable PIN expiry and parcel lifecycle
        dynamic_template = EmailTemplate(
            subject="🔄 New Pickup PIN - Locker #{locker_id}",
            body=f"""Your new pickup PIN has been generated.

PICKUP PIN: {{pin}}

PICKUP DETAILS:
• Locker: #{{locker_id}}
• PIN expires: {{expiry_time}}
• Parcel pickup deadline: {parcel_max_pickup_days} days from deposit

TO COLLECT YOUR PARCEL:
1. Go to the pickup location
2. Enter PIN: {{pin}}
3. Open locker #{{locker_id}}
4. Collect your parcel and close the locker

🔄 NEED A NEW PIN?
If this PIN expires, you can generate a new one:
{{pin_generation_url}}

SECURITY NOTES:
• This PIN is valid for {pin_expiry_hours} hours only
• This PIN replaces any previous PIN for this parcel
• You can generate up to 3 PINs per day
• Parcel must be collected within {parcel_max_pickup_days} days of deposit

Campus Locker System""",
            notification_type=NotificationType.PIN_REGENERATION
        )
        
        data = {
            'parcel_id': parcel_id,
            'locker_id': locker_id,
            'pin': pin,
            'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S') + ' UTC',
            'pin_generation_url': pin_generation_url
        }
        return dynamic_template.format_with_data(data)
    
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