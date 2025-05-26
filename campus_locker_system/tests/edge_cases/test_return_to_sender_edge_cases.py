# Edge Case Coverage Note:
# This file tests the return-to-sender process after pickup window expiry.

import pytest
from app.application.services import assign_locker_and_create_parcel, process_overdue_parcels, process_pickup
from app import db
from datetime import datetime, timedelta

# Test: After pickup window expiry, parcel status is 'return_to_sender' and locker is 'awaiting_collection' if not free
def test_return_to_sender_status_and_locker_state(init_database, app):
    with app.app_context():
        parcel, pin, _ = assign_locker_and_create_parcel('small', 'rts_edgecase@example.com')
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
        parcel, pin, _ = assign_locker_and_create_parcel('small', 'rts_blocked@example.com')
        assert parcel is not None
        # Simulate overdue and process
        parcel.deposited_at = datetime.utcnow() - timedelta(days=8)
        db.session.commit()
        process_overdue_parcels()
        db.session.refresh(parcel)
        # Try to pick up with the original PIN
        _, _, error = process_pickup(pin)
        assert error is not None
        assert 'Invalid PIN' in error or 'not in' in error 