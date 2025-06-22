#!/usr/bin/env python3
"""
Create Old Test Parcels for Reminder Testing
============================================

This script creates test parcels with timestamps set to 25+ hours ago,
making them immediately eligible for 24-hour reminders.
"""

import sys
import os
# Add the parent directory to Python path so we can import the app module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import datetime as dt
from app import create_app, db
from app.persistence.models import Parcel, Locker

def create_old_test_parcels():
    """Create test parcels with old timestamps for immediate reminder testing"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Creating Old Test Parcels for Immediate Reminder Testing")
        print("=" * 60)
        
        # Clean up existing test parcels
        print("\n1. Cleaning up existing test parcels...")
        existing_parcels = Parcel.query.filter(Parcel.recipient_email.like("reminder.test%")).all()
        if existing_parcels:
            print(f"   Removing {len(existing_parcels)} existing test parcels...")
            for parcel in existing_parcels:
                db.session.delete(parcel)
            db.session.commit()
        
        # Check if we have lockers, create some if needed
        print("\n2. Checking for available lockers...")
        existing_lockers = Locker.query.filter(Locker.location.like("Test Reminder Locker%")).all()
        
        if not existing_lockers:
            print("   Creating test lockers...")
            test_lockers = [
                Locker(location="Test Reminder Locker 1", size="small", status="occupied"),
                Locker(location="Test Reminder Locker 2", size="medium", status="occupied"),
                Locker(location="Test Reminder Locker 3", size="large", status="occupied"),
            ]
            db.session.add_all(test_lockers)
            db.session.commit()
            locker_ids = [locker.id for locker in test_lockers]
            print(f"   ✅ Created {len(test_lockers)} test lockers")
        else:
            locker_ids = [locker.id for locker in existing_lockers]
            print(f"   ✅ Using {len(existing_lockers)} existing test lockers")
        
        # Create test parcels with old timestamps
        print("\n3. Creating test parcels with old timestamps...")
        now = datetime.now(dt.UTC)
        
        test_parcels_data = [
            {
                "email": "reminder.test1@example.com",
                "hours_ago": 25,
                "has_pin": False,
                "description": "No PIN, needs reminder"
            },
            {
                "email": "reminder.test2@example.com", 
                "hours_ago": 30,
                "has_pin": True,
                "description": "Has PIN, needs reminder"
            },
            {
                "email": "reminder.test3@example.com",
                "hours_ago": 48,
                "has_pin": True, 
                "description": "Has PIN, very old, needs reminder"
            }
        ]
        
        created_parcels = []
        
        for i, parcel_data in enumerate(test_parcels_data):
            deposited_time = now - timedelta(hours=parcel_data["hours_ago"])
            
            parcel = Parcel(
                locker_id=locker_ids[i % len(locker_ids)],
                recipient_email=parcel_data["email"],
                status="deposited",
                deposited_at=deposited_time,
                reminder_sent_at=None  # No reminder sent yet
            )
            
            # Add PIN if specified
            if parcel_data["has_pin"]:
                parcel.pin_hash = "test_pin_hash:test_salt"
                parcel.pin_generation_count = 1
                parcel.last_pin_generation = now - timedelta(hours=1)
                parcel.pin_generation_token = f"test-token-{i+1}"
                parcel.pin_generation_token_expiry = now + timedelta(hours=1)
            
            db.session.add(parcel)
            created_parcels.append(parcel)
        
        db.session.commit()
        
        # Show created parcels
        print(f"\n✅ Created {len(created_parcels)} test parcels:")
        for parcel in created_parcels:
            age_hours = (now - parcel.deposited_at).total_seconds() / 3600
            has_pin = "YES" if parcel.pin_hash else "NO"
            print(f"   - ID {parcel.id}: {parcel.recipient_email}")
            print(f"     Age: {age_hours:.1f}h, Has PIN: {has_pin}, Locker: {parcel.locker_id}")
        
        # Verify eligibility
        print("\n4. Verifying reminder eligibility...")
        from app.persistence.repositories.parcel_repository import ParcelRepository
        cutoff_time = now - timedelta(hours=24)
        eligible_parcels = ParcelRepository.get_all_deposited_needing_reminder(cutoff_time)
        
        test_eligible = [p for p in eligible_parcels if p.recipient_email.startswith("reminder.test")]
        print(f"   ✅ {len(test_eligible)} test parcels are eligible for reminders")
        
        if test_eligible:
            print("\n   Eligible test parcels:")
            for parcel in test_eligible:
                age_hours = (now - parcel.deposited_at).total_seconds() / 3600
                has_pin = "YES" if parcel.pin_hash else "NO"
                print(f"     - ID {parcel.id}: {parcel.recipient_email} (Age: {age_hours:.1f}h, PIN: {has_pin})")
        
        print(f"\n🎯 Ready to Test!")
        print(f"   ✅ {len(test_eligible)} parcels ready for reminder testing")
        print(f"   📧 Run 'python trigger_reminder_check.py' to send reminders")
        print(f"   🌐 Check MailHog at http://localhost:8025 for emails")

if __name__ == "__main__":
    create_old_test_parcels() 