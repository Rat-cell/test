# Edge Case Coverage Note:
# This file tests invalid state transitions and error handling for the dispute pickup API.
# It does NOT cover:
# - Config-driven behaviors (e.g., changing pickup time limit via config)
# - Direct locker status updates via API/sensor
# - Email/mobile confirmation before sending PINs
# - PIN reissue logic (old PIN invalidation, only within window)
# - Return-to-sender after pickup window expiry
# - Explicit test that new PIN expires old PINs

import pytest
from app.services.parcel_service import assign_locker_and_create_parcel, process_pickup, dispute_pickup
from app import db

# Test: Disputing pickup for a non-existent parcel should return an error
def test_dispute_pickup_parcel_not_found(init_database, app):
    with app.app_context():
        _, error = dispute_pickup(99999) # Non-existent parcel ID
        assert error is not None
        assert "Parcel not found" in error

# Test: Disputing pickup for a parcel that has not been picked up should return an error
def test_dispute_pickup_parcel_not_picked_up(init_database, app):
    with app.app_context():
        result = assign_locker_and_create_parcel('dispute_not_pickedup@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        assert parcel.status == 'deposited'
        _, error = dispute_pickup(parcel.id)
        assert error is not None
        assert "not in 'picked_up' state" in error 