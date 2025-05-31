#!/usr/bin/env python3
"""Test PIN flow functionality"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.business.parcel import Parcel
from app.persistence.models import Locker
from app.services.pin_service import generate_pin_by_token, regenerate_pin_token, request_pin_regeneration_by_recipient_email_and_locker
from app.services.parcel_service import assign_locker_and_create_parcel, process_pickup
from app.business.pin import PinManager
from app.services.audit_service import AuditService
from app.persistence.models import AuditLog
import json
import subprocess
import sys
import os
from pathlib import Path

# Add the campus_locker_system directory to the Python path
current_dir = Path(__file__).parent.parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture
def init_database(app):
    """Initialize database with test data"""
    with app.app_context():
        db.create_all()
        
        # Clear existing data to avoid conflicts
        db.session.query(Parcel).delete()
        db.session.query(Locker).delete()
        db.session.commit()
        
        # Create test lockers
        locker1 = Locker(id=1, location='Test Locker 1', size='small', status='free')
        locker2 = Locker(id=2, location='Test Locker 2', size='medium', status='free')
        locker3 = Locker(id=3, location='Test Locker 3', size='large', status='free')
        
        db.session.add(locker1)
        db.session.add(locker2)
        db.session.add(locker3)
        db.session.commit()
        
        yield db
        
        db.drop_all()

class TestTraditionalPinFlow:
    """Test traditional immediate PIN generation flow"""
    
    def test_traditional_pin_deposit_and_pickup_flow(self, init_database, app):
        """Test complete traditional PIN flow: deposit -> PIN sent -> pickup"""
        with app.app_context():
            # Configure for traditional PIN generation
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = False
            
            with patch('app.services.parcel_service.NotificationService.send_parcel_deposit_notification') as mock_notify:
                mock_notify.return_value = (True, "PIN sent successfully")
                
                # Step 1: Deposit parcel (should generate PIN immediately)
                parcel, message = assign_locker_and_create_parcel(
                    recipient_email='traditional@example.com',
                    preferred_size='small'
                )
                
                assert parcel is not None
                assert parcel.pin_hash is not None  # PIN generated immediately
                assert parcel.otp_expiry is not None
                assert parcel.pin_generation_token is None  # No email token
                assert "PIN sent" in message
                
                # Verify notification was called with PIN
                mock_notify.assert_called_once()
                call_args = mock_notify.call_args[1]
                assert 'pin' in call_args
                
                # Step 2: Simulate pickup with correct PIN
                # We need to extract the PIN from the mock call
                sent_pin = call_args['pin']
                pickup_parcel, pickup_message = process_pickup(sent_pin)
                
                assert pickup_parcel is not None
                assert pickup_parcel.id == parcel.id
                assert pickup_parcel.status == 'picked_up'
                assert "successfully picked up" in pickup_message
    
    def test_traditional_pin_reissue_flow(self, init_database, app):
        """Test traditional PIN reissue by admin"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = False
            
            with patch('app.services.parcel_service.NotificationService.send_parcel_deposit_notification') as mock_deposit:
                with patch('app.services.notification_service.NotificationService.send_parcel_ready_notification') as mock_reissue:
                    mock_deposit.return_value = (True, "PIN sent successfully")
                    mock_reissue.return_value = (True, "New PIN token sent successfully")
                    
                    # Create parcel with traditional PIN
                    parcel, _ = assign_locker_and_create_parcel('reissue@example.com', 'small')
                    original_pin_hash = parcel.pin_hash
                    
                    # Regenerate PIN token
                    success, reissue_message = regenerate_pin_token(parcel.id, parcel.recipient_email)
                    
                    assert success is not False
                    assert "PIN generation link sent" in reissue_message or "sent successfully" in reissue_message
                    
                    # Verify reissue notification was called
                    mock_reissue.assert_called_once()

class TestEmailBasedPinFlow:
    """Test email-based PIN generation flow"""
    
    def test_email_pin_deposit_and_generation_flow(self, init_database, app):
        """Test complete email-based PIN flow: deposit -> email link -> generate PIN -> pickup"""
        with app.app_context():
            # Configure for email-based PIN generation
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            app.config['MAX_PIN_GENERATIONS_PER_DAY'] = 3
            
            with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_ready:
                with patch('app.services.pin_service.NotificationService.send_pin_generation_notification') as mock_pin:
                    mock_ready.return_value = (True, "Ready email sent")
                    mock_pin.return_value = (True, "PIN email sent")
                    
                    # Step 1: Deposit parcel (should send email link, no PIN yet)
                    parcel, message = assign_locker_and_create_parcel(
                        recipient_email='email@example.com',
                        preferred_size='medium'
                    )
                    
                    assert parcel is not None
                    assert parcel.pin_hash is None  # No PIN generated yet
                    assert parcel.otp_expiry is None
                    assert parcel.pin_generation_token is not None  # Email token exists
                    assert parcel.pin_generation_token_expiry is not None
                    assert "PIN generation link sent" in message
                    
                    # Verify ready notification was called (without PIN)
                    mock_ready.assert_called_once()
                    
                    # Step 2: Generate PIN using token
                    token = parcel.pin_generation_token
                    pin_parcel, pin_message = generate_pin_by_token(token)
                    
                    assert pin_parcel is not None
                    assert pin_parcel.id == parcel.id
                    assert pin_parcel.pin_hash is not None  # PIN now generated
                    assert pin_parcel.otp_expiry is not None
                    assert pin_parcel.pin_generation_count == 1
                    assert pin_parcel.last_pin_generation is not None
                    assert "PIN generated successfully" in pin_message
                    
                    # Verify PIN notification was called
                    mock_pin.assert_called_once()
                    
                    # Step 3: Simulate pickup with generated PIN
                    sent_pin = mock_pin.call_args[1]['pin']
                    pickup_parcel, pickup_message = process_pickup(sent_pin)
                    
                    assert pickup_parcel is not None
                    assert pickup_parcel.id == parcel.id
                    assert pickup_parcel.status == 'picked_up'
                    assert "successfully picked up" in pickup_message
    
    def test_email_pin_multiple_generations(self, init_database, app):
        """Test multiple PIN generations within daily limit"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            app.config['MAX_PIN_GENERATIONS_PER_DAY'] = 3
            
            # Create parcel with email-based PIN
            parcel = Parcel(
                locker_id=1,
                recipient_email='multi@example.com',
                status='deposited'
            )
            token = parcel.generate_pin_token()
            db.session.add(parcel)
            db.session.commit()
            
            with patch('app.services.pin_service.NotificationService.send_pin_generation_notification') as mock_pin:
                mock_pin.return_value = (True, "PIN sent successfully")
                
                # Generate PIN 3 times (within limit)
                for i in range(3):
                    result_parcel, message = generate_pin_by_token(token)
                    assert result_parcel is not None
                    assert result_parcel.pin_generation_count == i + 1
                    
                    # Refresh token for next generation
                    db.session.refresh(parcel)
                    token = parcel.pin_generation_token
                
                # 4th attempt should fail (rate limit)
                result_parcel, message = generate_pin_by_token(token)
                assert result_parcel is None
                assert "Daily PIN generation limit reached" in message
    
    def test_email_pin_token_regeneration_flow(self, init_database, app):
        """Test admin regeneration of PIN token"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            
            # Create parcel
            parcel = Parcel(
                locker_id=1,
                recipient_email='regen@example.com',
                status='deposited'
            )
            old_token = parcel.generate_pin_token()
            db.session.add(parcel)
            db.session.commit()
            
            with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_ready:
                mock_ready.return_value = (True, "New link sent")
                
                # Regenerate token
                success, message = regenerate_pin_token(
                    parcel.id, 
                    'regen@example.com'
                )
                
                assert success is True
                assert "New PIN generation link sent" in message
                
                # Verify token was changed
                db.session.refresh(parcel)
                assert parcel.pin_generation_token != old_token
                
                # Verify notification was called
                mock_ready.assert_called_once()

    def test_email_pin_rate_limiting_integration(self, init_database, app):
        """Test email-based PIN generation rate limiting"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            app.config['MAX_PIN_GENERATIONS_PER_DAY'] = 2  # Lower limit for testing
            
            # Create parcel with email-based PIN
            parcel = Parcel(
                locker_id=1,
                recipient_email='rate_limit@example.com',
                status='deposited'
            )
            token = parcel.generate_pin_token()
            db.session.add(parcel)
            db.session.commit()
            
            # Generate PIN twice (within limit)
            with patch('app.services.pin_service.NotificationService.send_pin_generation_notification') as mock_pin:
                mock_pin.return_value = (True, "PIN sent successfully")
                
                for i in range(2):
                    result_parcel, message = generate_pin_by_token(token)
                    assert result_parcel is not None
                    assert result_parcel.pin_generation_count == i + 1
                    
                    # Refresh token for next generation
                    db.session.refresh(parcel)
                    token = parcel.pin_generation_token
                
                # Third attempt should fail (rate limit)
                result_parcel, message = generate_pin_by_token(token)
                assert result_parcel is None
                assert "Daily PIN generation limit reached" in message

    def test_email_pin_pickup_integration(self, init_database, app):
        """Test pickup with email-generated PIN"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            
            # Create parcel and generate PIN
            parcel = Parcel(
                locker_id=1,
                recipient_email='pickup_test@example.com',
                status='deposited'
            )
            token = parcel.generate_pin_token()
            db.session.add(parcel)
            db.session.commit()
            
            # Generate PIN
            with patch('app.services.pin_service.NotificationService.send_pin_generation_notification') as mock_pin:
                mock_pin.return_value = (True, "PIN sent successfully")
                
                pin_parcel, _ = generate_pin_by_token(token)
                assert pin_parcel is not None
                
                # Extract PIN from the generated hash for testing
                # In real scenario, PIN would be sent via email
                # For testing, we'll generate a known PIN
                test_pin, test_hash = PinManager.generate_pin_and_hash()
                pin_parcel.pin_hash = test_hash
                db.session.commit()
                
                # Test pickup with the PIN
                pickup_parcel, pickup_message = process_pickup(test_pin)
                
                assert pickup_parcel is not None
                assert pickup_parcel.id == parcel.id
                assert pickup_parcel.status == 'picked_up'
                assert "successfully picked up" in pickup_message

    def test_email_pin_admin_token_regeneration_integration(self, init_database, app):
        """Test admin regeneration of email PIN tokens"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            
            # Create parcel
            parcel = Parcel(
                locker_id=1,
                recipient_email='admin_regen@example.com',
                status='deposited'
            )
            old_token = parcel.generate_pin_token()
            db.session.add(parcel)
            db.session.commit()
            
            # Admin regenerates token
            with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_ready:
                mock_ready.return_value = (True, "New link sent")
                
                success, message = regenerate_pin_token(
                    parcel.id, 
                    'admin_regen@example.com'
                )
                
                assert success is True
                assert "New PIN generation link sent" in message
                
                # Verify token was changed
                db.session.refresh(parcel)
                assert parcel.pin_generation_token != old_token

    def test_email_pin_generation_workflow_integration(self, init_database, app):
        """Test complete email-based PIN generation workflow"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            app.config['MAX_PIN_GENERATIONS_PER_DAY'] = 3
            
            # Step 1: Create parcel with email-based PIN
            with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_ready:
                mock_ready.return_value = (True, "Email link sent")
                
                parcel, _ = assign_locker_and_create_parcel('workflow@example.com', 'medium')
                assert parcel.pin_generation_token is not None
            
            # Step 2: Generate PIN using token
            token = parcel.pin_generation_token
            with patch('app.services.pin_service.NotificationService.send_pin_generation_notification') as mock_pin:
                mock_pin.return_value = (True, "PIN sent successfully")
                
                pin_parcel, pin_message = generate_pin_by_token(token)
                
                assert pin_parcel is not None
                assert pin_parcel.pin_hash is not None
                assert pin_parcel.pin_generation_count == 1
                assert "PIN generated successfully" in pin_message

    def test_recipient_pin_regeneration_email_based_system(self, init_database, app):
        """Test recipient PIN regeneration request for email-based PIN system"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            
            # Create parcel with email-based PIN
            parcel = Parcel(
                locker_id=1,
                recipient_email='regeneration_test@example.com',
                status='deposited'
            )
            token = parcel.generate_pin_token()
            db.session.add(parcel)
            db.session.commit()
            
            with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_ready:
                mock_ready.return_value = (True, "New link sent")
                
                # Test recipient PIN regeneration request
                result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                    'regeneration_test@example.com', '1'
                )
                
                assert result_parcel is not None
                assert "PIN generation link has been sent" in message
                
                # Verify token was regenerated
                db.session.refresh(parcel)
                assert parcel.pin_generation_token != token

    def test_recipient_pin_regeneration_traditional_system(self, init_database, app):
        """Test recipient PIN regeneration request for traditional PIN system"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = False
            
            with patch('app.services.parcel_service.NotificationService.send_parcel_deposit_notification') as mock_deposit:
                mock_deposit.return_value = (True, "PIN sent successfully")
                
                # Create parcel with traditional PIN
                parcel, _ = assign_locker_and_create_parcel('traditional_regen@example.com', 'small')
                original_pin_hash = parcel.pin_hash
                
                with patch('app.services.pin_service.NotificationService.send_pin_regeneration_notification') as mock_regen:
                    mock_regen.return_value = (True, "New PIN sent")
                    
                    # Test recipient PIN regeneration request
                    result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                        'traditional_regen@example.com', '1'
                    )
                    
                    assert result_parcel is not None
                    assert "New PIN generated" in message
                    
                    # Verify PIN was changed
                    db.session.refresh(parcel)
                    assert parcel.pin_hash != original_pin_hash

    def test_recipient_pin_regeneration_security(self, init_database, app):
        """Test security aspects of recipient PIN regeneration"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            
            # Create parcel
            parcel = Parcel(
                locker_id=1,
                recipient_email='security_test@example.com',
                status='deposited'
            )
            parcel.generate_pin_token()
            db.session.add(parcel)
            db.session.commit()
            
            from app.services.pin_service import request_pin_regeneration_by_recipient_email_and_locker
            
            # Test with wrong email
            result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                'wrong_email@example.com', '1'
            )
            assert result_parcel is None
            assert "If your details matched" in message  # Generic security message
            
            # Test with wrong locker ID
            result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                'security_test@example.com', '999'
            )
            assert result_parcel is None
            assert "If your details matched" in message  # Generic security message
            
            # Test with invalid locker ID format
            result_parcel, message = request_pin_regeneration_by_recipient_email_and_locker(
                'security_test@example.com', 'invalid'
            )
            assert result_parcel is None
            assert "If your details matched" in message  # Generic security message

class TestPinFlowEdgeCases:
    """Test edge cases and error conditions in PIN flows"""
    
    def test_pickup_with_expired_pin(self, init_database, app):
        """Test pickup attempt with expired PIN"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = False
            
            # Create parcel with expired PIN
            pin, pin_hash = PinManager.generate_pin_and_hash()
            parcel = Parcel(
                locker_id=1,
                recipient_email='expired@example.com',
                pin_hash=pin_hash,
                otp_expiry=datetime.utcnow() - timedelta(hours=1),  # Expired
                status='deposited'
            )
            db.session.add(parcel)
            db.session.commit()
            
            # Attempt pickup with expired PIN
            pickup_parcel, pickup_message = process_pickup(pin)
            
            assert pickup_parcel is None
            assert "PIN has expired" in pickup_message
    
    def test_pickup_with_invalid_pin(self, init_database, app):
        """Test pickup attempt with invalid PIN"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = False
            
            with patch('app.services.parcel_service.NotificationService.send_parcel_deposit_notification') as mock_notify:
                mock_notify.return_value = (True, "PIN sent successfully")
                
                # Create parcel
                parcel, _ = assign_locker_and_create_parcel('invalid@example.com', 'small')
                
                # Attempt pickup with wrong PIN
                pickup_parcel, pickup_message = process_pickup('999999')
                
                assert pickup_parcel is None
                assert "Invalid PIN" in pickup_message
    
    def test_email_pin_expired_token(self, init_database, app):
        """Test PIN generation with expired token"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            
            # Create parcel with expired token
            parcel = Parcel(
                locker_id=1,
                recipient_email='expired_token@example.com',
                status='deposited',
                pin_generation_token='expired_token',
                pin_generation_token_expiry=datetime.utcnow() - timedelta(hours=1)
            )
            db.session.add(parcel)
            db.session.commit()
            
            # Attempt PIN generation with expired token
            result_parcel, message = generate_pin_by_token('expired_token')
            
            assert result_parcel is None
            assert "Token has expired" in message
    
    def test_email_pin_wrong_parcel_status(self, init_database, app):
        """Test PIN generation for parcel with wrong status"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            
            # Create parcel with wrong status
            parcel = Parcel(
                locker_id=1,
                recipient_email='wrong_status@example.com',
                status='picked_up'  # Wrong status
            )
            token = parcel.generate_pin_token()
            db.session.add(parcel)
            db.session.commit()
            
            # Attempt PIN generation
            result_parcel, message = generate_pin_by_token(token)
            
            assert result_parcel is None
            assert "not available for pickup" in message

    def test_email_pin_token_expiry_integration(self, init_database, app):
        """Test email-based PIN generation token expiry"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            
            # Create parcel with expired token
            parcel = Parcel(
                locker_id=1,
                recipient_email='expired@example.com',
                status='deposited',
                pin_generation_token='expired_token',
                pin_generation_token_expiry=datetime.utcnow() - timedelta(hours=1)
            )
            db.session.add(parcel)
            db.session.commit()
            
            # Attempt PIN generation with expired token
            result_parcel, message = generate_pin_by_token('expired_token')
            
            assert result_parcel is None
            assert "Token has expired" in message

class TestPinFlowIntegration:
    """Integration tests covering complete PIN workflows"""
    
    def test_configuration_switch_between_pin_systems(self, init_database, app):
        """Test that configuration properly switches between PIN systems"""
        with app.app_context():
            # Test traditional system
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = False
            
            with patch('app.services.parcel_service.NotificationService.send_parcel_deposit_notification') as mock_traditional:
                mock_traditional.return_value = (True, "PIN sent successfully")
                
                parcel1, message1 = assign_locker_and_create_parcel('traditional@example.com', 'small')
                
                assert parcel1.pin_hash is not None  # Immediate PIN
                assert parcel1.pin_generation_token is None  # No email token
                assert "PIN sent" in message1
            
            # Switch to email-based system
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            
            with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_email:
                mock_email.return_value = (True, "Email link sent")
                
                parcel2, message2 = assign_locker_and_create_parcel('email@example.com', 'medium')
                
                assert parcel2.pin_hash is None  # No immediate PIN
                assert parcel2.pin_generation_token is not None  # Email token exists
                assert "PIN generation link sent" in message2
    
    def test_old_pin_invalidation_after_regeneration(self, init_database, app):
        """Test that old PINs are invalidated when new ones are generated"""
        with app.app_context():
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            
            # Create parcel and generate first PIN
            parcel = Parcel(
                locker_id=1,
                recipient_email='invalidation@example.com',
                status='deposited'
            )
            token = parcel.generate_pin_token()
            db.session.add(parcel)
            db.session.commit()
            
            with patch('app.services.pin_service.NotificationService.send_pin_generation_notification') as mock_pin:
                mock_pin.return_value = (True, "PIN sent successfully")
                
                # Generate first PIN
                result_parcel1, _ = generate_pin_by_token(token)
                first_pin = mock_pin.call_args[1]['pin']
                first_pin_hash = result_parcel1.pin_hash
                
                # Generate second PIN (should invalidate first)
                db.session.refresh(parcel)
                token = parcel.pin_generation_token
                result_parcel2, _ = generate_pin_by_token(token)
                second_pin = mock_pin.call_args[1]['pin']
                second_pin_hash = result_parcel2.pin_hash
                
                # Verify PINs are different
                assert first_pin != second_pin
                assert first_pin_hash != second_pin_hash
                
                # Verify only the latest PIN works for pickup
                pickup_result1, pickup_message1 = process_pickup(first_pin)
                assert pickup_result1 is None  # Old PIN should not work
                
                pickup_result2, pickup_message2 = process_pickup(second_pin)
                assert pickup_result2 is not None  # New PIN should work
                assert pickup_result2.status == 'picked_up'

    def test_email_pin_vs_traditional_pin_audit_logging(self, init_database, app):
        """Test that both PIN systems generate appropriate audit logs"""
        with app.app_context():
            # Test traditional PIN audit logging
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = False
            
            with patch('app.services.parcel_service.NotificationService.send_parcel_deposit_notification') as mock_traditional:
                mock_traditional.return_value = (True, "PIN sent successfully")
                
                traditional_parcel, _ = assign_locker_and_create_parcel('traditional_audit@example.com', 'small')
                
                # Check for traditional PIN audit log
                traditional_log = AuditLog.query.filter(
                    AuditLog.action.contains("Parcel")
                ).order_by(AuditLog.timestamp.desc()).first()
                assert traditional_log is not None
            
            # Test email-based PIN audit logging
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            
            with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_email:
                mock_email.return_value = (True, "Email link sent")
                
                email_parcel, _ = assign_locker_and_create_parcel('email_audit@example.com', 'medium')
                
                # Generate PIN to create audit log
                token = email_parcel.pin_generation_token
                with patch('app.services.pin_service.NotificationService.send_pin_generation_notification') as mock_pin:
                    mock_pin.return_value = (True, "PIN sent successfully")
                    generate_pin_by_token(token)
                
                # Check for email PIN generation audit log
                email_log = AuditLog.query.filter_by(action="PIN_GENERATED_VIA_EMAIL").first()
                assert email_log is not None
                
                details = json.loads(email_log.details)
                assert details['parcel_id'] == email_parcel.id

    def test_email_pin_generation_enabled_configuration(self, init_database, app):
        """Test that email-based PIN generation works when enabled"""
        with app.app_context():
            # Configure for email-based PIN generation
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
            app.config['MAX_PIN_GENERATIONS_PER_DAY'] = 3
            
            with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_ready:
                mock_ready.return_value = (True, "Email link sent")
                
                # Create parcel with email-based PIN generation
                parcel, message = assign_locker_and_create_parcel('email_pin@example.com', 'small')
                
                assert parcel is not None
                assert parcel.pin_hash is None  # No immediate PIN
                assert parcel.pin_generation_token is not None  # Email token exists
                assert parcel.pin_generation_token_expiry is not None
                assert "PIN generation link sent" in message

    def test_email_pin_generation_disabled_configuration(self, init_database, app):
        """Test that traditional PIN generation works when email-based is disabled"""
        with app.app_context():
            # Configure for traditional PIN generation
            app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = False
            
            with patch('app.services.parcel_service.NotificationService.send_parcel_deposit_notification') as mock_traditional:
                mock_traditional.return_value = (True, "PIN sent successfully")
                
                # Create parcel with traditional PIN generation
                parcel, message = assign_locker_and_create_parcel('traditional_pin@example.com', 'small')
                
                assert parcel is not None
                assert parcel.pin_hash is not None  # Immediate PIN
                assert parcel.pin_generation_token is None  # No email token
                assert "PIN sent" in message


# ============================================================================
# PIN TEST RUNNER - Consolidated test execution functionality
# ============================================================================

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def run_pin_tests():
    """
    PIN Testing Suite Runner for Campus Locker System v2.2
    
    This function runs comprehensive tests for both traditional and email-based PIN generation systems.
    All PIN-related tests are organized into two main categories:
    - Flow tests: Complete workflows and integration tests (test_pin_flow.py)
    - Edge cases: Error conditions and boundary testing (test_pin_reissue_edge_cases.py)
    
    Usage:
        python -c "from tests.flow.test_pin_flow import run_pin_tests; run_pin_tests()"
        
    Or run specific categories:
        python -m pytest tests/flow/test_pin_flow.py -v
        python -m pytest tests/edge_cases/test_pin_reissue_edge_cases.py -v
    """
    print("🧪 Campus Locker System v2.2 - PIN Testing Suite")
    print("=" * 60)
    
    # Change to the project root directory
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Available test categories
    test_categories = {
        'flow': {
            'description': 'PIN Flow Tests (Traditional & Email-based workflows)',
            'files': ['tests/flow/test_pin_flow.py'],
            'focus': 'Complete PIN workflows, integration tests, pickup flows'
        },
        'edge': {
            'description': 'PIN Edge Cases (Error conditions & boundary tests)',
            'files': ['tests/edge_cases/test_pin_reissue_edge_cases.py'],
            'focus': 'PIN invalidation, rate limiting, token expiry'
        },
        'presentation': {
            'description': 'PIN Presentation Layer Tests (UI & Routes)',
            'files': ['tests/test_presentation.py'],
            'focus': 'Email PIN generation routes, admin UI, deposit confirmation'
        },
        'all': {
            'description': 'All PIN-related Tests',
            'files': [
                'tests/flow/test_pin_flow.py',
                'tests/edge_cases/test_pin_reissue_edge_cases.py',
                'tests/test_presentation.py::test_generate_pin_by_token_success',
                'tests/test_presentation.py::test_generate_pin_by_token_invalid_token',
                'tests/test_presentation.py::test_generate_pin_by_token_rate_limit',
                'tests/test_presentation.py::test_generate_pin_by_token_exception_handling',
                'tests/test_presentation.py::test_admin_regenerate_pin_token_success',
                'tests/test_presentation.py::test_admin_regenerate_pin_token_parcel_not_found',
                'tests/test_presentation.py::test_admin_regenerate_pin_token_email_disabled',
                'tests/test_presentation.py::test_deposit_confirmation_email_pin_display',
                'tests/test_presentation.py::test_deposit_confirmation_traditional_pin_display',
                'tests/test_presentation.py::test_admin_view_parcel_email_pin_information',
                'tests/test_presentation.py::test_admin_view_parcel_traditional_pin_information'
            ],
            'focus': 'Complete PIN system coverage'
        }
    }
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        category = sys.argv[1].lower()
        if category not in test_categories:
            print(f"❌ Invalid category: {category}")
            print(f"Available categories: {', '.join(test_categories.keys())}")
            return 1
    else:
        # Show available categories and prompt user
        print("\nAvailable test categories:")
        for cat, info in test_categories.items():
            print(f"  {cat:12} - {info['description']}")
            print(f"               Focus: {info['focus']}")
        
        category = input("\nEnter test category (or 'all' for everything): ").lower().strip()
        if category not in test_categories:
            print(f"❌ Invalid category: {category}")
            return 1
    
    # Get test configuration
    test_config = test_categories[category]
    test_files = test_config['files']
    
    print(f"\n🎯 Running: {test_config['description']}")
    print(f"📋 Focus: {test_config['focus']}")
    print(f"📁 Files: {len(test_files)} test file(s)")
    
    # Check for additional options
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    coverage = '--coverage' in sys.argv or '-c' in sys.argv
    
    # Build pytest command
    pytest_cmd = ['python', '-m', 'pytest']
    
    if verbose:
        pytest_cmd.append('-v')
    else:
        pytest_cmd.append('-q')
    
    if coverage:
        pytest_cmd.extend(['--cov=app', '--cov-report=term-missing'])
    
    # Add test files
    pytest_cmd.extend(test_files)
    
    # Run the tests
    success = run_command(
        pytest_cmd,
        f"{test_config['description']} ({'with coverage' if coverage else 'standard'})"
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    
    if success:
        print("✅ All PIN tests passed successfully!")
        print(f"📋 Category: {category}")
        print(f"📁 Files tested: {len(test_files)}")
        
        if category == 'all':
            print("\n🎉 Complete PIN system validation successful!")
            print("   ✓ Traditional PIN generation and pickup")
            print("   ✓ Email-based PIN generation and pickup")
            print("   ✓ Rate limiting and security features")
            print("   ✓ Admin token regeneration")
            print("   ✓ Edge cases and error handling")
            print("   ✓ UI and presentation layer")
        
        return 0
    else:
        print("❌ Some tests failed!")
        print("💡 Check the output above for details")
        return 1


if __name__ == '__main__':
    """
    Allow running this file directly to execute PIN tests
    
    Usage:
        python tests/flow/test_pin_flow.py [category] [--verbose] [--coverage]
        
    Examples:
        python tests/flow/test_pin_flow.py all
        python tests/flow/test_pin_flow.py flow --verbose
        python tests/flow/test_pin_flow.py edge --coverage
    """
    exit_code = run_pin_tests()
    sys.exit(exit_code) 