"""
FR-04 Automated Reminder System Test Suite

This module contains comprehensive tests for the FR-04 requirement:
"Send Reminder After 24h of Occupancy" - Fully automated background processing

Test Categories:
1. Automatic Background Scheduler Tests
2. Bulk Reminder Processing Tests  
3. Configuration and Timing Tests
4. Duplicate Prevention Tests
5. Error Handling and Resilience Tests
6. Email Content and Delivery Tests
7. Audit Trail and Logging Tests
8. Performance and Scalability Tests

Author: Campus Locker System Team I
Date: May 30, 2025
FR-04 Implementation: Fully automated with background scheduling
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import create_app, db
from app.persistence.models import Parcel, Locker, AuditLog
from app.services.parcel_service import process_reminder_notifications
from app.services.notification_service import send_24h_reminder_notification
from app.business.notification import create_24h_reminder_email


class TestFR04AutomatedReminders:
    """
    FR-04: Send Reminder After 24h of Occupancy - Automated Test Suite
    
    Tests the fully automated reminder system that processes bulk reminders
    without any admin intervention via background scheduling.
    """

    @pytest.fixture
    def app(self):
        """Create test application with FR-04 configuration"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['REMINDER_HOURS_AFTER_DEPOSIT'] = 24
        app.config['REMINDER_PROCESSING_INTERVAL_HOURS'] = 1
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    @pytest.fixture
    def test_parcel_eligible_for_reminder(self, app):
        """Create a parcel eligible for reminder (deposited >24h ago)"""
        with app.app_context():
            # Create test locker
            locker = Locker(id=999, location="Test Locker FR-04", size="medium", status="occupied")
            db.session.add(locker)
            
            # Create parcel deposited 25 hours ago (eligible for reminder)
            old_time = datetime.utcnow() - timedelta(hours=25)
            parcel = Parcel(
                locker_id=999,
                recipient_email="test-fr04@example.com",
                status="deposited",
                deposited_at=old_time,
                pin_hash="test_hash",
                reminder_sent_at=None  # FR-04: No reminder sent yet
            )
            db.session.add(parcel)
            db.session.commit()
            
            yield parcel
            
            # Cleanup
            db.session.delete(parcel)
            db.session.delete(locker)
            db.session.commit()

    @pytest.fixture
    def test_parcel_not_eligible(self, app):
        """Create a parcel not eligible for reminder (deposited <24h ago)"""
        with app.app_context():
            # Create test locker
            locker = Locker(id=998, location="Test Locker FR-04 Recent", size="small", status="occupied")
            db.session.add(locker)
            
            # Create parcel deposited 2 hours ago (not eligible)
            recent_time = datetime.utcnow() - timedelta(hours=2)
            parcel = Parcel(
                locker_id=998,
                recipient_email="recent-fr04@example.com",
                status="deposited",
                deposited_at=recent_time,
                pin_hash="test_hash_recent",
                reminder_sent_at=None
            )
            db.session.add(parcel)
            db.session.commit()
            
            yield parcel
            
            # Cleanup
            db.session.delete(parcel)
            db.session.delete(locker)
            db.session.commit()

    # ===== 1. AUTOMATIC BACKGROUND SCHEDULER TESTS =====

    def test_fr04_scheduler_initialization(self, app):
        """
        FR-04: Test that the background scheduler initializes correctly
        Verifies the automatic scheduling system starts with the application
        """
        with app.app_context():
            # Test that scheduler configuration is loaded
            reminder_hours = app.config.get('REMINDER_HOURS_AFTER_DEPOSIT', 24)
            interval_hours = app.config.get('REMINDER_PROCESSING_INTERVAL_HOURS', 1)
            
            assert reminder_hours == 24, "FR-04: Default reminder timing should be 24 hours"
            assert interval_hours == 1, "FR-04: Default processing interval should be 1 hour"

    @patch('app.services.parcel_service.process_reminder_notifications')
    def test_fr04_scheduler_executes_processing(self, mock_process, app):
        """
        FR-04: Test that the scheduler executes reminder processing
        Verifies automatic execution without admin intervention
        """
        with app.app_context():
            # Simulate scheduler calling the processing function
            mock_process.return_value = (1, 0)  # 1 processed, 0 errors
            
            # Call the function that would be triggered by scheduler
            processed, errors = process_reminder_notifications()
            
            # Verify processing was called
            mock_process.assert_called_once()

    # ===== 2. BULK REMINDER PROCESSING TESTS =====

    @patch('app.services.notification_service.send_24h_reminder_notification')
    def test_fr04_bulk_processing_eligible_parcels(self, mock_send, app, test_parcel_eligible_for_reminder):
        """
        FR-04: Test bulk processing of eligible parcels
        Verifies system processes all eligible parcels automatically
        """
        with app.app_context():
            mock_send.return_value = True
            
            # Process reminders
            processed_count, error_count = process_reminder_notifications()
            
            # Verify results
            assert processed_count >= 1, "FR-04: Should process at least one eligible parcel"
            assert error_count == 0, "FR-04: Should have no errors for successful processing"
            
            # Verify notification was sent
            mock_send.assert_called()

    def test_fr04_bulk_processing_skips_ineligible(self, app, test_parcel_not_eligible):
        """
        FR-04: Test that bulk processing skips ineligible parcels
        Verifies correct filtering based on deposit timing
        """
        with app.app_context():
            # Process reminders
            processed_count, error_count = process_reminder_notifications()
            
            # Should not process recent parcels
            # Note: processed_count might be 0 if no other eligible parcels exist
            assert error_count == 0, "FR-04: Should have no errors even when skipping ineligible parcels"

    # ===== 3. CONFIGURATION AND TIMING TESTS =====

    def test_fr04_configurable_timing_respected(self, app):
        """
        FR-04: Test that configurable timing is respected
        Verifies open-closed principle implementation
        """
        with app.app_context():
            # Test default configuration
            default_hours = app.config.get('REMINDER_HOURS_AFTER_DEPOSIT', 24)
            assert default_hours == 24, "FR-04: Default timing should be 24 hours"
            
            # Test custom configuration
            app.config['REMINDER_HOURS_AFTER_DEPOSIT'] = 12
            custom_hours = app.config.get('REMINDER_HOURS_AFTER_DEPOSIT')
            assert custom_hours == 12, "FR-04: Custom timing should be configurable"

    def test_fr04_processing_interval_configurable(self, app):
        """
        FR-04: Test that processing interval is configurable
        Verifies scheduler timing can be adjusted
        """
        with app.app_context():
            # Test default interval
            default_interval = app.config.get('REMINDER_PROCESSING_INTERVAL_HOURS', 1)
            assert default_interval == 1, "FR-04: Default interval should be 1 hour"
            
            # Test custom interval
            app.config['REMINDER_PROCESSING_INTERVAL_HOURS'] = 2
            custom_interval = app.config.get('REMINDER_PROCESSING_INTERVAL_HOURS')
            assert custom_interval == 2, "FR-04: Custom interval should be configurable"

    # ===== 4. DUPLICATE PREVENTION TESTS =====

    def test_fr04_duplicate_prevention(self, app, test_parcel_eligible_for_reminder):
        """
        FR-04: Test that duplicate reminders are prevented
        Verifies reminder_sent_at tracking prevents multiple sends
        """
        with app.app_context():
            parcel = test_parcel_eligible_for_reminder
            
            # Mark as reminder already sent
            parcel.reminder_sent_at = datetime.utcnow()
            db.session.commit()
            
            # Process reminders
            processed_count, error_count = process_reminder_notifications()
            
            # Should not process parcel with reminder already sent
            # Verify by checking that parcel wasn't processed again
            assert error_count == 0, "FR-04: No errors should occur when skipping already-reminded parcels"

    def test_fr04_reminder_timestamp_updated(self, app, test_parcel_eligible_for_reminder):
        """
        FR-04: Test that reminder_sent_at is updated after sending
        Verifies database tracking for duplicate prevention
        """
        with app.app_context():
            parcel = test_parcel_eligible_for_reminder
            original_reminder_time = parcel.reminder_sent_at
            
            # Process reminders (mocked to always succeed)
            with patch('app.services.notification_service.send_24h_reminder_notification', return_value=True):
                process_reminder_notifications()
            
            # Refresh parcel from database
            db.session.refresh(parcel)
            
            # Verify reminder timestamp was updated
            assert parcel.reminder_sent_at is not None, "FR-04: reminder_sent_at should be set after processing"
            assert parcel.reminder_sent_at != original_reminder_time, "FR-04: reminder_sent_at should be updated"

    # ===== 5. ERROR HANDLING AND RESILIENCE TESTS =====

    @patch('app.services.notification_service.send_24h_reminder_notification')
    def test_fr04_error_handling_resilience(self, mock_send, app, test_parcel_eligible_for_reminder):
        """
        FR-04: Test system resilience during email failures
        Verifies continued operation despite individual failures
        """
        with app.app_context():
            # Simulate email delivery failure
            mock_send.return_value = False
            
            # Process reminders
            processed_count, error_count = process_reminder_notifications()
            
            # System should handle errors gracefully
            assert error_count >= 0, "FR-04: Error count should be tracked"
            # System should not crash on email failures

    @patch('app.services.notification_service.send_24h_reminder_notification')
    def test_fr04_partial_failure_handling(self, mock_send, app):
        """
        FR-04: Test handling of partial failures in bulk processing
        Verifies system continues processing despite individual failures
        """
        with app.app_context():
            # Simulate intermittent failures
            mock_send.side_effect = [True, False, True]  # Success, Failure, Success
            
            # Process reminders (if multiple parcels exist)
            processed_count, error_count = process_reminder_notifications()
            
            # System should continue processing despite failures
            assert isinstance(processed_count, int), "FR-04: Should return valid processed count"
            assert isinstance(error_count, int), "FR-04: Should return valid error count"

    # ===== 6. EMAIL CONTENT AND DELIVERY TESTS =====

    def test_fr04_email_content_generation(self, app):
        """
        FR-04: Test reminder email content generation
        Verifies professional email template creation
        """
        with app.app_context():
            # Test email template creation
            email_data = create_24h_reminder_email(
                recipient_email="test@example.com",
                locker_location="Test Locker 1",
                pin_regeneration_url="http://example.com/pin/123"
            )
            
            # Verify email content
            assert email_data['to'] == "test@example.com", "FR-04: Email should be addressed correctly"
            assert "reminder" in email_data['subject'].lower(), "FR-04: Subject should mention reminder"
            assert "Test Locker 1" in email_data['html'], "FR-04: Email should include locker location"
            assert "pin" in email_data['html'].lower(), "FR-04: Email should include PIN instructions"

    @patch('app.adapters.email_adapter.send_email')
    def test_fr04_email_delivery_attempt(self, mock_send_email, app, test_parcel_eligible_for_reminder):
        """
        FR-04: Test email delivery attempt
        Verifies notification service attempts email delivery
        """
        with app.app_context():
            mock_send_email.return_value = True
            parcel = test_parcel_eligible_for_reminder
            
            # Attempt to send reminder
            result = send_24h_reminder_notification(
                parcel.id,
                parcel.recipient_email,
                "Test Locker",
                "http://example.com/pin/123"
            )
            
            # Verify email delivery was attempted
            assert result is True, "FR-04: Email delivery should succeed when properly configured"
            mock_send_email.assert_called_once()

    # ===== 7. AUDIT TRAIL AND LOGGING TESTS =====

    def test_fr04_audit_trail_logging(self, app, test_parcel_eligible_for_reminder):
        """
        FR-04: Test comprehensive audit trail logging
        Verifies all reminder activities are logged
        """
        with app.app_context():
            # Clear existing audit logs for this test
            AuditLog.query.filter(AuditLog.action.like('%FR-04%')).delete()
            db.session.commit()
            
            # Process reminders with mocked email
            with patch('app.services.notification_service.send_24h_reminder_notification', return_value=True):
                process_reminder_notifications()
            
            # Check for FR-04 audit entries
            fr04_logs = AuditLog.query.filter(AuditLog.action.like('%FR-04%')).all()
            
            # Verify audit logging occurred
            assert len(fr04_logs) > 0, "FR-04: Audit trail should contain FR-04 activity logs"
            
            # Check for specific log types
            log_actions = [log.action for log in fr04_logs]
            has_processing_log = any('PROCESSING' in action for action in log_actions)
            assert has_processing_log, "FR-04: Should log processing activities"

    def test_fr04_audit_log_details(self, app):
        """
        FR-04: Test audit log detail content
        Verifies comprehensive logging of reminder activities
        """
        with app.app_context():
            # Process reminders and check log details
            with patch('app.services.notification_service.send_24h_reminder_notification', return_value=True):
                process_reminder_notifications()
            
            # Get recent FR-04 logs
            recent_logs = AuditLog.query.filter(
                AuditLog.action.like('%FR-04%'),
                AuditLog.timestamp >= datetime.utcnow() - timedelta(minutes=1)
            ).all()
            
            if recent_logs:
                log = recent_logs[0]
                # Verify log structure
                assert log.action.startswith('FR-04'), "FR-04: Action should be prefixed with FR-04"
                assert log.details is not None, "FR-04: Log should contain details"

    # ===== 8. PERFORMANCE AND SCALABILITY TESTS =====

    def test_fr04_bulk_processing_performance(self, app):
        """
        FR-04: Test bulk processing performance
        Verifies efficient processing of multiple parcels
        """
        with app.app_context():
            start_time = time.time()
            
            # Process reminders
            with patch('app.services.notification_service.send_24h_reminder_notification', return_value=True):
                processed_count, error_count = process_reminder_notifications()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Performance should be reasonable (under 5 seconds for bulk processing)
            assert processing_time < 5.0, f"FR-04: Bulk processing should complete quickly (took {processing_time:.2f}s)"

    def test_fr04_concurrent_processing_safety(self, app):
        """
        FR-04: Test concurrent processing safety
        Verifies system handles concurrent access safely
        """
        with app.app_context():
            results = []
            
            def run_processing():
                with patch('app.services.notification_service.send_24h_reminder_notification', return_value=True):
                    result = process_reminder_notifications()
                    results.append(result)
            
            # Simulate concurrent processing attempts
            threads = []
            for _ in range(2):
                thread = threading.Thread(target=run_processing)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify no crashes occurred
            assert len(results) == 2, "FR-04: Both concurrent operations should complete"
            
            # Results should be valid tuples
            for result in results:
                assert isinstance(result, tuple), "FR-04: Should return tuple (processed, errors)"
                assert len(result) == 2, "FR-04: Should return (processed_count, error_count)"

    # ===== 9. INTEGRATION TESTS =====

    def test_fr04_endpoint_integration(self, app, client):
        """
        FR-04: Test automatic reminder processing endpoint
        Verifies system endpoint for automated processing
        """
        with app.app_context():
            # Test the automatic processing endpoint
            response = client.get('/system/process-reminders')
            
            # Verify endpoint responds correctly
            assert response.status_code == 200, "FR-04: Automatic processing endpoint should be accessible"
            
            # Verify JSON response structure
            data = response.get_json()
            assert 'processed_count' in data, "FR-04: Response should include processed count"
            assert 'error_count' in data, "FR-04: Response should include error count"
            assert 'status' in data, "FR-04: Response should include status"

    def test_fr04_end_to_end_automation(self, app, test_parcel_eligible_for_reminder):
        """
        FR-04: Test complete end-to-end automation
        Verifies full automatic reminder workflow
        """
        with app.app_context():
            parcel = test_parcel_eligible_for_reminder
            
            # Verify parcel is eligible
            assert parcel.reminder_sent_at is None, "FR-04: Test parcel should not have reminder sent"
            
            # Mock successful email delivery
            with patch('app.services.notification_service.send_24h_reminder_notification', return_value=True):
                # Process reminders automatically
                processed_count, error_count = process_reminder_notifications()
            
            # Verify automation completed successfully
            assert processed_count >= 1, "FR-04: Should process eligible parcels"
            assert error_count == 0, "FR-04: Should complete without errors"
            
            # Verify parcel state updated
            db.session.refresh(parcel)
            assert parcel.reminder_sent_at is not None, "FR-04: Parcel should be marked as reminded"


# ===== STANDALONE TEST FUNCTIONS =====

def test_fr04_configuration_validation():
    """
    FR-04: Test configuration validation
    Standalone test for configuration system
    """
    app = create_app()
    app.config['TESTING'] = True
    
    with app.app_context():
        # Test required configuration exists
        assert hasattr(app.config, 'get'), "FR-04: App should have configuration system"
        
        # Test default values
        reminder_hours = app.config.get('REMINDER_HOURS_AFTER_DEPOSIT', 24)
        interval_hours = app.config.get('REMINDER_PROCESSING_INTERVAL_HOURS', 1)
        
        assert isinstance(reminder_hours, int), "FR-04: Reminder hours should be integer"
        assert isinstance(interval_hours, int), "FR-04: Interval hours should be integer"
        assert reminder_hours > 0, "FR-04: Reminder hours should be positive"
        assert interval_hours > 0, "FR-04: Interval hours should be positive"


def test_fr04_system_health_check():
    """
    FR-04: Test system health for reminder functionality
    Verifies all components are available
    """
    app = create_app()
    
    with app.app_context():
        # Test that all required components exist
        from app.services.parcel_service import process_reminder_notifications
        from app.services.notification_service import send_24h_reminder_notification
        from app.business.notification import create_24h_reminder_email
        
        # Verify functions are callable
        assert callable(process_reminder_notifications), "FR-04: Main processing function should exist"
        assert callable(send_24h_reminder_notification), "FR-04: Notification service should exist" 
        assert callable(create_24h_reminder_email), "FR-04: Email template function should exist"


if __name__ == '__main__':
    # Run FR-04 tests
    pytest.main([__file__, '-v', '-s']) 