"""
Email Adapter - External email service interface and implementation

This adapter provides a clean interface to external email services,
abstracting away implementation details like Flask-Mail from the business logic.
"""
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from dataclasses import dataclass
from flask import current_app
from flask_mail import Message
from app import mail


@dataclass
class EmailMessage:
    """Domain representation of an email message"""
    to: str
    subject: str
    body: str
    from_address: Optional[str] = None
    html_body: Optional[str] = None


class EmailAdapterInterface(ABC):
    """Interface for email adapters - defines the contract"""
    
    @abstractmethod
    def send_email(self, message: EmailMessage) -> Tuple[bool, str]:
        """
        Send an email message
        
        Args:
            message: EmailMessage containing email details
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if email adapter is properly configured"""
        pass


class FlaskMailAdapter(EmailAdapterInterface):
    """Flask-Mail implementation of the email adapter"""
    
    def send_email(self, message: EmailMessage) -> Tuple[bool, str]:
        """Send email using Flask-Mail"""
        try:
            if not self.is_configured():
                return False, "Email service not configured"
            
            # Create Flask-Mail message
            msg = Message(
                subject=message.subject,
                recipients=[message.to],
                body=message.body,
                sender=message.from_address  # Will use default if None
            )
            
            if message.html_body:
                msg.html = message.html_body
            
            # Send via Flask-Mail
            mail.send(msg)
            
            return True, f"Email sent successfully to {message.to}"
            
        except Exception as e:
            error_msg = f"Email delivery failed to {message.to}: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg
    
    def is_configured(self) -> bool:
        """Check if Flask-Mail is configured"""
        try:
            # Check if mail extension is properly configured
            return (
                hasattr(current_app, 'extensions') and 
                'mail' in current_app.extensions and
                current_app.extensions['mail'] is not None
            )
        except:
            return False


class MockEmailAdapter(EmailAdapterInterface):
    """Mock email adapter for testing - stores messages instead of sending"""
    
    def __init__(self):
        self.sent_messages = []
    
    def send_email(self, message: EmailMessage) -> Tuple[bool, str]:
        """Mock send - just store the message"""
        self.sent_messages.append(message)
        return True, f"Mock email sent to {message.to}"
    
    def is_configured(self) -> bool:
        """Mock adapter is always configured"""
        return True
    
    def clear_messages(self):
        """Clear stored messages"""
        self.sent_messages.clear()
    
    def get_messages_for(self, email_address: str):
        """Get messages sent to specific email address"""
        return [msg for msg in self.sent_messages if msg.to == email_address]


# Factory function to create appropriate adapter
def create_email_adapter() -> EmailAdapterInterface:
    """Factory to create the appropriate email adapter based on configuration"""
    try:
        # Check if we're in testing mode
        if hasattr(current_app, 'testing') and current_app.testing:
            return MockEmailAdapter()
        else:
            return FlaskMailAdapter()
    except RuntimeError:
        # Working outside of application context - default to production adapter
        return FlaskMailAdapter() 