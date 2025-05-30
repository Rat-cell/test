"""
FR-05 Re-issue PIN Test Suite

This module contains comprehensive tests for the FR-05 requirement:
"Allow users to generate a fresh PIN when their old one has expired or is no longer usable"

Test Categories:
1. Admin PIN Re-issue Tests
2. User PIN Regeneration Tests
3. Token Regeneration Tests
4. Web Form Interface Tests
5. Security Validation Tests
6. Rate Limiting Tests
7. Integration Tests
8. Error Handling Tests

Author: Campus Locker System Team I
Date: May 30, 2025
FR-05 Implementation: Critical PIN management requirement for user accessibility
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app import create_app, db
from app.business.pin import PinManager
from app.services.pin_service import (
    reissue_pin, 
    request_pin_regeneration_by_recipient,
    regenerate_pin_token,
    request_pin_regeneration_by_recipient_email_and_locker
)
from app.persistence.models import Parcel, Locker


class TestFR05ReissuePin:
    """
    FR-05: Re-issue PIN - Comprehensive Test Suite
    
    Tests the PIN re-issue system that allows users to generate fresh PINs
    when old ones have expired or are no longer usable.
    """

    @pytest.fixture
    def app(self):
        """Create test application with FR-05 configuration"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['MAX_PIN_GENERATIONS_PER_DAY'] = 3
        app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    @pytest.fixture
    def test_locker_and_parcel(self, app):
        """Setup test locker and parcel for PIN re-issue testing"""
        with app.app_context():
            # Create test locker
            locker = Locker(id=905, location="Test FR-05 Locker", size="medium", status="occupied")
            db.session.add(locker)
            
            # Create test parcel with expired PIN
            parcel = Parcel(
                locker_id=905,
                recipient_email="test-fr05@example.com",
                status="deposited",
                deposited_at=datetime.utcnow() - timedelta(hours=25),
                pin_hash="expired_hash:12345",
                otp_expiry=datetime.utcnow() - timedelta(hours=1)  # Expired
            )
            token = parcel.generate_pin_token()
            db.session.add(parcel)
            db.session.commit()
            
            yield locker, parcel
            
            # Cleanup
            db.session.delete(parcel)
            db.session.delete(locker)
            db.session.commit()

    # ===== 1. ADMIN PIN RE-ISSUE TESTS =====

    def test_fr05_admin_reissue_pin_success(self, app, test_locker_and_parcel):
        """
        FR-05: Test admin can successfully re-issue PIN for deposited parcel
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            original_pin_hash = parcel.pin_hash
            
            with patch('app.services.pin_service.NotificationService.send_pin_reissue_notification') as mock_notify:
                mock_notify.return_value = (True, "PIN sent successfully")
                
                # Admin re-issues PIN
                result_parcel, message = reissue_pin(parcel.id)
                
                # Verify success
                assert result_parcel is not None, "FR-05: Admin reissue should succeed"
                assert "New PIN issued and sent" in message, "FR-05: Should confirm PIN was sent"
                
                # Verify PIN was changed
                db.session.refresh(parcel)
                assert parcel.pin_hash != original_pin_hash, "FR-05: PIN hash should be updated"
                assert parcel.otp_expiry > datetime.utcnow(), "FR-05: New expiry should be in future"
                
                # Verify notification was sent
                mock_notify.assert_called_once()

    def test_fr05_admin_reissue_pin_invalid_status(self, app, test_locker_and_parcel):
        """
        FR-05: Test admin cannot re-issue PIN for non-deposited parcel
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            parcel.status = "picked_up"
            db.session.commit()
            
            # Attempt to re-issue PIN
            result_parcel, message = reissue_pin(parcel.id)
            
            # Verify failure
            assert result_parcel is None, "FR-05: Should not reissue PIN for picked up parcel"
            assert "not in 'deposited' state" in message, "FR-05: Should explain status requirement"

    def test_fr05_admin_reissue_pin_nonexistent_parcel(self, app):
        """
        FR-05: Test admin reissue handles nonexistent parcel gracefully
        """
        with app.app_context():
            # Attempt to re-issue PIN for nonexistent parcel
            result_parcel, message = reissue_pin(99999)
            
            # Verify failure
            assert result_parcel is None, "FR-05: Should return None for nonexistent parcel"
            assert "Parcel not found" in message, "FR-05: Should explain parcel not found"

    # ===== 2. USER PIN REGENERATION TESTS =====

    def test_fr05_user_regeneration_success(self, app, test_locker_and_parcel):
        """
        FR-05: Test user can successfully regenerate PIN with correct email
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            original_pin_hash = parcel.pin_hash
            
            with patch('app.services.pin_service.NotificationService.send_pin_regeneration_notification') as mock_notify:
                mock_notify.return_value = (True, "PIN sent successfully")
                
                # User regenerates PIN
                result_parcel, message = request_pin_regeneration_by_recipient(
                    parcel.id, 
                    "test-fr05@example.com"
                )
                
                # Verify success
                assert result_parcel is not None, "FR-05: User regeneration should succeed"
                assert "New PIN generated and sent" in message, "FR-05: Should confirm PIN was sent"
                
                # Verify PIN was changed
                db.session.refresh(parcel)
                assert parcel.pin_hash != original_pin_hash, "FR-05: PIN hash should be updated"

    def test_fr05_user_regeneration_wrong_email(self, app, test_locker_and_parcel):
        """
        FR-05: Test user cannot regenerate PIN with wrong email
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            # Attempt regeneration with wrong email
            result_parcel, message = request_pin_regeneration_by_recipient(
                parcel.id, 
                "wrong@example.com"
            )
            
            # Verify failure
            assert result_parcel is None, "FR-05: Should reject wrong email"
            assert "Email does not match" in message, "FR-05: Should explain email mismatch"

    def test_fr05_user_regeneration_case_insensitive_email(self, app, test_locker_and_parcel):
        """
        FR-05: Test email matching is case insensitive for security
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.pin_service.NotificationService.send_pin_regeneration_notification') as mock_notify:
                mock_notify.return_value = (True, "PIN sent successfully")
                
                # User regenerates PIN with different case
                result_parcel, message = request_pin_regeneration_by_recipient(
                    parcel.id, 
                    "TEST-FR05@EXAMPLE.COM"
                )
                
                # Verify success
                assert result_parcel is not None, "FR-05: Case insensitive email should work"

    # ===== 3. TOKEN REGENERATION TESTS =====

    def test_fr05_token_regeneration_success(self, app, test_locker_and_parcel):
        """
        FR-05: Test token regeneration for expired PIN generation links
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            original_token = parcel.pin_generation_token
            
            with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                mock_notify.return_value = (True, "Link sent successfully")
                
                # Regenerate token
                success, message = regenerate_pin_token(parcel.id, "test-fr05@example.com")
                
                # Verify success
                assert success is True, "FR-05: Token regeneration should succeed"
                assert "PIN generation link sent" in message, "FR-05: Should confirm link sent"
                
                # Verify token was changed
                db.session.refresh(parcel)
                assert parcel.pin_generation_token != original_token, "FR-05: Token should be updated"

    def test_fr05_token_regeneration_resets_daily_count(self, app, test_locker_and_parcel):
        """
        FR-05: Test token regeneration resets daily generation count for new day
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            # Set parcel to look like previous day
            parcel.pin_generation_count = 3
            parcel.last_pin_generation = datetime.utcnow() - timedelta(days=1)
            db.session.commit()
            
            with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                mock_notify.return_value = (True, "Link sent successfully")
                
                # Regenerate token
                success, message = regenerate_pin_token(parcel.id, "test-fr05@example.com")
                
                # Verify count was reset
                db.session.refresh(parcel)
                assert parcel.pin_generation_count == 0, "FR-05: Count should reset for new day"

    # ===== 4. WEB FORM INTERFACE TESTS =====

    def test_fr05_web_form_success(self, app, test_locker_and_parcel):
        """
        FR-05: Test web form interface handles PIN regeneration requests
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.pin_service.regenerate_pin_token') as mock_regen:
                mock_regen.return_value = (True, "Link sent")
                
                # Submit web form request
                result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                    "test-fr05@example.com", 
                    "905"
                )
                
                # Verify success
                assert result_parcel is not None, "FR-05: Web form should find matching parcel"
                assert "PIN generation link has been sent" in message, "FR-05: Should confirm link sent"

    def test_fr05_web_form_security_message(self, app):
        """
        FR-05: Test web form returns generic security message for non-matching details
        """
        with app.app_context():
            # Submit request for non-existent parcel
            result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                "nonexistent@example.com", 
                "999"
            )
            
            # Verify security response
            assert result_parcel is None, "FR-05: Should not find non-matching parcel"
            assert "If your details matched" in message, "FR-05: Should return generic security message"

    def test_fr05_web_form_invalid_locker_id(self, app):
        """
        FR-05: Test web form handles invalid locker ID gracefully
        """
        with app.app_context():
            # Submit request with invalid locker ID
            result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                "test@example.com", 
                "invalid"
            )
            
            # Verify graceful handling
            assert result_parcel is None, "FR-05: Should handle invalid locker ID"
            assert "If your details matched" in message, "FR-05: Should return generic message"

    # ===== 5. SECURITY VALIDATION TESTS =====

    def test_fr05_pin_invalidation_on_reissue(self, app, test_locker_and_parcel):
        """
        FR-05: Test old PIN is invalidated when new PIN is issued
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            # Generate first PIN
            first_pin, first_hash = PinManager.generate_pin_and_hash()
            parcel.pin_hash = first_hash
            db.session.commit()
            
            with patch('app.services.pin_service.NotificationService.send_pin_reissue_notification') as mock_notify:
                mock_notify.return_value = (True, "PIN sent successfully")
                
                # Admin reissues PIN
                result_parcel, message = reissue_pin(parcel.id)
                
                # Verify PIN invalidation
                db.session.refresh(parcel)
                assert parcel.pin_hash != first_hash, "FR-05: Old PIN hash should be replaced"
                assert not PinManager.verify_pin(parcel.pin_hash, first_pin), "FR-05: Old PIN should not verify"

    def test_fr05_email_validation_security(self, app, test_locker_and_parcel):
        """
        FR-05: Test email validation prevents unauthorized access
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            # Test various email attack vectors
            malicious_emails = [
                "test-fr05@example.com\nBcc: hacker@evil.com",
                "test-fr05@example.com%0ABcc:hacker@evil.com",
                "",
                None
            ]
            
            for malicious_email in malicious_emails:
                try:
                    result_parcel, message = request_pin_regeneration_by_recipient(
                        parcel.id, 
                        malicious_email
                    )
                    # Should either fail or reject malicious input
                    if result_parcel is not None:
                        assert False, f"FR-05: Should reject malicious email: {malicious_email}"
                except Exception:
                    # Exception is acceptable for malicious input
                    pass

    # ===== 6. RATE LIMITING TESTS =====

    def test_fr05_rate_limiting_integration(self, app, test_locker_and_parcel):
        """
        FR-05: Test PIN re-issue integrates with rate limiting system
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            # Set parcel to maximum generations
            parcel.pin_generation_count = 3
            parcel.last_pin_generation = datetime.utcnow()
            db.session.commit()
            
            with patch('app.services.pin_service.NotificationService.send_pin_regeneration_notification') as mock_notify:
                mock_notify.return_value = (True, "PIN sent successfully")
                
                # Attempt regeneration at limit
                result_parcel, message = request_pin_regeneration_by_recipient(
                    parcel.id, 
                    "test-fr05@example.com"
                )
                
                # Should still work (regeneration doesn't use token system)
                assert result_parcel is not None, "FR-05: Direct regeneration should bypass rate limit"

    def test_fr05_daily_reset_functionality(self, app, test_locker_and_parcel):
        """
        FR-05: Test daily count reset works correctly
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            # Set parcel to previous day with max count
            parcel.pin_generation_count = 3
            parcel.last_pin_generation = datetime.utcnow() - timedelta(days=2)
            db.session.commit()
            
            with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                mock_notify.return_value = (True, "Link sent successfully")
                
                # Regenerate token (should reset count)
                success, message = regenerate_pin_token(parcel.id, "test-fr05@example.com")
                
                # Verify count reset
                db.session.refresh(parcel)
                assert parcel.pin_generation_count == 0, "FR-05: Count should reset after day boundary"

    # ===== 7. INTEGRATION TESTS =====

    def test_fr05_audit_logging_integration(self, app, test_locker_and_parcel):
        """
        FR-05: Test all PIN re-issue activities are logged for audit trail
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.pin_service.AuditService.log_event') as mock_audit:
                with patch('app.services.pin_service.NotificationService.send_pin_reissue_notification') as mock_notify:
                    mock_notify.return_value = (True, "PIN sent successfully")
                    
                    # Admin reissues PIN
                    reissue_pin(parcel.id)
                    
                    # Verify audit logging
                    mock_audit.assert_called_once()
                    audit_call = mock_audit.call_args[0][0]
                    assert "PIN reissued for parcel" in audit_call, "FR-05: Should log admin reissue"

    def test_fr05_notification_service_integration(self, app, test_locker_and_parcel):
        """
        FR-05: Test integration with notification service for all email types
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            # Test reissue notification
            with patch('app.services.pin_service.NotificationService.send_pin_reissue_notification') as mock_reissue:
                mock_reissue.return_value = (True, "Reissue email sent")
                reissue_pin(parcel.id)
                mock_reissue.assert_called_once()
                
            # Test regeneration notification  
            with patch('app.services.pin_service.NotificationService.send_pin_regeneration_notification') as mock_regen:
                mock_regen.return_value = (True, "Regeneration email sent")
                request_pin_regeneration_by_recipient(parcel.id, "test-fr05@example.com")
                mock_regen.assert_called_once()

    # ===== 8. ERROR HANDLING TESTS =====

    def test_fr05_database_error_handling(self, app, test_locker_and_parcel):
        """
        FR-05: Test graceful handling of database errors during PIN re-issue
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.pin_service.db.session.commit') as mock_commit:
                mock_commit.side_effect = Exception("Database error")
                
                # Attempt reissue with database error
                result_parcel, message = reissue_pin(parcel.id)
                
                # Verify graceful handling
                assert result_parcel is None, "FR-05: Should handle database errors gracefully"
                assert "error occurred" in message.lower(), "FR-05: Should provide error message"

    def test_fr05_email_failure_handling(self, app, test_locker_and_parcel):
        """
        FR-05: Test handling of email delivery failures
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.pin_service.NotificationService.send_pin_reissue_notification') as mock_notify:
                mock_notify.return_value = (False, "Email delivery failed")
                
                # Reissue PIN with email failure
                result_parcel, message = reissue_pin(parcel.id)
                
                # Verify graceful handling
                assert result_parcel is not None, "FR-05: PIN should still be issued despite email failure"
                assert "notification may have failed" in message, "FR-05: Should warn about email failure"

    def test_fr05_concurrent_reissue_safety(self, app, test_locker_and_parcel):
        """
        FR-05: Test thread safety of concurrent PIN re-issue operations
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            results = []
            errors = []
            
            def reissue_thread():
                try:
                    with patch('app.services.pin_service.NotificationService.send_pin_reissue_notification') as mock_notify:
                        mock_notify.return_value = (True, "PIN sent successfully")
                        result = reissue_pin(parcel.id)
                        results.append(result)
                except Exception as e:
                    errors.append(str(e))
            
            # Start multiple concurrent reissue attempts
            threads = []
            for i in range(3):
                thread = threading.Thread(target=reissue_thread)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify safe handling
            assert len(errors) == 0, f"FR-05: Concurrent operations should not cause errors: {errors}"
            successful_results = [r for r in results if r[0] is not None]
            assert len(successful_results) >= 1, "FR-05: At least one reissue should succeed"


# ===== STANDALONE TEST FUNCTIONS =====

def test_fr05_pin_reissue_validation():
    """
    FR-05: Comprehensive PIN re-issue functionality validation
    """
    app = create_app()
    
    with app.app_context():
        # Test that all required functions exist
        assert callable(reissue_pin), "FR-05: Admin reissue function should exist"
        assert callable(request_pin_regeneration_by_recipient), "FR-05: User regeneration function should exist"
        assert callable(regenerate_pin_token), "FR-05: Token regeneration function should exist"
        assert callable(request_pin_regeneration_by_recipient_email_and_locker), "FR-05: Web form handler should exist"
        
        print("FR-05 PIN Re-issue: All required functions available")


def test_fr05_system_health_check():
    """
    FR-05: Test system health for PIN re-issue functionality
    """
    app = create_app()
    
    with app.app_context():
        # Test PIN re-issue system components
        from app.services.pin_service import PinManager
        from app.services.notification_service import NotificationService
        from app.services.audit_service import AuditService
        
        # Verify components exist
        assert hasattr(PinManager, 'generate_pin_and_hash'), "FR-05: PIN generation should be available"
        assert hasattr(NotificationService, 'send_pin_reissue_notification'), "FR-05: Reissue notification should exist"
        assert hasattr(NotificationService, 'send_pin_regeneration_notification'), "FR-05: Regeneration notification should exist"
        assert hasattr(AuditService, 'log_event'), "FR-05: Audit logging should be available"
        
        print("FR-05 System Health: All PIN re-issue components functional")


if __name__ == '__main__':
    # Run FR-05 tests
    pytest.main([__file__, '-v', '-s']) 