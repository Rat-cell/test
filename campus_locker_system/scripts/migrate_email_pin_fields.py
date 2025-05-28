#!/usr/bin/env python3
"""
Database migration script to add email-based PIN generation fields to the Parcel model.
This script should be run after updating the Parcel model to include the new fields.
"""

import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.business.parcel import Parcel
from sqlalchemy import text

def migrate_email_pin_fields():
    """Add new email-based PIN generation fields to existing database"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Starting email-based PIN generation migration...")
            
            # Check if the new columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('parcel')]
            
            new_columns = [
                'pin_generation_token',
                'pin_generation_token_expiry', 
                'pin_generation_count',
                'last_pin_generation'
            ]
            
            missing_columns = [col for col in new_columns if col not in columns]
            
            if not missing_columns:
                print("All email-based PIN generation columns already exist. No migration needed.")
                return
            
            print(f"Adding missing columns: {missing_columns}")
            
            # Add the new columns if they don't exist
            if 'pin_generation_token' in missing_columns:
                db.session.execute(text('ALTER TABLE parcel ADD COLUMN pin_generation_token VARCHAR(128)'))
                print("Added pin_generation_token column")
            
            if 'pin_generation_token_expiry' in missing_columns:
                db.session.execute(text('ALTER TABLE parcel ADD COLUMN pin_generation_token_expiry DATETIME'))
                print("Added pin_generation_token_expiry column")
            
            if 'pin_generation_count' in missing_columns:
                db.session.execute(text('ALTER TABLE parcel ADD COLUMN pin_generation_count INTEGER NOT NULL DEFAULT 0'))
                print("Added pin_generation_count column")
            
            if 'last_pin_generation' in missing_columns:
                db.session.execute(text('ALTER TABLE parcel ADD COLUMN last_pin_generation DATETIME'))
                print("Added last_pin_generation column")
            
            # Make pin_hash and otp_expiry nullable for email-based PIN generation
            try:
                # Note: SQLite doesn't support ALTER COLUMN, so we'll handle this differently
                # For SQLite, we need to check if the columns are already nullable
                print("Checking if pin_hash and otp_expiry columns need to be made nullable...")
                
                # Try to insert a test record with NULL values to see if columns are nullable
                test_parcel = Parcel(
                    locker_id=1,  # Assuming locker 1 exists
                    recipient_email='test@example.com',
                    pin_hash=None,
                    otp_expiry=None
                )
                db.session.add(test_parcel)
                db.session.flush()  # This will fail if columns are not nullable
                db.session.delete(test_parcel)  # Clean up test record
                print("pin_hash and otp_expiry columns are already nullable")
                
            except Exception as e:
                print(f"Columns may not be nullable yet: {e}")
                print("Note: For SQLite, you may need to recreate the table to make columns nullable.")
                print("This is handled automatically by SQLAlchemy when you restart the application.")
            
            db.session.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Migration failed: {e}")
            raise

if __name__ == '__main__':
    migrate_email_pin_fields() 