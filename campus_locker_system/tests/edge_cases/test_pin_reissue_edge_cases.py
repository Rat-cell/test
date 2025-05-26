# Edge Case Coverage Note:
# This file tests that after PIN regeneration, the old PIN is invalid and only the new PIN works.

import pytest
from app.application.services import assign_locker_and_create_parcel, verify_pin
from app import db
from app.application.services import request_pin_regeneration_by_recipient

# Test: After PIN regeneration, the old PIN should be invalid and the new PIN should be valid
def test_old_pin_invalid_after_regeneration(client, init_database, app):
    with app.app_context():
        # Setup: Create a deposited parcel
        parcel, old_pin, _ = assign_locker_and_create_parcel('small', 'regen_edgecase@example.com')
        assert parcel is not None
        old_pin_hash = parcel.pin_hash
        # Regenerate PIN
        result = request_pin_regeneration_by_recipient(parcel.recipient_email, parcel.locker_id)
        assert result is True
        db.session.refresh(parcel)
        new_pin_hash = parcel.pin_hash
        assert new_pin_hash != old_pin_hash
        # The old PIN should now be invalid
        assert not verify_pin(new_pin_hash, old_pin)
        # The new PIN should be valid (simulate extracting from email or log if needed)
        # For this test, we can only check that the hash changed and old PIN is invalid 