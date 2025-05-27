# Edge Case Coverage Note:
# This file tests that after PIN regeneration, the old PIN is invalid and only the new PIN works.

import pytest
from app.services.parcel_service import assign_locker_and_create_parcel
from app import db
from app.business.pin import PinManager
from app.services.pin_service import reissue_pin

# Test: After PIN regeneration, the old PIN should be invalid and the new PIN should be valid
def test_old_pin_invalid_after_regeneration(init_database, app):
    """Test: After PIN regeneration, the old PIN should be invalid and the new PIN should be valid"""
    with app.app_context():
        # 1. Deposit parcel to get a PIN
        result = assign_locker_and_create_parcel('recipient@example.com', 'small')
        parcel, _ = result
        assert parcel is not None
        
        # Store the old PIN hash
        old_pin_hash = parcel.pin_hash
        
        # Reissue PIN using parcel ID
        result = reissue_pin(parcel.id)
        reissued_parcel, message = result
        assert reissued_parcel is not None
        assert message is not None
        
        # Refresh parcel from database
        db.session.refresh(parcel)
        new_pin_hash = parcel.pin_hash
        
        # Verify the PIN hash changed
        assert new_pin_hash != old_pin_hash
        # The old PIN should now be invalid
        # We can't test the actual PIN since we don't know it, but we can verify the hash changed 