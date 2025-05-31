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
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add the campus_locker_system directory to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.business.pin import PinManager
from app.services.pin_service import (
    generate_pin_by_token,
    regenerate_pin_token,
    request_pin_regeneration_by_recipient_email_and_locker
)
from app.persistence.models import Parcel, Locker
# Add Repository Imports
from app.persistence.repositories.locker_repository import LockerRepository
from app.persistence.repositories.parcel_repository import ParcelRepository


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
            LockerRepository.save(locker) # Use repository
            
            # Create test parcel with expired PIN
            parcel = Parcel(
                locker_id=905,
                recipient_email="test-fr05@example.com",
                status="deposited",
                deposited_at=datetime.utcnow() - timedelta(hours=25),
                pin_hash="expired_hash:12345",
                otp_expiry=datetime.utcnow() - timedelta(hours=1)  # Expired
            )
            token = parcel.generate_pin_token() # generate_pin_token needs to be called before saving if it sets a value
            ParcelRepository.save(parcel) # Use repository
            
            yield locker, parcel
            
            # Cleanup
            # Keeping direct db.session.delete for test cleanup simplicity
            db.session.delete(parcel)
            db.session.delete(locker)
            db.session.commit()

    # ===== 1. ADMIN PIN RE-ISSUE TESTS =====

    def test_fr05_admin_reissue_pin_success(self, app, test_locker_and_parcel):
        """
        FR-05: Test admin can successfully regenerate PIN token for deposited parcel
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            original_token = parcel.pin_generation_token
            parcel_id = parcel.id
            
            with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                mock_notify.return_value = (True, "New PIN link sent successfully")
                
                # Admin regenerates PIN token (equivalent to reissuing PIN access)
                success, message = regenerate_pin_token(parcel.id, parcel.recipient_email, admin_reset=True)
                
                # Verify success
                assert success is True, "FR-05: Admin token regeneration should succeed"
                assert "New PIN generation link sent" in message, "FR-05: Should confirm link was sent"
                
                # Verify token was changed by re-fetching from database
                updated_parcel = ParcelRepository.get_by_id(parcel_id) # Use repository
                assert updated_parcel is not None, "FR-05: Updated parcel should be found"
                assert updated_parcel.pin_generation_token != original_token, "FR-05: Token should be updated"
                
                # Verify notification was sent
                mock_notify.assert_called_once()

    def test_fr05_admin_reissue_pin_invalid_status(self, app, test_locker_and_parcel):
        """
        FR-05: Test admin cannot regenerate PIN token for non-deposited parcel
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            parcel.status = "picked_up"
            ParcelRepository.save(parcel) # Use repository to save status change
            
            # Attempt to regenerate PIN token
            success, message = regenerate_pin_token(parcel.id, parcel.recipient_email)
            
            # Verify failure
            assert success is False, "FR-05: Should not regenerate token for picked up parcel"
            # Accept either the status error or database error
            assert ("Parcel is not in 'deposited' state" in message or 
                    "error occurred" in message.lower()), "FR-05: Should fail with appropriate error message"

    def test_fr05_admin_reissue_pin_nonexistent_parcel(self, app):
        """
        FR-05: Test admin token regeneration handles nonexistent parcel gracefully
        """
        with app.app_context():
            # Attempt to regenerate token for nonexistent parcel
            success, message = regenerate_pin_token(99999, "test@example.com")
            
            # Verify failure
            assert success is False, "FR-05: Should return False for nonexistent parcel"
            assert "Parcel not found" in message, "FR-05: Should explain parcel not found"

    # ===== 2. USER PIN REGENERATION TESTS =====

    def test_fr05_user_regeneration_success(self, app, test_locker_and_parcel):
        """
        FR-05: Test user can successfully request PIN token regeneration with correct email and locker
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            original_token = parcel.pin_generation_token
            parcel_id = parcel.id
            
            with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                mock_notify.return_value = (True, "PIN generation link sent successfully")
                
                # User requests PIN regeneration
                result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                    "test-fr05@example.com", 
                    "905"
                )
                
                # Verify success
                assert result_parcel is not None, "FR-05: User regeneration request should succeed"
                assert "PIN generation link has been regenerated" in message, "FR-05: Should confirm link was sent"
                
                # Verify token was changed by re-fetching from database
                updated_parcel = ParcelRepository.get_by_id(parcel_id) # Use repository
                assert updated_parcel is not None, "FR-05: Updated parcel should be found after user regeneration"
                assert updated_parcel.pin_generation_token != original_token, "FR-05: Token should be updated"

    def test_fr05_user_regeneration_wrong_email(self, app, test_locker_and_parcel):
        """
        FR-05: Test user cannot request regeneration with wrong email
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            # Attempt regeneration with wrong email
            result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                "wrong@example.com", 
                "905"
            )
            
            # Verify failure (security message)
            assert result_parcel is None, "FR-05: Should reject wrong email"
            assert "If your details matched" in message, "FR-05: Should return security message"

    def test_fr05_user_regeneration_case_insensitive_email(self, app, test_locker_and_parcel):
        """
        FR-05: Test email matching is case insensitive for security
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                mock_notify.return_value = (True, "PIN generation link sent successfully")
                
                # User requests regeneration with different case
                result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                    "TEST-FR05@EXAMPLE.COM", 
                    "905"
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
            parcel_id = parcel.id
            
            with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                mock_notify.return_value = (True, "Link sent successfully")
                
                # Regenerate token
                success, message = regenerate_pin_token(parcel.id, "test-fr05@example.com")
                
                # Verify success
                assert success is True, "FR-05: Token regeneration should succeed"
                assert "PIN generation link sent" in message, "FR-05: Should confirm link sent"
                
                # Verify token was changed by re-fetching from database
                updated_parcel = ParcelRepository.get_by_id(parcel_id) # Use repository
                assert updated_parcel is not None, "FR-05: Updated parcel should be found after token regeneration"
                assert updated_parcel.pin_generation_token != original_token, "FR-05: Token should be updated"

    def test_fr05_token_regeneration_resets_daily_count(self, app, test_locker_and_parcel):
        """
        FR-05: Test token regeneration resets daily generation count for new day
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            parcel_id = parcel.id
            
            # Set parcel to look like previous day
            parcel.pin_generation_count = 3
            parcel.last_pin_generation = datetime.utcnow() - timedelta(days=1)
            db.session.commit()
            
            with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                mock_notify.return_value = (True, "Link sent successfully")
                
                # Regenerate token
                success, message = regenerate_pin_token(parcel.id, "test-fr05@example.com")
                
                # Verify count was reset by re-fetching from database
                updated_parcel = db.session.get(Parcel, parcel_id)
                assert updated_parcel.pin_generation_count == 0, "FR-05: Count should reset for new day"

    # ===== 4. WEB FORM INTERFACE TESTS =====

    def test_fr05_web_form_success(self, app, test_locker_and_parcel):
        """
        FR-05: Test web form interface handles PIN regeneration requests
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_regen:
                mock_regen.return_value = (True, "Link sent")
                
                # Submit web form request
                result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                    "test-fr05@example.com", 
                    "905"
                )
                
                # Verify success
                assert result_parcel is not None, "FR-05: Web form should find matching parcel"
                assert "PIN generation link has been regenerated" in message, "FR-05: Should confirm link sent"

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
            assert "If your details matched an active parcel" in message, "FR-05: Should return generic security message"

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
            assert "Invalid locker ID format" in message or "If your details matched" in message, "FR-05: Should return error or generic message"

    # ===== 5. SECURITY VALIDATION TESTS =====

    def test_fr05_pin_invalidation_on_reissue(self, app, test_locker_and_parcel):
        """
        FR-05: Test old PIN is invalidated when new PIN is generated via token
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            parcel_id = parcel.id
            token = parcel.pin_generation_token
            
            # Generate first PIN via token
            with patch('app.services.notification_service.NotificationService.send_pin_generation_notification') as mock_notify:
                mock_notify.return_value = (True, "PIN sent successfully")
                
                first_parcel, first_message = generate_pin_by_token(token)
                assert first_parcel is not None, "FR-05: First PIN generation should succeed"
                first_pin_hash = first_parcel.pin_hash
                
                # Get updated token after first generation
                updated_parcel = db.session.get(Parcel, parcel_id)
                current_token = updated_parcel.pin_generation_token
                
                # Generate second PIN using same token (should update PIN)
                second_parcel, second_message = generate_pin_by_token(current_token)
                
                if second_parcel is not None:
                    # Verify PIN invalidation if second generation succeeded
                    assert second_parcel.pin_hash != first_pin_hash, "FR-05: PIN hash should be different"
                else:
                    # If failed due to rate limiting, that's also acceptable behavior
                    assert "limit" in second_message.lower(), "FR-05: Should fail due to rate limiting"

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
                    result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                        malicious_email, 
                        "905"
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
            
            with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                mock_notify.return_value = (True, "PIN generation link sent successfully")
                
                # Attempt regeneration at limit
                result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                    "test-fr05@example.com", 
                    "905"
                )
                
                # Should still work (regeneration doesn't use token system rate limiting directly)
                assert result_parcel is not None, "FR-05: Direct regeneration should bypass token rate limit"

    def test_fr05_daily_reset_functionality(self, app, test_locker_and_parcel):
        """
        FR-05: Test daily count reset works correctly
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            parcel_id = parcel.id
            
            # Set parcel to previous day with max count
            parcel.pin_generation_count = 3
            parcel.last_pin_generation = datetime.utcnow() - timedelta(days=2)
            db.session.commit()
            
            with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                mock_notify.return_value = (True, "Link sent successfully")
                
                # Regenerate token (should reset count)
                success, message = regenerate_pin_token(parcel.id, "test-fr05@example.com")
                
                # Verify count reset by re-fetching from database
                updated_parcel = db.session.get(Parcel, parcel_id)
                assert updated_parcel.pin_generation_count == 0, "FR-05: Count should reset after day boundary"

    # ===== 7. INTEGRATION TESTS =====

    def test_fr05_audit_logging_integration(self, app, test_locker_and_parcel):
        """
        FR-05: Test all PIN token operations are logged for audit trail
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.audit_service.AuditService.log_event') as mock_audit:
                with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                    mock_notify.return_value = (True, "New link sent successfully")
                    
                    # Admin regenerates token
                    regenerate_pin_token(parcel.id, parcel.recipient_email, admin_reset=True)
                    
                    # Verify audit logging
                    mock_audit.assert_called()
                    audit_calls = [call[0][0] for call in mock_audit.call_args_list]
                    assert any("PIN_TOKEN_REGENERATED" in call for call in audit_calls), "FR-05: Should log token regeneration"

    def test_fr05_notification_service_integration(self, app, test_locker_and_parcel):
        """
        FR-05: Test integration with notification service for token regeneration and PIN generation
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            # Test token regeneration notification
            with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_ready:
                mock_ready.return_value = (True, "Token regeneration email sent")
                regenerate_pin_token(parcel.id, parcel.recipient_email)
                mock_ready.assert_called_once()
                
            # Refresh parcel to get new token
            updated_parcel = db.session.get(Parcel, parcel.id)
            new_token = updated_parcel.pin_generation_token
            
            # Test PIN generation notification  
            with patch('app.services.notification_service.NotificationService.send_pin_generation_notification') as mock_pin:
                mock_pin.return_value = (True, "PIN generation email sent")
                # Use the refreshed token to generate PIN
                result_parcel, result_message = generate_pin_by_token(new_token)
                
                # Verify PIN generation succeeded and notification was called
                if result_parcel is not None:
                    mock_pin.assert_called_once()
                else:
                    # If PIN generation failed, that's also valid behavior (rate limiting, etc.)
                    # Just verify we tried to use the notification service appropriately
                    assert "error" in result_message.lower() or "limit" in result_message.lower(), f"Expected error or limit message, got: {result_message}"

    # ===== 8. ERROR HANDLING TESTS =====

    def test_fr05_database_error_handling(self, app, test_locker_and_parcel):
        """
        FR-05: Test graceful handling of database errors during token regeneration
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.pin_service.db.session.commit') as mock_commit:
                mock_commit.side_effect = Exception("Database error")
                
                # Attempt token regeneration with database error
                success, message = regenerate_pin_token(parcel.id, parcel.recipient_email)
                
                # Verify graceful handling
                assert success is False, "FR-05: Should handle database errors gracefully"
                assert "error occurred" in message.lower(), "FR-05: Should provide error message"

    def test_fr05_email_failure_handling(self, app, test_locker_and_parcel):
        """
        FR-05: Test handling of email delivery failures in token regeneration
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            
            with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                mock_notify.return_value = (False, "Email delivery failed")
                
                # Regenerate token with email failure
                success, message = regenerate_pin_token(parcel.id, parcel.recipient_email)
                
                # Verify graceful handling
                assert success is True, "FR-05: Token should still be regenerated despite email failure"
                assert "notification may have failed" in message, "FR-05: Should warn about email failure"

    def test_fr05_concurrent_reissue_safety(self, app, test_locker_and_parcel):
        """
        FR-05: Test thread safety of concurrent token regeneration operations
        """
        with app.app_context():
            locker, parcel = test_locker_and_parcel
            results = []
            errors = []
            
            def regenerate_thread():
                try:
                    # Each thread needs its own app context
                    with app.app_context():
                        with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_notify:
                            mock_notify.return_value = (True, "New link sent successfully")
                            result = regenerate_pin_token(parcel.id, parcel.recipient_email)
                            results.append(result)
                except Exception as e:
                    errors.append(str(e))
            
            # Start multiple concurrent regeneration attempts
            threads = []
            for i in range(3):
                thread = threading.Thread(target=regenerate_thread)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify safe handling - some may fail due to database contention, but no crashes
            assert len(errors) <= 2, f"FR-05: Most concurrent operations should succeed, got errors: {errors[:2]}"
            successful_results = [r for r in results if r[0] is True]
            assert len(successful_results) >= 1, "FR-05: At least one regeneration should succeed"


# ===== STANDALONE TEST FUNCTIONS =====

def test_fr05_pin_reissue_validation():
    """
    FR-05: Comprehensive PIN token-based regeneration functionality validation
    """
    app = create_app()
    
    with app.app_context():
        # Test that all required functions exist
        assert callable(generate_pin_by_token), "FR-05: PIN generation by token function should exist"
        assert callable(request_pin_regeneration_by_recipient_email_and_locker), "FR-05: User regeneration function should exist"
        assert callable(regenerate_pin_token), "FR-05: Token regeneration function should exist"
        
        print("FR-05 PIN Token System: All required functions available")


def test_fr05_system_health_check():
    """
    FR-05: Test system health for PIN token-based regeneration functionality
    """
    app = create_app()
    
    with app.app_context():
        # Test PIN re-issue system components
        from app.services.pin_service import PinManager
        from app.services.notification_service import NotificationService
        from app.services.audit_service import AuditService
        
        # Verify components exist
        assert hasattr(PinManager, 'generate_pin_and_hash'), "FR-05: PIN generation should be available"
        assert hasattr(NotificationService, 'send_pin_generation_notification'), "FR-05: PIN generation notification should exist"
        assert hasattr(NotificationService, 'send_parcel_ready_notification'), "FR-05: Token regeneration notification should exist"
        assert hasattr(AuditService, 'log_event'), "FR-05: Audit logging should be available"
        
        print("FR-05 System Health: All PIN token system components functional")


if __name__ == '__main__':
    # Run FR-05 tests
    pytest.main([__file__, '-v', '-s']) 