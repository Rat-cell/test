#!/usr/bin/env python3
"""
PIN Reissue Edge Cases Test Suite
================================

Tests edge cases and error scenarios for PIN reissue functionality.

Test Categories:
1. Invalid Parcel States
2. Expired PINs and Reissue Windows
3. System Configuration Edge Cases
4. Rate Limiting and Security
5. Error Handling and Recovery
"""

import sys
import os
from pathlib import Path

# Add the campus_locker_system directory to the Python path
current_dir = Path(__file__).parent.parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from app.services.parcel_service import assign_locker_and_create_parcel
from app.services.pin_service import generate_pin_by_token, regenerate_pin_token
from app import db
from app.business.pin import PinManager
from app.business.parcel import Parcel

# Test: After PIN regeneration, the old PIN should be invalid and the new PIN should be valid
def test_old_pin_invalid_after_regeneration(init_database, app):
    """Test: After PIN regeneration, the old PIN should be invalid and the new PIN should be valid"""
    with app.app_context():
        # Configure for traditional PIN generation
        app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = False
        
        with patch('app.services.parcel_service.NotificationService.send_parcel_deposit_notification') as mock_deposit:
            with patch('app.services.pin_service.NotificationService.send_pin_reissue_notification') as mock_reissue:
                mock_deposit.return_value = (True, "PIN sent successfully")
                mock_reissue.return_value = (True, "New PIN sent successfully")
                
                # 1. Deposit parcel to get a PIN
                result = assign_locker_and_create_parcel('recipient@example.com', 'small')
                parcel, _ = result
                assert parcel is not None
                
                # Store the old PIN hash
                old_pin_hash = parcel.pin_hash
                
                # Reissue PIN using parcel ID and email
                result = regenerate_pin_token(parcel.id, parcel.recipient_email)
                success, message = result
                assert success is not False
                assert message is not None
                
                # For token-based system, we would check if token was regenerated
                db.session.refresh(parcel)
                # In token-based system, old tokens become invalid when new ones are generated
                
                # Verify the PIN hash changed
                assert parcel.pin_hash != old_pin_hash
                # The old PIN should now be invalid
                # We can't test the actual PIN since we don't know it, but we can verify the hash changed

def test_email_pin_old_pin_invalid_after_regeneration(init_database, app):
    """Test: After email-based PIN regeneration, the old PIN should be invalid and only the new PIN should be valid"""
    with app.app_context():
        # Configure for email-based PIN generation
        app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
        app.config['MAX_PIN_GENERATIONS_PER_DAY'] = 3
        
        # Create parcel with email-based PIN generation
        parcel = Parcel(
            locker_id=1,
            recipient_email='email_regen@example.com',
            status='deposited'
        )
        token = parcel.generate_pin_token()
        db.session.add(parcel)
        db.session.commit()
        
        with patch('app.services.pin_service.NotificationService.send_pin_generation_notification') as mock_pin:
            mock_pin.return_value = (True, "PIN sent successfully")
            
            # Generate first PIN
            result_parcel1, _ = generate_pin_by_token(token)
            assert result_parcel1 is not None
            first_pin_hash = result_parcel1.pin_hash
            
            # Generate second PIN (should invalidate first)
            db.session.refresh(parcel)
            token = parcel.pin_generation_token
            result_parcel2, _ = generate_pin_by_token(token)
            assert result_parcel2 is not None
            second_pin_hash = result_parcel2.pin_hash
            
            # Verify the PIN hash changed
            assert second_pin_hash != first_pin_hash
            assert result_parcel2.pin_generation_count == 2
            
            # The old PIN should now be invalid (hash changed)
            # We can verify this by checking that the hash is different

def test_email_pin_token_regeneration_resets_attempts(init_database, app):
    """Test: Token regeneration should reset daily PIN generation attempts"""
    with app.app_context():
        app.config['ENABLE_EMAIL_BASED_PIN_GENERATION'] = True
        app.config['MAX_PIN_GENERATIONS_PER_DAY'] = 3
        
        # Create parcel that has reached daily limit
        parcel = Parcel(
            locker_id=1,
            recipient_email='reset_attempts@example.com',
            status='deposited',
            pin_generation_count=3,  # At daily limit
            last_pin_generation=datetime.utcnow()
        )
        token = parcel.generate_pin_token()
        db.session.add(parcel)
        db.session.commit()
        
        # Verify PIN generation fails due to rate limit
        result_parcel, message = generate_pin_by_token(token)
        assert result_parcel is None
        assert "Daily PIN generation limit reached" in message
        
        # Admin regenerates token (simulating new day or admin intervention)
        with patch('app.services.pin_service.NotificationService.send_parcel_ready_notification') as mock_ready:
            mock_ready.return_value = (True, "New link sent")
            
            # Simulate time passing (new day)
            parcel.last_pin_generation = datetime.utcnow() - timedelta(days=1)
            db.session.commit()
            
            success, message = regenerate_pin_token(
                parcel.id, 
                'reset_attempts@example.com'
            )
            
            assert success is True
            
            # Verify generation count was reset
            db.session.refresh(parcel)
            assert parcel.pin_generation_count == 0  # Should be reset
            
            # Now PIN generation should work again
            with patch('app.services.pin_service.NotificationService.send_pin_generation_notification') as mock_pin:
                mock_pin.return_value = (True, "PIN sent successfully")
                
                new_token = parcel.pin_generation_token
                result_parcel, message = generate_pin_by_token(new_token)
                
                assert result_parcel is not None
                assert result_parcel.pin_generation_count == 1 