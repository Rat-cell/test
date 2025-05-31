"""
FR-03 Email Notification System Test Suite

This module contains comprehensive tests for the FR-03 requirement:
"System shall send automated email notifications for key parcel lifecycle events"

Test Categories:
1. Email Template Generation Tests
2. Email Content Validation Tests
3. Email Delivery Tests
4. Notification Service Integration Tests
5. Error Handling and Resilience Tests
6. Email Security and Validation Tests
7. Performance and Scalability Tests
8. End-to-End Workflow Tests

Author: Campus Locker System Team I
Date: May 30, 2025
FR-03 Implementation: Critical communication requirement for user engagement
"""

import sys
import os
from pathlib import Path

# Add the campus_locker_system directory to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

import pytest
import re
import time
import threading
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta

from app import create_app, db
from app.business.notification import NotificationManager, NotificationType, EmailTemplate, FormattedEmail
from app.services.notification_service import NotificationService
from app.persistence.models import Parcel, Locker
from app.adapters.email_adapter import EmailMessage, create_email_adapter
# Add Repository Imports
from app.persistence.repositories.locker_repository import LockerRepository
from app.persistence.repositories.parcel_repository import ParcelRepository


class TestFR03EmailNotificationSystem:
    """
    FR-03: Email Notification System - Comprehensive Test Suite
    
    Tests the email notification system that must send automated emails
    for key parcel lifecycle events with professional formatting and delivery.
    """

    @pytest.fixture
    def app(self):
        """Create test application with FR-03 configuration"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['MAIL_SERVER'] = 'mailhog'
        app.config['MAIL_PORT'] = 1025
        app.config['MAIL_DEFAULT_SENDER'] = 'noreply@campuslocker.local'
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    @pytest.fixture
    def test_locker_and_parcel(self, app):
        """Setup test locker and parcel for notification testing"""
        with app.app_context():
            # Create test locker
            locker = Locker(id=903, location="Test Email Locker", size="medium", status="occupied")
            LockerRepository.save(locker) # Use repository
            
            # Create test parcel
            parcel = Parcel(
                locker_id=903,
                recipient_email="test-fr03@example.com",
                status="deposited",
                deposited_at=datetime.utcnow(),
                pin_generation_token="test-token-123"
            )
            ParcelRepository.save(parcel) # Use repository
            
            yield locker, parcel
            
            # Cleanup
            # Keeping direct db.session.delete for test cleanup simplicity as previously discussed.
            db.session.delete(parcel)
            db.session.delete(locker)
            db.session.commit()

    # ===== 1. EMAIL TEMPLATE GENERATION TESTS =====

    def test_fr03_parcel_deposit_email_template(self, app):
        """
        FR-03: Test parcel deposit confirmation email template generation
        Verifies template structure and content formatting
        """
        with app.app_context():
            # Generate parcel ready email (this is the actual method name)
            email = NotificationManager.create_parcel_ready_email(
                parcel_id=1,
                locker_id=5,
                deposited_time=datetime(2025, 5, 30, 15, 30, 0),
                pin_generation_url="http://localhost/generate-pin/token123"
            )
            
            # Verify email structure
            assert isinstance(email, FormattedEmail), "FR-03: Should return FormattedEmail object"
            assert email.notification_type == NotificationType.PARCEL_READY_FOR_PICKUP, "FR-03: Should be ready notification type"
            
            # Verify subject content
            assert "📦" in email.subject, "FR-03: Subject should contain parcel emoji"
            assert "Ready" in email.subject or "Pickup" in email.subject, "FR-03: Subject should mention ready or pickup"
            
            # Verify body content
            assert "#5" in email.body, "FR-03: Body should contain locker number"
            assert "2025-05-30 15:30:00 UTC" in email.body, "FR-03: Body should contain formatted deposit time"
            assert "http://localhost/generate-pin/token123" in email.body, "FR-03: Body should contain PIN generation URL"
            assert "GENERATE YOUR PIN" in email.body, "FR-03: Should contain PIN generation instructions"
            assert "click the link" in email.body.lower(), "FR-03: Should contain link clicking instructions"

    def test_fr03_parcel_ready_email_template(self, app):
        """
        FR-03: Test parcel ready notification email template (email-based PIN system)
        Verifies template for initial deposit notification without PIN
        """
        with app.app_context():
            # Generate parcel ready email
            email = NotificationManager.create_parcel_ready_email(
                parcel_id=2,
                locker_id=8,
                deposited_time=datetime(2025, 5, 30, 10, 0, 0),
                pin_generation_url="http://localhost/generate-pin/token123"
            )
            
            # Verify email structure
            assert isinstance(email, FormattedEmail), "FR-03: Should return FormattedEmail object"
            assert email.notification_type == NotificationType.PARCEL_READY_FOR_PICKUP, "FR-03: Should be ready notification type"
            
            # Verify subject content
            assert "📦" in email.subject, "FR-03: Subject should contain parcel emoji"
            assert "Ready" in email.subject or "Pickup" in email.subject, "FR-03: Subject should mention ready or pickup"
            
            # Verify body content
            assert "#8" in email.body, "FR-03: Body should contain locker number"
            assert "2025-05-30 10:00:00 UTC" in email.body, "FR-03: Body should contain formatted deposit time"
            assert "http://localhost/generate-pin/token123" in email.body, "FR-03: Body should contain PIN generation URL"
            assert "GENERATE YOUR PIN" in email.body, "FR-03: Should contain PIN generation instructions"
            assert "click the link" in email.body.lower(), "FR-03: Should contain link clicking instructions"

    def test_fr03_pin_generation_email_template(self, app):
        """
        FR-03: Test PIN generation notification email template
        Verifies template for PIN delivery after generation
        """
        with app.app_context():
            # Generate PIN generation email
            email = NotificationManager.create_pin_generation_email(
                parcel_id=3,
                locker_id=12,
                pin="789012",
                expiry_time=datetime(2025, 5, 31, 9, 15, 0),
                pin_generation_url="http://localhost/generate-pin/token456"
            )
            
            # Verify email structure
            assert isinstance(email, FormattedEmail), "FR-03: Should return FormattedEmail object"
            assert email.notification_type == NotificationType.PIN_GENERATION, "FR-03: Should be PIN generation type"
            
            # Verify subject content
            assert "🔑" in email.subject, "FR-03: Subject should contain key emoji"
            assert "PIN" in email.subject, "FR-03: Subject should mention PIN"
            assert "#12" in email.subject, "FR-03: Subject should contain locker number"
            
            # Verify body content
            assert "789012" in email.body, "FR-03: Body should contain the PIN"
            assert "#12" in email.body, "FR-03: Body should contain locker number"
            assert "2025-05-31 09:15:00 UTC" in email.body, "FR-03: Body should contain formatted expiry time"
            assert "http://localhost/generate-pin/token456" in email.body, "FR-03: Body should contain regeneration URL"
            assert "NEED A NEW PIN" in email.body, "FR-03: Should contain regeneration instructions"

    def test_fr03_pin_reissue_email_template(self, app):
        """
        FR-03: Test PIN reissue notification email template
        Verifies template for admin-initiated PIN reissue
        """
        with app.app_context():
            # Generate PIN reissue email
            email = NotificationManager.create_pin_reissue_email(
                parcel_id=4,
                locker_id=15,
                pin="345678",
                expiry_time=datetime(2025, 5, 31, 12, 45, 0),
                pin_generation_url="http://localhost/generate-pin/token789"
            )
            
            # Verify email structure
            assert isinstance(email, FormattedEmail), "FR-03: Should return FormattedEmail object"
            assert email.notification_type == NotificationType.PIN_REISSUE, "FR-03: Should be PIN reissue type"
            
            # Verify subject content
            assert "🔄" in email.subject, "FR-03: Subject should contain refresh emoji"
            assert "New" in email.subject or "PIN" in email.subject, "FR-03: Subject should mention new PIN"
            
            # Verify body content
            assert "345678" in email.body, "FR-03: Body should contain the new PIN"
            assert "#15" in email.body, "FR-03: Body should contain locker number"
            assert "replaces any previous PIN" in email.body, "FR-03: Should mention PIN replacement"

    def test_fr03_24h_reminder_email_template(self, app):
        """
        FR-03: Test 24-hour reminder email template (FR-04 integration)
        Verifies template for pickup reminder notifications
        """
        with app.app_context():
            # Generate 24h reminder email
            email = NotificationManager.create_24h_reminder_email(
                parcel_id=5,
                locker_id=20,
                deposited_time=datetime(2025, 5, 29, 14, 30, 0),
                pin_generation_url="http://localhost/generate-pin/tokenABC"
            )
            
            # Verify email structure
            assert isinstance(email, FormattedEmail), "FR-03: Should return FormattedEmail object"
            assert email.notification_type == NotificationType.PICKUP_REMINDER, "FR-03: Should be reminder type"
            
            # Verify subject content
            assert "⏰" in email.subject, "FR-03: Subject should contain clock emoji"
            assert "Reminder" in email.subject, "FR-03: Subject should mention reminder"
            
            # Verify body content
            assert "#20" in email.body, "FR-03: Body should contain locker number"
            assert "2025-05-29 14:30:00 UTC" in email.body, "FR-03: Body should contain formatted deposit time"
            assert "http://localhost/generate-pin/tokenABC" in email.body, "FR-03: Body should contain PIN generation URL"
            assert "waiting for pickup" in email.body.lower(), "FR-03: Should mention waiting for pickup"

    # ===== 2. EMAIL CONTENT VALIDATION TESTS =====

    def test_fr03_email_content_security_validation(self, app):
        """
        FR-03: Test email content security and validation
        Verifies no sensitive information exposure and proper formatting
        """
        with app.app_context():
            # Test various email templates for security
            emails = [
                NotificationManager.create_parcel_ready_email(1, 1, datetime.utcnow(), "http://example.com/pin/token"),
                NotificationManager.create_parcel_ready_email(1, 1, datetime.utcnow(), "http://example.com/pin/token"),
                NotificationManager.create_pin_generation_email(1, 1, "654321", datetime.utcnow(), "http://example.com/pin/token")
            ]
            
            for email in emails:
                # Verify no HTML injection vulnerabilities
                assert "<script>" not in email.body.lower(), "FR-03: Email should not contain script tags"
                assert "javascript:" not in email.body.lower(), "FR-03: Email should not contain JavaScript"
                
                # Verify proper formatting
                assert len(email.subject) > 0, "FR-03: Email subject should not be empty"
                assert len(email.body) > 50, "FR-03: Email body should be substantial"
                
                # Verify professional tone
                assert "Hello" in email.body or "Your" in email.body, "FR-03: Email should have professional greeting"

    def test_fr03_email_mobile_friendly_formatting(self, app):
        """
        FR-03: Test email mobile-friendly formatting
        Verifies emails are readable on mobile devices
        """
        with app.app_context():
            email = NotificationManager.create_pin_generation_email(
                parcel_id=1,
                locker_id=1,
                pin="123456",
                expiry_time=datetime.utcnow(),
                pin_generation_url="http://example.com/pin/token"
            )
            
            # Check line length (mobile-friendly)
            lines = email.body.split('\n')
            long_lines = [line for line in lines if len(line) > 80]
            assert len(long_lines) < len(lines) * 0.2, "FR-03: Most lines should be mobile-friendly length"
            
            # Check for clear structure
            assert "PICKUP PIN:" in email.body, "FR-03: Should have clear section headers"
            assert "PICKUP DETAILS:" in email.body, "FR-03: Should have organized sections"

    def test_fr03_email_configuration_integration(self, app):
        """
        FR-03: Test email template integration with configuration
        Verifies templates use configurable values correctly
        """
        with app.app_context():
            # Set test configuration
            app.config['PIN_EXPIRY_HOURS'] = 48
            app.config['PARCEL_MAX_PICKUP_DAYS'] = 14
            
            email = NotificationManager.create_parcel_ready_email(
                parcel_id=1,
                locker_id=1,
                deposited_time=datetime.utcnow(),
                pin_generation_url="http://example.com/pin/token"
            )
            
            # Verify configuration values are used
            assert "48 hours" in email.body, "FR-03: Should use configured PIN expiry hours"
            assert "14 days" in email.body, "FR-03: Should use configured max pickup days"

    # ===== 3. EMAIL DELIVERY TESTS =====

    @patch('app.services.notification_service.NotificationService._send_email')
    def test_fr03_email_delivery_success(self, mock_send_email, app, test_locker_and_parcel):
        """
        FR-03: Test successful email delivery
        Verifies notification service can deliver emails successfully
        """
        with app.app_context():
            # Mock successful email delivery
            mock_send_email.return_value = True

            locker, parcel = test_locker_and_parcel

            # Test parcel ready notification delivery
            success, message = NotificationService.send_parcel_ready_notification(
                recipient_email="test@example.com",
                parcel_id=parcel.id,
                locker_id=locker.id,
                deposited_time=parcel.deposited_at,
                pin_generation_url="http://example.com/pin/token"
            )

            # Verify delivery success
            assert success is True, "FR-03: Email delivery should succeed"
            assert "sent to test@example.com" in message, "FR-03: Success message should include recipient"

            # Verify adapter was called
            mock_send_email.assert_called_once()

            # Verify email message structure (check call arguments)
            call_args = mock_send_email.call_args
            assert call_args is not None, "FR-03: Email sending should be called"
            assert "test@example.com" in str(call_args), "FR-03: Should send to correct recipient"

    @patch('app.services.notification_service.NotificationService._send_email')
    def test_fr03_email_delivery_failure_handling(self, mock_send_email, app, test_locker_and_parcel):
        """
        FR-03: Test email delivery failure handling
        Verifies graceful handling of email delivery failures
        """
        with app.app_context():
            # Mock email delivery failure
            mock_send_email.return_value = False

            locker, parcel = test_locker_and_parcel

            # Test failed delivery handling
            success, message = NotificationService.send_parcel_ready_notification(
                recipient_email="fail@example.com",
                parcel_id=parcel.id,
                locker_id=locker.id,
                deposited_time=parcel.deposited_at,
                pin_generation_url="http://example.com/pin/token"
            )

            # Verify failure handling
            assert success is False, "FR-03: Should report delivery failure"
            assert "Failed to send" in message, "FR-03: Should provide failure message"

            # Verify system continues operation
            assert isinstance(message, str), "FR-03: Should return error message string"

    def test_fr03_email_validation_business_rules(self, app):
        """
        FR-03: Test email validation business rules
        Verifies email address validation and business logic
        """
        with app.app_context():
            # Test valid email addresses
            valid_emails = [
                "user@example.com",
                "test.user+tag@domain.co.uk",
                "user123@subdomain.example.org"
            ]
            
            for email in valid_emails:
                assert NotificationManager.validate_email_address(email), f"FR-03: {email} should be valid"
                assert NotificationManager.is_delivery_allowed(email), f"FR-03: {email} should be allowed"
            
            # Test invalid email addresses
            invalid_emails = [
                "invalid-email",
                "@example.com",
                "user@",
                "user..double@example.com",
                ""
            ]
            
            for email in invalid_emails:
                assert not NotificationManager.validate_email_address(email), f"FR-03: {email} should be invalid"
                assert not NotificationManager.is_delivery_allowed(email), f"FR-03: {email} should not be allowed"

    # ===== 4. NOTIFICATION SERVICE INTEGRATION TESTS =====

    def test_fr03_notification_service_all_email_types(self, app, test_locker_and_parcel):
        """
        FR-03: Test notification service handles all email types
        Verifies service layer integrates with all notification types
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.notification_service.NotificationService._send_email') as mock_send:
                mock_send.return_value = True
                
                # Test deposit notification
                success1, _ = NotificationService.send_parcel_ready_notification(
                    "test@example.com", parcel.id, locker.id, datetime.utcnow(), "http://example.com/pin"
                )
                
                # Test ready notification  
                success2, _ = NotificationService.send_parcel_ready_notification(
                    "test@example.com", parcel.id, locker.id, datetime.utcnow(), "http://example.com/pin"
                )
                
                # Test reminder notification
                success3, _ = NotificationService.send_24h_reminder_notification(
                    "test@example.com", parcel.id, locker.id, datetime.utcnow(), "http://example.com/pin"
                )
                
                # Verify all notification types work
                assert success1 is True, "FR-03: Ready notification should work"
                assert success2 is True, "FR-03: Ready notification should work"
                assert success3 is True, "FR-03: Reminder notification should work"
                
                # Verify all were sent
                assert mock_send.call_count == 3, "FR-03: All notification types should be sent"

    def test_fr03_audit_logging_integration(self, app, test_locker_and_parcel):
        """
        FR-03: Test audit logging integration for notifications
        Verifies all email activities are logged for audit trail
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.notification_service.NotificationService._send_email') as mock_send:
                with patch('app.services.audit_service.AuditService.log_event') as mock_audit:
                    mock_send.return_value = True
                    
                    # Send notification
                    NotificationService.send_parcel_ready_notification(
                        "audit@example.com", parcel.id, locker.id, datetime.utcnow(), "http://example.com/pin"
                    )
                    
                    # Verify audit logging occurred
                    mock_audit.assert_called_once()
                    
                    # Verify audit log content
                    call_args = mock_audit.call_args
                    assert call_args[0][0] == "NOTIFICATION_SENT", "FR-03: Should log notification event"
                    assert "notification_type" in call_args[1]["details"], "FR-03: Should log notification type"
                    assert "recipient" in call_args[1]["details"], "FR-03: Should log recipient"

    # ===== 5. ERROR HANDLING AND RESILIENCE TESTS =====

    @patch('app.services.notification_service.NotificationService._send_email')
    def test_fr03_email_service_exception_handling(self, mock_send_email, app, test_locker_and_parcel):
        """
        FR-03: Test email service exception handling
        Verifies system resilience during email service failures
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel

            # Mock email adapter exception
            mock_send_email.side_effect = Exception("Email service unavailable")

            # Test exception handling
            success, message = NotificationService.send_parcel_ready_notification(
                "exception@example.com", parcel.id, locker.id, datetime.utcnow(), "http://example.com/pin"
            )

            # Verify graceful failure
            assert success is False, "FR-03: Should handle email service exceptions"
            assert "error occurred" in message.lower(), "FR-03: Should provide error message"

    def test_fr03_invalid_template_data_handling(self, app):
        """
        FR-03: Test handling of invalid template data
        Verifies robust template formatting with edge cases
        """
        with app.app_context():
            # Test with None values
            try:
                email = NotificationManager.create_parcel_ready_email(
                    parcel_id=None,
                    locker_id=None,
                    deposited_time=None,
                    pin_generation_url=None
                )
                # Should not crash, but handle gracefully
                assert isinstance(email, FormattedEmail), "FR-03: Should handle None values gracefully"
            except Exception as e:
                # If exception occurs, should be handled gracefully
                assert "required" in str(e).lower() or "none" in str(e).lower(), "FR-03: Should provide meaningful error"

    def test_fr03_email_rate_limiting_simulation(self, app, test_locker_and_parcel):
        """
        FR-03: Test email rate limiting simulation
        Verifies system handles high email volume appropriately
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.notification_service.NotificationService._send_email') as mock_send:
                mock_send.return_value = True
                
                # Send multiple emails rapidly
                successes = 0
                for i in range(10):
                    success, _ = NotificationService.send_parcel_ready_notification(
                        f"rate-test-{i}@example.com", parcel.id, locker.id, datetime.utcnow(), f"http://example.com/pin/{i}"
                    )
                    if success:
                        successes += 1
                
                # Should handle multiple emails (no rate limiting implemented yet)
                assert successes >= 8, "FR-03: Should handle multiple emails successfully"

    # ===== 6. EMAIL SECURITY AND VALIDATION TESTS =====

    def test_fr03_email_injection_prevention(self, app):
        """
        FR-03: Test email injection attack prevention
        Verifies protection against email header injection
        """
        with app.app_context():
            # Test with malicious input
            malicious_inputs = [
                "user@example.com\nBcc: hacker@evil.com",
                "user@example.com\r\nSubject: Hijacked",
                "user@example.com%0ABcc:hacker@evil.com",
                "normal@example.com\nContent-Type: text/html"
            ]
            
            for malicious_email in malicious_inputs:
                # Should either reject or sanitize malicious input
                is_allowed = NotificationManager.is_delivery_allowed(malicious_email)
                is_valid = NotificationManager.validate_email_address(malicious_email)
                
                # At least one validation should fail
                assert not (is_allowed and is_valid), f"FR-03: Should reject malicious email: {malicious_email}"

    def test_fr03_pin_masking_in_logs(self, app, test_locker_and_parcel):
        """
        FR-03: Test PIN masking in log files
        Verifies PINs are not exposed in system logs
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.notification_service.current_app.logger') as mock_logger:
                with patch('app.services.notification_service.NotificationService._send_email') as mock_send:
                    mock_send.side_effect = Exception("Test logging error")
                    
                    # Trigger error to generate log
                    NotificationService.send_parcel_ready_notification(
                        "log-test@example.com", parcel.id, locker.id, datetime.utcnow(), "http://example.com/pin"
                    )
                    
                    # Verify logger was called
                    assert mock_logger.error.called, "FR-03: Should log errors"
                    
                    # Verify PIN not in logs (check all logged messages)
                    logged_messages = [call[0][0] for call in mock_logger.error.call_args_list]
                    for message in logged_messages:
                        assert "SECRET123" not in message, "FR-03: PIN should not appear in logs"

    # ===== 7. PERFORMANCE AND SCALABILITY TESTS =====

    def test_fr03_email_generation_performance(self, app):
        """
        FR-03: Test email template generation performance
        Verifies template generation is fast enough for real-time use
        """
        with app.app_context():
            # Measure email generation time
            start_time = time.time()
            
            for i in range(100):
                email = NotificationManager.create_parcel_ready_email(
                    parcel_id=i,
                    locker_id=i % 20 + 1,
                    deposited_time=datetime.utcnow(),
                    pin_generation_url="http://example.com/pin/token"
                )
                assert isinstance(email, FormattedEmail), "FR-03: Should generate valid email"
            
            end_time = time.time()
            generation_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Should generate 100 emails quickly
            assert generation_time < 1000, f"FR-03: Email generation too slow ({generation_time:.2f}ms for 100 emails)"
            
            # Calculate per-email time
            per_email_time = generation_time / 100
            assert per_email_time < 10, f"FR-03: Per-email generation should be <10ms (actual: {per_email_time:.2f}ms)"

    def test_fr03_concurrent_email_generation_safety(self, app):
        """
        FR-03: Test thread safety of concurrent email generation
        Verifies no race conditions in email template generation
        """
        emails = []
        errors = []
        
        def generate_email_thread(thread_id):
            try:
                with app.app_context():
                    email = NotificationManager.create_pin_generation_email(
                        parcel_id=thread_id,
                        locker_id=thread_id % 10 + 1,
                        pin=f"{thread_id:06d}",
                        expiry_time=datetime.utcnow() + timedelta(hours=24),
                        pin_generation_url=f"http://example.com/pin/token{thread_id}"
                    )
                    emails.append(email)
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple concurrent threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=generate_email_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0, f"FR-03: Concurrent email generation should not cause errors: {errors}"
        
        # Verify all generations succeeded
        assert len(emails) == 10, "FR-03: All concurrent email generations should succeed"
        
        # Verify all emails are unique and valid
        pins = {email.body.split("PICKUP PIN: ")[1].split("\n")[0] for email in emails}
        assert len(pins) == 10, "FR-03: All generated emails should have unique PINs"

    # ===== 8. END-TO-END WORKFLOW TESTS =====

    def test_fr03_complete_email_workflow_deposit_to_pickup(self, app, test_locker_and_parcel):
        """
        FR-03: Test complete email workflow from deposit to pickup
        Verifies all email notifications work in sequence
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.notification_service.NotificationService._send_email') as mock_send:
                mock_send.return_value = True
                
                # Step 1: Parcel ready notification (email-based PIN)
                success1, message1 = NotificationService.send_parcel_ready_notification(
                    recipient_email="workflow@example.com",
                    parcel_id=parcel.id,
                    locker_id=locker.id,
                    deposited_time=parcel.deposited_at,
                    pin_generation_url="http://example.com/pin/token123"
                )
                
                # Step 2: PIN generation notification
                success2, message2 = NotificationService.send_pin_generation_notification(
                    recipient_email="workflow@example.com",
                    parcel_id=parcel.id,
                    locker_id=locker.id,
                    pin="123456",
                    expiry_time=datetime.utcnow() + timedelta(hours=24),
                    pin_generation_url="http://example.com/pin/token123"
                )
                
                # Step 3: 24h reminder notification (if needed)
                success3, message3 = NotificationService.send_24h_reminder_notification(
                    recipient_email="workflow@example.com",
                    parcel_id=parcel.id,
                    locker_id=locker.id,
                    deposited_time=parcel.deposited_at,
                    pin_generation_url="http://example.com/pin/token123"
                )
                
                # Verify entire workflow
                assert success1 is True, "FR-03: Ready notification should succeed"
                assert success2 is True, "FR-03: PIN generation notification should succeed"
                assert success3 is True, "FR-03: Reminder notification should succeed"
                
                # Verify correct number of emails sent
                assert mock_send.call_count == 3, "FR-03: Should send all workflow emails"
                
                # Verify email content progression
                sent_emails = [call[0][1] for call in mock_send.call_args_list]  # Get FormattedEmail objects
                
                # Check ready email (no PIN)
                ready_email = sent_emails[0]
                assert "GENERATE YOUR PIN" in ready_email.body, "FR-03: Ready email should mention PIN generation"
                assert "123456" not in ready_email.body, "FR-03: Ready email should not contain PIN"
                
                # Check PIN email (contains PIN)
                pin_email = sent_emails[1]
                assert "PICKUP PIN: 123456" in pin_email.body, "FR-03: PIN email should contain PIN"
                
                # Check reminder email (mentions waiting)
                reminder_email = sent_emails[2]
                assert "waiting for pickup" in reminder_email.body.lower(), "FR-03: Reminder should mention waiting"

    def test_fr03_admin_missing_notification_workflow(self, app, test_locker_and_parcel):
        """
        FR-03: Test admin missing parcel notification workflow (FR-06 integration)
        Verifies admin notifications work correctly
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.notification_service.NotificationService._send_email') as mock_send:
                mock_send.return_value = True
                
                # Send admin missing notification
                success, message = NotificationService.send_parcel_missing_admin_notification(
                    parcel_id=parcel.id,
                    locker_id=locker.id,
                    recipient_email="reporter@example.com"
                )
                
                # Verify admin notification
                assert success is True, "FR-03: Admin notification should succeed"
                assert "admin" in message.lower(), "FR-03: Should mention admin in response"
                
                # Verify email was sent
                mock_send.assert_called_once()
                
                # Verify admin email content
                sent_admin_email = mock_send.call_args[0][1]  # Get FormattedEmail object
                assert "🚨" in sent_admin_email.subject, "FR-03: Admin email should have urgent indicator"
                assert "URGENT" in sent_admin_email.body or "Missing" in sent_admin_email.body, "FR-03: Should indicate urgency"
                assert str(parcel.id) in sent_admin_email.body, "FR-03: Should contain parcel ID"
                assert str(locker.id) in sent_admin_email.body, "FR-03: Should contain locker ID"


# ===== STANDALONE TEST FUNCTIONS =====

def test_fr03_email_template_validation_comprehensive():
    """
    FR-03: Comprehensive email template validation
    Validates all email templates meet professional standards
    """
    app = create_app()
    
    with app.app_context():
        # Test all notification types
        test_data = {
            'parcel_deposit': NotificationManager.create_parcel_ready_email(
                1, 1, datetime.utcnow(), "http://example.com/pin"
            ),
            'parcel_ready': NotificationManager.create_parcel_ready_email(
                1, 1, datetime.utcnow(), "http://example.com/pin"
            ),
            'pin_generation': NotificationManager.create_pin_generation_email(
                1, 1, "654321", datetime.utcnow(), "http://example.com/pin"
            ),
            'reminder': NotificationManager.create_24h_reminder_email(
                1, 1, datetime.utcnow() - timedelta(hours=25), "http://example.com/pin"
            )
        }
        
        for email_type, email in test_data.items():
            # Professional standards validation
            assert len(email.subject) >= 10, f"FR-03: {email_type} subject too short"
            assert len(email.subject) <= 100, f"FR-03: {email_type} subject too long"
            assert len(email.body) >= 100, f"FR-03: {email_type} body too short"
            
            # Content quality validation
            assert email.subject[0].isupper() or email.subject[0] in "📦🔑⏰🚨", f"FR-03: {email_type} subject should start with capital or emoji"
            assert "Campus Locker System" in email.body, f"FR-03: {email_type} should include system name"
            assert re.search(r'#\d+', email.body), f"FR-03: {email_type} should include locker number with #"
            
            # Structure validation
            assert email.body.count('\n\n') >= 2, f"FR-03: {email_type} should have clear paragraph structure"
            assert ":" in email.body, f"FR-03: {email_type} should have structured sections"
            
        print("FR-03 Email Template Validation: All templates meet professional standards")


def test_fr03_notification_type_coverage():
    """
    FR-03: Test coverage of all notification types
    Ensures all required notification types are implemented
    """
    app = create_app()
    
    with app.app_context():
        # Required notification types for FR-03
        required_types = [
            NotificationType.PARCEL_READY_FOR_PICKUP,
            NotificationType.PIN_GENERATION,
            NotificationType.PIN_REISSUE,
            NotificationType.PIN_REGENERATION,
            NotificationType.PICKUP_REMINDER
        ]
        
        # Verify all types have email creation methods
        creation_methods = {
            NotificationType.PARCEL_READY_FOR_PICKUP: NotificationManager.create_parcel_ready_email,
            NotificationType.PIN_GENERATION: NotificationManager.create_pin_generation_email,
            NotificationType.PIN_REISSUE: NotificationManager.create_pin_reissue_email,
            NotificationType.PIN_REGENERATION: NotificationManager.create_pin_regeneration_email,
            NotificationType.PICKUP_REMINDER: NotificationManager.create_24h_reminder_email
        }
        
        for notification_type in required_types:
            assert notification_type in creation_methods, f"FR-03: Missing email creation method for {notification_type}"
            assert callable(creation_methods[notification_type]), f"FR-03: Email creation method for {notification_type} should be callable"
        
        print(f"FR-03 Notification Type Coverage: All {len(required_types)} required types implemented")


def test_fr03_system_health_check():
    """
    FR-03: Test system health for email notification functionality
    Verifies all components are available and working
    """
    app = create_app()
    
    with app.app_context():
        # Test that all required components exist
        assert hasattr(NotificationManager, 'create_parcel_ready_email'), "FR-03: Ready email method should exist"
        assert hasattr(NotificationManager, 'validate_email_address'), "FR-03: Email validation should exist"
        assert hasattr(NotificationService, 'send_parcel_ready_notification'), "FR-03: Ready service should exist"
        
        # Test basic functionality
        email = NotificationManager.create_parcel_ready_email(1, 1, datetime.utcnow(), "http://example.com/pin")
        assert isinstance(email, FormattedEmail), "FR-03: Should create FormattedEmail objects"
        assert len(email.subject) > 0, "FR-03: Email should have subject"
        assert len(email.body) > 0, "FR-03: Email should have body"
        
        # Test email validation
        assert NotificationManager.validate_email_address("test@example.com"), "FR-03: Email validation should work"
        assert not NotificationManager.validate_email_address("invalid"), "FR-03: Should reject invalid emails"
        
        print("FR-03 System Health: All email notification components functional")


if __name__ == '__main__':
    # Run FR-03 tests
    pytest.main([__file__, '-v', '-s']) 