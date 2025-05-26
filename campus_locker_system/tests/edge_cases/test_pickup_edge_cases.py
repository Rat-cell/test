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
from app.application.services import assign_locker_and_create_parcel, process_pickup, retract_deposit, dispute_pickup
from app import db

# Test: Picking up a parcel that has already been retracted should fail with 'Invalid PIN'
def test_process_pickup_fails_for_retracted_parcel(init_database, app):
    with app.app_context():
        parcel, plain_pin, _ = assign_locker_and_create_parcel('small', 'pickup_retracted_fail@example.com')
        assert parcel is not None
        retract_deposit(parcel.id)
        assert db.session.get(type(parcel), parcel.id).status == 'retracted_by_sender'
        _, _, error = process_pickup(plain_pin)
        assert error is not None
        assert "Invalid PIN" in error

# Test: Picking up a parcel that has been disputed should fail with 'Invalid PIN'
def test_process_pickup_fails_for_disputed_parcel(init_database, app):
    with app.app_context():
        parcel, plain_pin, _ = assign_locker_and_create_parcel('small', 'pickup_disputed_fail@example.com')
        assert parcel is not None
        process_pickup(plain_pin)
        dispute_pickup(parcel.id)
        assert db.session.get(type(parcel), parcel.id).status == 'pickup_disputed'
        _, _, error = process_pickup(plain_pin)
        assert error is not None
        assert "Invalid PIN" in error 