#!/usr/bin/env python3
"""
Cleanup Test Parcels Script
===========================

This script removes all test parcels and test lockers created for testing.
"""

import sys
import os
# Add the parent directory to Python path so we can import the app module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.persistence.models import Parcel, Locker

def cleanup_test_data():
    """Delete all test parcels and test lockers"""
    app = create_app()
    
    with app.app_context():
        print("🧹 Cleaning Up Test Data")
        print("=" * 30)
        
        # Find and delete test parcels
        print("\n1. Removing test parcels...")
        test_parcels = Parcel.query.filter(
            Parcel.recipient_email.like("reminder.test%")
        ).all()
        
        if test_parcels:
            print(f"   Found {len(test_parcels)} test parcels to delete:")
            for parcel in test_parcels:
                print(f"     - ID {parcel.id}: {parcel.recipient_email}")
                db.session.delete(parcel)
            
            db.session.commit()
            print(f"   ✅ Deleted {len(test_parcels)} test parcels")
        else:
            print("   ✅ No test parcels found")
        
        # Find and delete test lockers
        print("\n2. Removing test lockers...")
        test_lockers = Locker.query.filter(
            Locker.location.like("Test Reminder Locker%")
        ).all()
        
        if test_lockers:
            print(f"   Found {len(test_lockers)} test lockers to delete:")
            for locker in test_lockers:
                print(f"     - ID {locker.id}: {locker.location}")
                db.session.delete(locker)
            
            db.session.commit()
            print(f"   ✅ Deleted {len(test_lockers)} test lockers")
        else:
            print("   ✅ No test lockers found")
        
        # Show final database state
        print("\n3. Final database state:")
        remaining_parcels = Parcel.query.count()
        remaining_lockers = Locker.query.count()
        
        print(f"   Remaining parcels: {remaining_parcels}")
        print(f"   Remaining lockers: {remaining_lockers}")
        
        print(f"\n🎯 Cleanup Complete!")
        print(f"   Database is now clean of test data")

if __name__ == "__main__":
    cleanup_test_data() 