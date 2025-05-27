# Edge Case Coverage Note:
# This file tests invalid state transitions and error handling for the retract deposit API.
# It does NOT cover:
# - Config-driven behaviors (e.g., changing pickup time limit via config)
# - Direct locker status updates via API/sensor
# - Email/mobile confirmation before sending PINs
# - PIN reissue logic (old PIN invalidation, only within window)
# - Return-to-sender after pickup window expiry
# - Explicit test that new PIN expires old PINs

import pytest
from app.services.parcel_service import assign_locker_and_create_parcel, process_pickup
from app.persistence.models import Locker, Parcel, AdminUser
from app import db
from app.services.locker_service import set_locker_status

# Test: API should return 404 or 400 when trying to retract a non-existent parcel
def test_api_retract_deposit_parcel_not_found(client, init_database, app):
    with app.app_context():
        response = client.post('/api/v1/deposit/99999/retract')
        assert response.status_code == 404 or response.status_code == 400
        # Optionally check error message in response

# Test: API should return 400 or 409 when trying to retract a parcel that is not in 'deposited' state (already picked up)
def test_api_retract_deposit_not_deposited(client, init_database, app):
    with app.app_context():
        result = assign_locker_and_create_parcel('retract_not_deposited@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Create a known PIN for testing
        from app.business.pin import PinManager
        test_pin, test_hash = PinManager.generate_pin_and_hash()
        parcel.pin_hash = test_hash
        db.session.commit()
        
        # Simulate pickup (so status is 'picked_up')
        process_pickup(test_pin)
        response = client.post(f'/api/v1/deposit/{parcel.id}/retract')
        assert response.status_code == 400 or response.status_code == 409
        # Optionally check error message in response

# Test: Retracting a deposit when the locker is out_of_service should succeed, but locker remains out_of_service
def test_api_retract_deposit_locker_was_oos(client, init_database, app):
    with app.app_context():
        # Setup: create admin user
        admin = AdminUser(username='edge_admin')
        admin.set_password('edgepass123')
        db.session.add(admin)
        db.session.commit()
        # Setup: deposit parcel
        result = assign_locker_and_create_parcel('retract_oos@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        original_locker_id = parcel.locker_id
        # Mark locker as out_of_service
        set_locker_status(admin.id, admin.username, original_locker_id, 'out_of_service')
        assert db.session.get(Locker, original_locker_id).status == 'out_of_service'
        # Retract deposit
        response = client.post(f'/api/v1/deposit/{parcel.id}/retract')
        assert response.status_code == 200
        # Locker should remain out_of_service
        assert db.session.get(Locker, original_locker_id).status == 'out_of_service' 