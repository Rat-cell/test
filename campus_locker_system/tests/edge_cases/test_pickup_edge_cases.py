# Edge Case Coverage Note:
# This file tests invalid state transitions and error handling for the pickup process.
# It does NOT cover:
# - Config-driven behaviors (e.g., changing pickup time limit via config)
# - Direct locker status updates via API/sensor
# - Email/mobile confirmation before sending PINs
# - PIN reissue logic (old PIN invalidation, only within window)
# - Return-to-sender after pickup window expiry
# - Explicit test that new PIN expires old PINs

import pytest
from app.services.parcel_service import assign_locker_and_create_parcel, process_pickup, retract_deposit, dispute_pickup
from app import db

# Test: Picking up a parcel that has already been retracted should fail with 'Invalid PIN'
def test_process_pickup_fails_for_retracted_parcel(init_database, app):
    with app.app_context():
        result = assign_locker_and_create_parcel('pickup_retracted_fail@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Create a known PIN for testing
        from app.business.pin import PinManager
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        retract_deposit(parcel.id)
        assert db.session.get(type(parcel), parcel.id).status == 'retracted_by_sender'
        
        pickup_result = process_pickup(test_pin)
        picked_parcel, pickup_message = pickup_result
        assert picked_parcel is None
        assert "Invalid PIN" in pickup_message

# Test: Picking up a parcel that has been disputed should fail with 'Invalid PIN'
def test_process_pickup_fails_for_disputed_parcel(init_database, app):
    with app.app_context():
        result = assign_locker_and_create_parcel('pickup_disputed_fail@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Create a known PIN for testing
        from app.business.pin import PinManager
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        process_pickup(test_pin)
        dispute_pickup(parcel.id)
        assert db.session.get(type(parcel), parcel.id).status == 'pickup_disputed'
        
        pickup_result = process_pickup(test_pin)
        picked_parcel, pickup_message = pickup_result
        assert picked_parcel is None
        assert "Invalid PIN" in pickup_message 