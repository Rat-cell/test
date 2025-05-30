# Notification service - orchestration layer
from typing import Tuple, Optional
from flask import current_app
from app.business.notification import NotificationManager, FormattedEmail, NotificationType
from app.services.audit_service import AuditService
from app.adapters.email_adapter import create_email_adapter, EmailMessage
from datetime import datetime

class NotificationService:
    """Service layer for notification orchestration"""
    
    @staticmethod
    def send_parcel_deposit_notification(recipient_email: str, parcel_id: int, locker_id: int, pin: str, expiry_time) -> Tuple[bool, str]:
        """Send notification when parcel is deposited"""
        try:
            # Business rule validation
            if not NotificationManager.is_delivery_allowed(recipient_email):
                return False, f"Email delivery not allowed for {recipient_email}"
            
            # Create formatted email using business logic
            formatted_email = NotificationManager.create_parcel_deposit_email(
                parcel_id=parcel_id,
                locker_id=locker_id,
                pin=pin,
                expiry_time=expiry_time
            )
            
            # Send email via adapter
            success = NotificationService._send_email(recipient_email, formatted_email)
            
            if success:
                # Log successful notification
                AuditService.log_event("NOTIFICATION_SENT", details={
                    "notification_type": NotificationType.PARCEL_DEPOSIT.value,
                    "recipient": recipient_email,
                    "parcel_id": parcel_id,
                    "locker_id": locker_id
                })
                return True, f"Deposit notification sent to {recipient_email}"
            else:
                return False, "Failed to send email notification"
                
        except Exception as e:
            current_app.logger.error(f"Error sending parcel deposit notification: {str(e)}")
            return False, "An error occurred while sending notification"
    
    @staticmethod
    def send_parcel_ready_notification(recipient_email: str, parcel_id: int, locker_id: int, deposited_time, pin_generation_url: str) -> Tuple[bool, str]:
        """Send notification when parcel is ready for pickup (email-based PIN generation)"""
        try:
            # Business rule validation
            if not NotificationManager.is_delivery_allowed(recipient_email):
                return False, f"Email delivery not allowed for {recipient_email}"
            
            # Create formatted email using business logic
            formatted_email = NotificationManager.create_parcel_ready_email(
                parcel_id=parcel_id,
                locker_id=locker_id,
                deposited_time=deposited_time,
                pin_generation_url=pin_generation_url
            )
            
            # Send email via adapter
            success = NotificationService._send_email(recipient_email, formatted_email)
            
            if success:
                # Log successful notification
                AuditService.log_event("NOTIFICATION_SENT", details={
                    "notification_type": NotificationType.PARCEL_READY_FOR_PICKUP.value,
                    "recipient": recipient_email,
                    "parcel_id": parcel_id,
                    "locker_id": locker_id
                })
                return True, f"Parcel ready notification sent to {recipient_email}"
            else:
                return False, "Failed to send email notification"
                
        except Exception as e:
            current_app.logger.error(f"Error sending parcel ready notification: {str(e)}")
            return False, "An error occurred while sending notification"
    
    @staticmethod
    def send_pin_generation_notification(recipient_email: str, parcel_id: int, locker_id: int, pin: str, expiry_time, pin_generation_url: str) -> Tuple[bool, str]:
        """Send notification when PIN is generated via email link"""
        try:
            # Business rule validation
            if not NotificationManager.is_delivery_allowed(recipient_email):
                return False, f"Email delivery not allowed for {recipient_email}"
            
            # Create formatted email using business logic
            formatted_email = NotificationManager.create_pin_generation_email(
                parcel_id=parcel_id,
                locker_id=locker_id,
                pin=pin,
                expiry_time=expiry_time,
                pin_generation_url=pin_generation_url
            )
            
            # Send email via adapter
            success = NotificationService._send_email(recipient_email, formatted_email)
            
            if success:
                # Log successful notification
                AuditService.log_event("NOTIFICATION_SENT", details={
                    "notification_type": NotificationType.PIN_GENERATION.value,
                    "recipient": recipient_email,
                    "parcel_id": parcel_id,
                    "locker_id": locker_id
                })
                return True, f"PIN generation notification sent to {recipient_email}"
            else:
                return False, "Failed to send email notification"
                
        except Exception as e:
            current_app.logger.error(f"Error sending PIN generation notification: {str(e)}")
            return False, "An error occurred while sending notification"
    
    @staticmethod
    def send_pin_reissue_notification(recipient_email: str, parcel_id: int, locker_id: int, pin: str, expiry_time, pin_generation_url: str) -> Tuple[bool, str]:
        """Send notification when PIN is reissued by admin"""
        try:
            # Business rule validation
            if not NotificationManager.is_delivery_allowed(recipient_email):
                return False, f"Email delivery not allowed for {recipient_email}"
            
            # Create formatted email using business logic
            formatted_email = NotificationManager.create_pin_reissue_email(
                parcel_id=parcel_id,
                locker_id=locker_id,
                pin=pin,
                expiry_time=expiry_time,
                pin_generation_url=pin_generation_url
            )
            
            # Send email via adapter
            success = NotificationService._send_email(recipient_email, formatted_email)
            
            if success:
                # Log successful notification
                AuditService.log_event("NOTIFICATION_SENT", details={
                    "notification_type": NotificationType.PIN_REISSUE.value,
                    "recipient": recipient_email,
                    "parcel_id": parcel_id,
                    "locker_id": locker_id
                })
                return True, f"PIN reissue notification sent to {recipient_email}"
            else:
                return False, "Failed to send email notification"
                
        except Exception as e:
            current_app.logger.error(f"Error sending PIN reissue notification: {str(e)}")
            return False, "An error occurred while sending notification"
    
    @staticmethod
    def send_pin_regeneration_notification(recipient_email: str, parcel_id: int, locker_id: int, pin: str, expiry_time, pin_generation_url: str) -> Tuple[bool, str]:
        """Send notification when PIN is regenerated by recipient request"""
        try:
            # Business rule validation
            if not NotificationManager.is_delivery_allowed(recipient_email):
                return False, f"Email delivery not allowed for {recipient_email}"
            
            # Create formatted email using business logic
            formatted_email = NotificationManager.create_pin_regeneration_email(
                parcel_id=parcel_id,
                locker_id=locker_id,
                pin=pin,
                expiry_time=expiry_time,
                pin_generation_url=pin_generation_url
            )
            
            # Send email via adapter
            success = NotificationService._send_email(recipient_email, formatted_email)
            
            if success:
                # Log successful notification
                AuditService.log_event("NOTIFICATION_SENT", details={
                    "notification_type": NotificationType.PIN_REGENERATION.value,
                    "recipient": recipient_email,
                    "parcel_id": parcel_id,
                    "locker_id": locker_id
                })
                return True, f"PIN regeneration notification sent to {recipient_email}"
            else:
                return False, "Failed to send email notification"
                
        except Exception as e:
            current_app.logger.error(f"Error sending PIN regeneration notification: {str(e)}")
            return False, "An error occurred while sending notification"
    
    @staticmethod
    def send_24h_reminder_notification(recipient_email: str, parcel_id: int, locker_id: int, deposited_time, pin_generation_url: str) -> Tuple[bool, str]:
        """
        FR-04: Send Reminder After 24h of Occupancy - Send configurable-hour reminder notification for parcel pickup
        """
        try:
            # FR-04: Business rule validation for email delivery
            if not NotificationManager.is_delivery_allowed(recipient_email):
                return False, f"Email delivery not allowed for {recipient_email}"
            
            # FR-04: Create formatted email using business logic for configurable-hour reminder
            formatted_email = NotificationManager.create_24h_reminder_email(
                parcel_id=parcel_id,
                locker_id=locker_id,
                deposited_time=deposited_time,
                pin_generation_url=pin_generation_url
            )
            
            # FR-04: Send email via adapter
            success = NotificationService._send_email(recipient_email, formatted_email)
            
            if success:
                # FR-04: Log successful notification for audit trail as required
                AuditService.log_event("FR-04_REMINDER_SENT", details={
                    "notification_type": NotificationType.PICKUP_REMINDER.value,
                    "recipient": recipient_email,
                    "parcel_id": parcel_id,
                    "locker_id": locker_id,
                    "deposited_time": deposited_time.isoformat() if deposited_time else None,
                    "hours_since_deposit": (datetime.utcnow() - deposited_time).total_seconds() / 3600 if deposited_time else None,
                    "configured_reminder_hours": current_app.config.get('REMINDER_HOURS_AFTER_DEPOSIT', 24)  # FR-04: Log configured timing
                })
                return True, f"Reminder sent to {recipient_email}"
            else:
                return False, "Failed to send reminder email"
                
        except Exception as e:
            current_app.logger.error(f"FR-04: Error sending reminder for parcel {parcel_id}: {str(e)}")  # FR-04: Error logging
            return False, "An error occurred while sending reminder"
    
    @staticmethod
    def send_parcel_missing_admin_notification(parcel_id: int, locker_id: int, recipient_email: str) -> Tuple[bool, str]:
        """
        FR-06: Report Missing Item - Send notification to admin when parcel is reported missing by recipient
        """
        try:
            # Get admin email from configuration
            admin_email = current_app.config.get('ADMIN_NOTIFICATION_EMAIL', 'admin@campuslocker.local')
            
            # Business rule validation for admin email
            if not NotificationManager.is_delivery_allowed(admin_email):
                return False, f"Email delivery not allowed for admin email {admin_email}"
            
            # FR-06: Create formatted email using business logic for missing parcel notification
            formatted_email = NotificationManager.create_parcel_missing_admin_email(
                parcel_id=parcel_id,
                locker_id=locker_id,
                recipient_email=recipient_email
            )
            
            # Send email via adapter
            success = NotificationService._send_email(admin_email, formatted_email)
            
            if success:
                # FR-06: Log successful notification for audit trail as required
                AuditService.log_event("ADMIN_NOTIFICATION_SENT", details={
                    "notification_type": "PARCEL_MISSING_REPORT",
                    "admin_recipient": admin_email,
                    "parcel_id": parcel_id,
                    "locker_id": locker_id,
                    "reporter_email_domain": recipient_email.split('@')[1] if '@' in recipient_email else 'unknown'
                })
                return True, f"Admin notification sent to {admin_email}"
            else:
                return False, "Failed to send admin notification email"
                
        except Exception as e:
            current_app.logger.error(f"Error sending admin notification for missing parcel {parcel_id}: {str(e)}")
            return False, "An error occurred while sending admin notification"
    
    @staticmethod
    def _send_email(recipient_email: str, formatted_email: FormattedEmail) -> bool:
        """Internal method to send email via adapter"""
        try:
            email_adapter = create_email_adapter()
            email_message = EmailMessage(
                to=recipient_email,
                subject=formatted_email.subject,
                body=formatted_email.body
            )
            return email_adapter.send_email(email_message)
        except Exception as e:
            current_app.logger.error(f"Error in email adapter: {str(e)}")
            return False 