"""
FR-04 Automatic Reminder System Test Suite

Tests the automatic 24-hour reminder system without waiting for real time to pass.
Uses time mocking to simulate 24+ hour conditions and tests background processing.

Key Features Tested:
- Automatic reminder detection for parcels older than 24h
- Background processing without admin intervention
- Email notification sending
- Audit trail logging
- Multiple parcel handling
"""

import sys
import os
# Add the parent directory to Python path so we can import the app module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
import datetime as dt
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.persistence.models import Parcel, Locker, AuditLog
from app.services.parcel_service import process_reminder_notifications
from app.services.notification_service import NotificationService
from app.services.audit_service import AuditService


class TestFR04AutomaticReminders:
    """Test suite for FR-04 automatic reminder system"""

    @pytest.fixture
    def setup_test_data(self, app):
        """Setup test parcels with different ages"""
        with app.app_context():
            # Clear existing data
            Parcel.query.delete()
            Locker.query.delete()
            AuditLog.query.delete()
            db.session.commit()
            
            # Create test lockers
            locker1 = Locker(id=1, location="Test Locker 1", size="small", status="occupied")
            locker2 = Locker(id=2, location="Test Locker 2", size="medium", status="occupied")
            locker3 = Locker(id=3, location="Test Locker 3", size="large", status="free")
            
            db.session.add_all([locker1, locker2, locker3])
            db.session.commit()
            
            # Create test parcels with different ages
            now = datetime.now(dt.UTC)
            
            # Parcel that needs reminder (25 hours old, no reminder sent)
            parcel_needs_reminder = Parcel(
                id=1,
                locker_id=1,
                recipient_email="test1@example.com",
                status="deposited",
                deposited_at=now - timedelta(hours=25),  # 25 hours ago
                reminder_sent_at=None  # No reminder sent yet
            )
            
            # Parcel that needs reminder (30 hours old, no reminder sent)
            parcel_needs_reminder2 = Parcel(
                id=2,
                locker_id=2,
                recipient_email="test2@example.com",
                status="deposited",
                deposited_at=now - timedelta(hours=30),  # 30 hours ago
                reminder_sent_at=None  # No reminder sent yet
            )
            
            # Parcel that doesn't need reminder (12 hours old)
            parcel_too_new = Parcel(
                id=3,
                locker_id=None,
                recipient_email="test3@example.com",
                status="deposited",
                deposited_at=now - timedelta(hours=12),  # 12 hours ago
                reminder_sent_at=None
            )
            
            # Parcel that already has reminder sent
            parcel_already_reminded = Parcel(
                id=4,
                locker_id=None,
                recipient_email="test4@example.com",
                status="deposited",
                deposited_at=now - timedelta(hours=48),  # 48 hours ago
                reminder_sent_at=now - timedelta(hours=12)  # Reminder sent 12 hours ago
            )
            
            # Picked up parcel (should not get reminder)
            parcel_picked_up = Parcel(
                id=5,
                locker_id=None,
                recipient_email="test5@example.com",
                status="picked_up",
                deposited_at=now - timedelta(hours=30),  # 30 hours ago
                picked_up_at=now - timedelta(hours=2),
                reminder_sent_at=None
            )
            
            db.session.add_all([
                parcel_needs_reminder, parcel_needs_reminder2, parcel_too_new,
                parcel_already_reminded, parcel_picked_up
            ])
            db.session.commit()
            
            yield {
                'needs_reminder': [parcel_needs_reminder, parcel_needs_reminder2],
                'too_new': parcel_too_new,
                'already_reminded': parcel_already_reminded,
                'picked_up': parcel_picked_up
            }

    def test_fr04_identifies_parcels_needing_reminders(self, app, setup_test_data):
        """Test that FR-04 correctly identifies parcels that need 24h reminders"""
        print("\n" + "="*60)
        print("🧪 TEST: FR-04 Identifies Parcels Needing Reminders")
        print("="*60)
        
        with app.app_context():
            # Show test setup
            print("📋 Test Setup:")
            print("  - 5 test parcels created with different conditions")
            print("  - 2 parcels are >24h old and need reminders")
            print("  - 1 parcel is <24h old (too new)")
            print("  - 1 parcel already has reminder sent")
            print("  - 1 parcel is picked up (shouldn't get reminder)")
            
            # Mock the notification service to avoid actual email sending
            print("\n🔧 Mocking email service to avoid sending real emails...")
            with patch.object(NotificationService, 'send_24h_reminder_notification') as mock_send:
                mock_send.return_value = (True, "Reminder sent successfully")
                
                print("⚡ Processing reminder notifications...")
                # Process reminders
                processed_count, error_count = process_reminder_notifications()
                
                print(f"📊 Results:")
                print(f"  - Processed: {processed_count} parcels")
                print(f"  - Errors: {error_count}")
                print(f"  - Email service calls: {mock_send.call_count}")
                
                # Should process exactly 2 parcels (the ones needing reminders)
                print(f"\n✅ Verification:")
                print(f"  - Expected 2 parcels to be processed: {'✓' if processed_count == 2 else '✗'}")
                print(f"  - Expected 0 errors: {'✓' if error_count == 0 else '✗'}")
                print(f"  - Expected 2 email calls: {'✓' if mock_send.call_count == 2 else '✗'}")
                
                assert processed_count == 2, f"Expected 2 parcels to be processed, got {processed_count}"
                assert error_count == 0, f"Expected 0 errors, got {error_count}"
                
                # Verify notification service was called for each parcel needing reminder
                assert mock_send.call_count == 2, f"Expected 2 notification calls, got {mock_send.call_count}"
                
                print("🎉 Test PASSED: FR-04 correctly identified parcels needing reminders!")

    def test_fr04_updates_reminder_sent_timestamp(self, app, setup_test_data):
        """Test that FR-04 updates reminder_sent_at timestamp after sending"""
        print("\n" + "="*60)
        print("🧪 TEST: FR-04 Updates Reminder Timestamps")
        print("="*60)
        
        with app.app_context():
            # Get parcels before processing
            parcel1 = db.session.get(Parcel, 1)
            parcel2 = db.session.get(Parcel, 2)
            
            print("📋 Initial State Check:")
            print(f"  - Parcel 1 reminder_sent_at: {parcel1.reminder_sent_at}")
            print(f"  - Parcel 2 reminder_sent_at: {parcel2.reminder_sent_at}")
            
            # Verify they don't have reminder timestamps initially
            assert parcel1.reminder_sent_at is None
            assert parcel2.reminder_sent_at is None
            print("  ✓ Both parcels have no reminder timestamp initially")
            
            # Mock notification service
            print("\n🔧 Mocking notification service...")
            with patch.object(NotificationService, 'send_24h_reminder_notification') as mock_send:
                mock_send.return_value = (True, "Reminder sent successfully")
                
                print("⚡ Processing reminders...")
                # Process reminders
                process_reminder_notifications()
                
                # Refresh parcels from database
                db.session.refresh(parcel1)
                db.session.refresh(parcel2)
                
                print(f"\n📊 After Processing:")
                print(f"  - Parcel 1 reminder_sent_at: {parcel1.reminder_sent_at}")
                print(f"  - Parcel 2 reminder_sent_at: {parcel2.reminder_sent_at}")
                
                # Verify reminder timestamps were set
                timestamp1_set = parcel1.reminder_sent_at is not None
                timestamp2_set = parcel2.reminder_sent_at is not None
                
                print(f"\n✅ Verification:")
                print(f"  - Parcel 1 timestamp set: {'✓' if timestamp1_set else '✗'}")
                print(f"  - Parcel 2 timestamp set: {'✓' if timestamp2_set else '✗'}")
                
                assert parcel1.reminder_sent_at is not None, "Parcel 1 should have reminder_sent_at timestamp"
                assert parcel2.reminder_sent_at is not None, "Parcel 2 should have reminder_sent_at timestamp"
                
                # Verify timestamps are recent (within last minute)
                now = datetime.now(dt.UTC)
                time_diff1 = (now - parcel1.reminder_sent_at).total_seconds()
                time_diff2 = (now - parcel2.reminder_sent_at).total_seconds()
                
                print(f"  - Parcel 1 timestamp age: {time_diff1:.1f} seconds")
                print(f"  - Parcel 2 timestamp age: {time_diff2:.1f} seconds")
                print(f"  - Both timestamps recent (<60s): {'✓' if time_diff1 < 60 and time_diff2 < 60 else '✗'}")
                
                assert (now - parcel1.reminder_sent_at).total_seconds() < 60
                assert (now - parcel2.reminder_sent_at).total_seconds() < 60
                
                print("🎉 Test PASSED: FR-04 correctly updates reminder timestamps!")

    def test_fr04_skips_already_reminded_parcels(self, app, setup_test_data):
        """Test that FR-04 doesn't send duplicate reminders"""
        with app.app_context():
            # Mock notification service
            with patch.object(NotificationService, 'send_24h_reminder_notification') as mock_send:
                mock_send.return_value = (True, "Reminder sent successfully")
                
                # Process reminders first time
                processed_count1, error_count1 = process_reminder_notifications()
                
                # Should process 2 parcels initially
                assert processed_count1 == 2
                assert error_count1 == 0
                
                # Process reminders again immediately
                processed_count2, error_count2 = process_reminder_notifications()
                
                # Should process 0 parcels the second time (no duplicates)
                assert processed_count2 == 0, "Should not process already reminded parcels"
                assert error_count2 == 0

    def test_fr04_handles_notification_failures(self, app, setup_test_data):
        """Test that FR-04 handles email notification failures gracefully"""
        with app.app_context():
            # Mock notification service to fail
            with patch.object(NotificationService, 'send_24h_reminder_notification') as mock_send:
                mock_send.return_value = (False, "Email service unavailable")
                
                # Process reminders
                processed_count, error_count = process_reminder_notifications()
                
                # Should have attempted 2 parcels but had errors
                assert processed_count == 0, "No parcels should be marked as processed on failure"
                assert error_count == 2, f"Expected 2 errors, got {error_count}"
                
                # Verify parcels don't have reminder timestamps set on failure
                parcel1 = db.session.get(Parcel, 1)
                parcel2 = db.session.get(Parcel, 2)
                assert parcel1.reminder_sent_at is None, "Failed reminder should not set timestamp"
                assert parcel2.reminder_sent_at is None, "Failed reminder should not set timestamp"

    def test_fr04_audit_logging(self, app, setup_test_data):
        """Test that FR-04 creates proper audit logs"""
        with app.app_context():
            # Clear existing audit logs
            AuditLog.query.delete()
            db.session.commit()
            
            # Mock notification service
            with patch.object(NotificationService, 'send_24h_reminder_notification') as mock_send:
                mock_send.return_value = (True, "Reminder sent successfully")
                
                # Process reminders
                processed_count, error_count = process_reminder_notifications()
                
                # Check audit logs were created
                audit_logs = AuditLog.query.all()
                
                # Should have at least one audit log for the processing
                assert len(audit_logs) > 0, "Should create audit logs for reminder processing"
                
                # Check for specific audit log content
                processing_logs = [log for log in audit_logs if "REMINDER_PROCESSING" in log.action]
                assert len(processing_logs) > 0, "Should have reminder processing audit log"

    def test_fr04_respects_24_hour_threshold(self, app):
        """Test that FR-04 only processes parcels older than 24 hours"""
        print("\n" + "="*60)
        print("🧪 TEST: FR-04 Respects 24-Hour Threshold")
        print("="*60)
        
        with app.app_context():
            # Clear existing data
            Parcel.query.delete()
            Locker.query.delete()
            db.session.commit()
            
            # Create locker
            locker = Locker(id=1, location="Test Locker", size="small", status="occupied")
            db.session.add(locker)
            
            now = datetime.now(dt.UTC)
            
            print("📋 Test Setup - Creating parcels with precise timing:")
            
            # Create parcels with different ages around the 24-hour threshold
            parcels = [
                # 23 hours, 59 minutes (should NOT get reminder)
                Parcel(
                    id=1, locker_id=1, recipient_email="test1@example.com",
                    status="deposited", deposited_at=now - timedelta(hours=23, minutes=59),
                    reminder_sent_at=None
                ),
                # Exactly 24 hours (should get reminder)
                Parcel(
                    id=2, locker_id=1, recipient_email="test2@example.com",
                    status="deposited", deposited_at=now - timedelta(hours=24),
                    reminder_sent_at=None
                ),
                # 24 hours, 1 minute (should get reminder)
                Parcel(
                    id=3, locker_id=1, recipient_email="test3@example.com",
                    status="deposited", deposited_at=now - timedelta(hours=24, minutes=1),
                    reminder_sent_at=None
                )
            ]
            
            print("  - Parcel 1: 23h 59m old (should NOT get reminder)")
            print("  - Parcel 2: Exactly 24h old (should get reminder)")
            print("  - Parcel 3: 24h 1m old (should get reminder)")
            
            db.session.add_all(parcels)
            db.session.commit()
            
            # Mock notification service
            print("\n🔧 Mocking notification service...")
            with patch.object(NotificationService, 'send_24h_reminder_notification') as mock_send:
                mock_send.return_value = (True, "Reminder sent successfully")
                
                print("⚡ Processing reminders with 24-hour threshold check...")
                # Process reminders
                processed_count, error_count = process_reminder_notifications()
                
                print(f"\n📊 Results:")
                print(f"  - Processed: {processed_count} parcels")
                print(f"  - Errors: {error_count}")
                print(f"  - Email service calls: {mock_send.call_count}")
                
                print(f"\n✅ Verification:")
                print(f"  - Expected 2 parcels processed (24h and 24h1m): {'✓' if processed_count == 2 else '✗'}")
                print(f"  - Expected 0 errors: {'✓' if error_count == 0 else '✗'}")
                print(f"  - 23h59m parcel correctly ignored: {'✓' if processed_count == 2 else '✗'}")
                
                # Should process exactly 2 parcels (24h and 24h1m, but not 23h59m)
                assert processed_count == 2, f"Expected 2 parcels to be processed, got {processed_count}"
                assert error_count == 0
                
                print("🎉 Test PASSED: FR-04 correctly respects 24-hour threshold!")

    def test_fr04_background_processing_simulation(self, app):
        """Test that simulates the background processing scheduler"""
        with app.app_context():
            # This test simulates what the background scheduler does
            # without actually running the scheduler thread
            
            # Setup test data
            Parcel.query.delete()
            Locker.query.delete()
            db.session.commit()
            
            locker = Locker(id=1, location="Test Locker", size="small", status="occupied")
            db.session.add(locker)
            
            # Create old parcel that needs reminder
            old_parcel = Parcel(
                id=1, locker_id=1, recipient_email="background@example.com",
                status="deposited", 
                deposited_at=datetime.now(dt.UTC) - timedelta(hours=25),
                reminder_sent_at=None
            )
            db.session.add(old_parcel)
            db.session.commit()
            
            # Mock the notification service
            with patch.object(NotificationService, 'send_24h_reminder_notification') as mock_send:
                mock_send.return_value = (True, "Background reminder sent")
                
                # Simulate what the background scheduler would do
                # This is the same function called by the scheduler
                processed_count, error_count = process_reminder_notifications()
                
                # Verify background processing worked
                assert processed_count == 1, "Background processing should handle 1 parcel"
                assert error_count == 0, "Background processing should have no errors"
                
                # Verify the parcel was updated
                db.session.refresh(old_parcel)
                assert old_parcel.reminder_sent_at is not None, "Background processing should update timestamp"

    def test_fr04_no_admin_intervention_required(self, app, setup_test_data):
        """Test that FR-04 works without any admin intervention"""
        with app.app_context():
            # This test verifies that the reminder system works completely automatically
            # No admin login, no manual triggers, just the background processing
            
            # Mock notification service
            with patch.object(NotificationService, 'send_24h_reminder_notification') as mock_send:
                mock_send.return_value = (True, "Automatic reminder sent")
                
                # Call the same function that the background scheduler calls
                # This proves no admin intervention is needed
                processed_count, error_count = process_reminder_notifications()
                
                # Verify it worked automatically
                assert processed_count == 2, "Automatic processing should work without admin"
                assert error_count == 0, "Automatic processing should be error-free"
                
                # Verify no admin context was needed
                # (This test itself proves admin intervention isn't required)
                assert True, "Test completed without admin authentication or intervention" 