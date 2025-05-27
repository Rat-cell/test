# Edge Case Coverage Note:
# This file tests invalid state transitions and error handling for reporting missing parcels.
# It does NOT cover:
# - Config-driven behaviors (e.g., changing pickup time limit via config)
# - Direct locker status updates via API/sensor
# - Email/mobile confirmation before sending PINs
# - PIN reissue logic (old PIN invalidation, only within window)
# - Return-to-sender after pickup window expiry
# - Explicit test that new PIN expires old PINs

import pytest
from app.services.parcel_service import assign_locker_and_create_parcel, process_pickup, report_parcel_missing_by_recipient, process_overdue_parcels
from app import db
from datetime import datetime, timedelta

# Test: Reporting a missing parcel with a non-existent ID should return an error
def test_report_missing_by_recipient_fail_not_found(init_database, app):
    with app.app_context():
        _, error = report_parcel_missing_by_recipient(99999)
        assert error is not None
        assert "Parcel not found" in error

# Test: Reporting a missing parcel in the wrong state (picked_up or expired) should return an error
def test_report_missing_by_recipient_fail_wrong_state(init_database, app):
    with app.app_context():
        # Parcel 'picked_up'
        result = assign_locker_and_create_parcel('missing_wrong_state1@example.com', 'small')
        parcel_picked_up, _ = result
        assert parcel_picked_up is not None
        
        # Create a known PIN for testing
        from app.business.pin import PinManager
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel_picked_up.pin_hash = test_hash
        from app import db
        db.session.commit()
        
        process_pickup(test_pin)
        assert db.session.get(type(parcel_picked_up), parcel_picked_up.id).status == 'picked_up'
        _, error_picked_up = report_parcel_missing_by_recipient(parcel_picked_up.id)
        assert error_picked_up is not None
        assert "cannot be reported missing by recipient from its current state: 'picked_up'" in error_picked_up
        # Parcel 'return_to_sender'
        result2 = assign_locker_and_create_parcel('missing_wrong_state2@example.com', 'small')
        parcel_return_to_sender, _ = result2
        assert parcel_return_to_sender is not None
        parcel_return_to_sender.deposited_at = datetime.utcnow() - timedelta(days=8)
        db.session.commit()
        process_overdue_parcels()
        assert db.session.get(type(parcel_return_to_sender), parcel_return_to_sender.id).status == 'return_to_sender'
        _, error_return_to_sender = report_parcel_missing_by_recipient(parcel_return_to_sender.id)
        assert error_return_to_sender is not None
        assert "cannot be reported missing by recipient from its current state: 'return_to_sender'" in error_return_to_sender 