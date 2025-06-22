#!/usr/bin/env python3
"""
24-Hour Reminder Trigger Script
===============================

This script checks the database for deposited parcels and automatically
sends reminder emails for parcels that:
- Are in "deposited" status
- Have been deposited for more than 24 hours
- Haven't received a reminder yet

This can be run manually or scheduled as a cron job for automated processing.

Usage:
    cd tests/
    python trigger_reminder_check.py

Features:
- Checks existing database parcels (no test data creation)
- Sends real emails to MailHog
- Comprehensive logging and status reporting
- Safe to run multiple times (won't send duplicate reminders)
"""

import sys
import os
# Add the parent directory to Python path so we can import the app module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import datetime as dt
from app import create_app, db
from app.persistence.models import Parcel
from app.services.parcel_service import process_reminder_notifications

def check_database_status():
    """Check and display current database status"""
    print("=== Database Status Check ===")
    
    # Get all parcels by status
    all_parcels = Parcel.query.all()
    deposited_parcels = Parcel.query.filter_by(status='deposited').all()
    
    print(f"Total parcels in database: {len(all_parcels)}")
    print(f"Deposited parcels: {len(deposited_parcels)}")
    
    if not deposited_parcels:
        print("❌ No deposited parcels found in database")
        return False
    
    print("\nDeposited parcels breakdown:")
    now = datetime.now(dt.UTC)
    cutoff_time = now - timedelta(hours=24)
    
    needs_reminder = []
    already_reminded = []
    too_new = []
    
    for parcel in deposited_parcels:
        age_hours = (now - parcel.deposited_at).total_seconds() / 3600
        
        if parcel.deposited_at <= cutoff_time:
            if parcel.reminder_sent_at is None:
                needs_reminder.append(parcel)
            else:
                already_reminded.append(parcel)
        else:
            too_new.append(parcel)
    
    print(f"  - Needs reminder (>24h, no reminder sent): {len(needs_reminder)}")
    print(f"  - Already reminded (>24h, reminder sent): {len(already_reminded)}")
    print(f"  - Too new (<24h): {len(too_new)}")
    
    if needs_reminder:
        print("\nParcels that need reminders:")
        for parcel in needs_reminder:
            age_hours = (now - parcel.deposited_at).total_seconds() / 3600
            print(f"  - ID {parcel.id}: {parcel.recipient_email} (deposited {age_hours:.1f}h ago)")
    
    if already_reminded:
        print("\nParcels already reminded:")
        for parcel in already_reminded:
            age_hours = (now - parcel.deposited_at).total_seconds() / 3600
            reminder_age_hours = (now - parcel.reminder_sent_at).total_seconds() / 3600
            print(f"  - ID {parcel.id}: {parcel.recipient_email} (reminded {reminder_age_hours:.1f}h ago)")
    
    return len(needs_reminder) > 0

def process_reminders():
    """Process reminder notifications for eligible parcels"""
    print("\n=== Processing Reminder Notifications ===")
    print("Checking for parcels that need 24-hour reminders...")
    
    # This will send REAL emails (not mocked)
    processed_count, error_count = process_reminder_notifications()
    
    print(f"\nResults:")
    print(f"  ✅ Successfully processed: {processed_count} parcels")
    print(f"  ❌ Errors encountered: {error_count} parcels")
    
    return processed_count, error_count

def show_updated_status():
    """Show updated database status after processing"""
    print("\n=== Updated Database Status ===")
    
    deposited_parcels = Parcel.query.filter_by(status='deposited').all()
    now = datetime.now(dt.UTC)
    cutoff_time = now - timedelta(hours=24)
    
    needs_reminder = []
    already_reminded = []
    
    for parcel in deposited_parcels:
        if parcel.deposited_at <= cutoff_time:
            if parcel.reminder_sent_at is None:
                needs_reminder.append(parcel)
            else:
                already_reminded.append(parcel)
    
    print(f"Parcels still needing reminders: {len(needs_reminder)}")
    print(f"Parcels with reminders sent: {len(already_reminded)}")
    
    if needs_reminder:
        print("⚠️  Some parcels still need reminders (check logs for errors)")
    else:
        print("✅ All eligible parcels have been reminded")

def main():
    """Main function to check database and process reminders"""
    app = create_app()
    
    with app.app_context():
        print("🔍 24-Hour Reminder Trigger Script")
        print("=" * 50)
        print()
        
        # Check current database status
        has_parcels_to_process = check_database_status()
        
        if not has_parcels_to_process:
            print("\n✅ No parcels need reminders at this time")
            print("💡 Tip: Parcels need to be deposited for >24 hours and not have received a reminder yet")
            return
        
        print(f"\n📧 Processing reminders (emails will be sent to MailHog)")
        print("   MailHog URL: http://localhost:8025")
        
        # Process the reminders
        processed_count, error_count = process_reminders()
        
        # Show updated status
        show_updated_status()
        
        print(f"\n🎯 Summary:")
        if processed_count > 0:
            print(f"   ✅ {processed_count} reminder email(s) sent successfully")
            print(f"   📧 Check MailHog at http://localhost:8025 to see the emails")
        
        if error_count > 0:
            print(f"   ❌ {error_count} error(s) occurred during processing")
            print(f"   📋 Check the application logs for details")
        
        if processed_count == 0 and error_count == 0:
            print(f"   ℹ️  No parcels were processed (all up to date)")

if __name__ == "__main__":
    main() 