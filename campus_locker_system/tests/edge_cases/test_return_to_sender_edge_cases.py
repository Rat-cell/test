# Edge Case Coverage Note:
# This file tests the return-to-sender process after pickup window expiry.

import pytest
from app.services.parcel_service import assign_locker_and_create_parcel, process_overdue_parcels, process_pickup
from app import db
from datetime import datetime, timedelta

# Test: After pickup window expiry, parcel status is 'return_to_sender' and locker is 'awaiting_collection' if not free
def test_return_to_sender_status_and_locker_state(init_database, app):
    with app.app_context():
        result = assign_locker_and_create_parcel('rts_edgecase@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        locker = parcel.locker
        # Simulate overdue
        parcel.deposited_at = datetime.utcnow() - timedelta(days=8)
        locker.status = 'occupied'
        db.session.commit()
        process_overdue_parcels()
        db.session.refresh(parcel)
        db.session.refresh(locker)
        assert parcel.status == 'return_to_sender'
        assert locker.status == 'awaiting_collection'

# Test: Recipient cannot pick up a parcel in 'return_to_sender' state
def test_pickup_blocked_for_return_to_sender(init_database, app):
    with app.app_context():
        result = assign_locker_and_create_parcel('rts_blocked@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        # Simulate overdue and process
        parcel.deposited_at = datetime.utcnow() - timedelta(days=8)
        db.session.commit()
        process_overdue_parcels()
        db.session.refresh(parcel)
        # Create a known PIN for testing
        from app.business.pin import PinManager
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        # Try to pick up (should fail)
        pickup_result = process_pickup(test_pin)
        picked_parcel, pickup_message = pickup_result
        assert picked_parcel is None
        assert 'Invalid PIN' in pickup_message or 'not in' in pickup_message 