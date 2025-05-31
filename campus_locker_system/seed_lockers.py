#!/usr/bin/env python3
"""
SAFE Locker Database Management Script

🛡️ SAFETY FIRST: This script protects existing locker data from accidental overwrites.

This script provides SAFE locker management:
1. ADD-ONLY mode: Only allows adding new lockers, never modifying existing ones
2. BACKUP protection: Creates automatic backups before any changes
3. VALIDATION: Prevents ID conflicts and data corruption
4. RESTRICTED overwrites: Requires special admin confirmation for destructive operations

Usage:
  python seed_lockers.py --add-new               # Safely add new lockers from JSON
  python seed_lockers.py --verify-only           # Check current state (safe)
  python seed_lockers.py --initial-seed          # Only seed if database is completely empty
  python seed_lockers.py --admin-reset-confirm   # DANGEROUS: Admin-only full reset
"""

import os
import sys
import json
import argparse
import sqlite3
import shutil
from datetime import datetime
import datetime as dt
from pathlib import Path

def load_json_config(config_file='databases/lockers-hwr.json'):
    """Load locker configuration from JSON file"""
    json_path = Path(__file__).parent / config_file
    if not json_path.exists():
        print(f"❌ JSON config file not found: {json_path}")
        return None
    
    with open(json_path, 'r') as f:
        return json.load(f)

def get_database_path():
    """Get the database file path"""
    return Path(__file__).parent / 'databases' / 'campus_locker.db'

def create_backup(db_path):
    """NFR-04: Backup - Create timestamped backup for data preservation"""
    if not db_path.exists():
        return None
    
    timestamp = datetime.now(dt.UTC).strftime('%Y%m%d_%H%M%S')
    
    # NFR-04: Backup - Store backups in dedicated backups directory
    backup_dir = db_path.parent / 'backups'
    backup_dir.mkdir(exist_ok=True)  # Create backups directory if it doesn't exist
    
    backup_path = backup_dir / f'campus_locker_backup_{timestamp}.db'
    
    # NFR-04: Backup - Copy database file for overwrite protection
    shutil.copy2(db_path, backup_path)
    print(f"💾 Created backup: {backup_path}")
    return backup_path

def get_existing_lockers(db_path):
    """Get all existing lockers from database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, location, size, status FROM locker ORDER BY id")
    existing = cursor.fetchall()
    conn.close()
    return existing

def check_for_conflicts(existing_lockers, new_config):
    """Check for ID conflicts between existing lockers and new config"""
    existing_ids = set(locker[0] for locker in existing_lockers)
    new_lockers = new_config.get('lockers', [])
    new_ids = set(locker['id'] for locker in new_lockers)
    
    conflicts = existing_ids.intersection(new_ids)
    
    return conflicts, existing_ids, new_ids

def add_new_lockers_safely(config, db_path):
    """Safely add ONLY new lockers without touching existing ones"""
    existing_lockers = get_existing_lockers(db_path)
    conflicts, existing_ids, new_ids = check_for_conflicts(existing_lockers, config)
    
    if conflicts:
        print("🚨" * 20)
        print("🚨 CRITICAL DATA PROTECTION ALERT 🚨")
        print("🚨" * 20)
        print(f"🚫 SAFETY BLOCK: Found ID conflicts: {sorted(conflicts)}")
        print(f"   These locker IDs already exist in the database.")
        print(f"   To protect existing data, operation cancelled.")
        print()
        print("🛡️  PROTECTION MODE: Your existing data is SAFE!")
        print("   No changes have been made to the database.")
        print("   All existing lockers remain unchanged.")
        print()
        print("💡 SAFE SOLUTIONS:")
        print(f"   1. Use different IDs for new lockers (recommended)")
        print(f"   2. Remove conflicting IDs from JSON file")
        print(f"   3. Use --verify-only to check current status")
        print()
        print("⚠️  RISKY ALTERNATIVE (NOT RECOMMENDED):")
        print(f"   💥 Use --admin-reset-confirm for complete replacement (DESTROYS ALL DATA)")
        print("🚨" * 20)
        return False
    
    # Find truly new lockers
    new_lockers = config.get('lockers', [])
    truly_new = [locker for locker in new_lockers if locker['id'] not in existing_ids]
    
    if not truly_new:
        print(f"ℹ️ No new lockers to add. All IDs in JSON already exist in database.")
        return True
    
    print(f"🔒 SAFE MODE: Adding {len(truly_new)} new lockers (protecting {len(existing_lockers)} existing)")
    
    # NFR-04: Create backup before making changes - overwrite protection
    backup_path = create_backup(db_path)
    
    # Add only new lockers
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    added_count = 0
    for locker in truly_new:
        try:
            cursor.execute("""
                INSERT INTO locker (id, location, size, status) 
                VALUES (?, ?, ?, ?)
            """, (
                locker['id'],
                locker['location'], 
                locker['size'],
                locker['status']
            ))
            added_count += 1
            print(f"  ✅ Added: ID {locker['id']} - {locker['location']} ({locker['size']})")
        except sqlite3.IntegrityError as e:
            print(f"  ❌ Failed to add locker ID {locker['id']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Successfully added {added_count} new lockers!")
    print(f"💾 Backup saved: {backup_path}")
    return True

def initial_seed_only(config, db_path):
    """Seed database ONLY if it's completely empty"""
    existing_count = len(get_existing_lockers(db_path))
    
    if existing_count > 0:
        print(f"🚫 SAFETY BLOCK: Database already contains {existing_count} lockers.")
        print(f"   Initial seeding is only allowed on empty databases.")
        print(f"   Use --add-new to safely add more lockers.")
        return False
    
    print(f"🌱 Database is empty. Performing initial seed...")
    
    lockers = config.get('lockers', [])
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for locker in lockers:
        cursor.execute("""
            INSERT INTO locker (id, location, size, status) 
            VALUES (?, ?, ?, ?)
        """, (
            locker['id'],
            locker['location'], 
            locker['size'],
            locker['status']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Successfully seeded {len(lockers)} lockers to empty database")
    return True

def admin_reset_with_confirmation(config, db_path):
    """DANGEROUS: Complete database reset with multiple confirmations"""
    existing_lockers = get_existing_lockers(db_path)
    
    if not existing_lockers:
        print("ℹ️ Database is already empty. No reset needed.")
        return True
    
    print(f"⚠️  DANGER ZONE ⚠️")
    print(f"This will PERMANENTLY DELETE all {len(existing_lockers)} existing lockers!")
    print(f"This includes:")
    print(f"  - All locker data")
    print(f"  - All associated parcels") 
    print(f"  - All sensor data")
    print(f"  - Locker usage history")
    
    # Multiple confirmations required
    confirm1 = input(f"\n🔴 Type 'DELETE ALL LOCKERS' to continue: ").strip()
    if confirm1 != 'DELETE ALL LOCKERS':
        print("❌ Operation cancelled. Safety first!")
        return False
    
    confirm2 = input(f"🔴 Are you absolutely sure? Type 'YES DELETE': ").strip()
    if confirm2 != 'YES DELETE':
        print("❌ Operation cancelled. Safety first!")
        return False
    
    print(f"⏳ Creating backup before destructive operation...")
    # NFR-04: Create backup before admin reset - data preservation
    backup_path = create_backup(db_path)
    
    # Clear and reseed
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM locker_sensor_data")
    cursor.execute("DELETE FROM parcel") 
    cursor.execute("DELETE FROM locker")
    
    lockers = config.get('lockers', [])
    for locker in lockers:
        cursor.execute("""
            INSERT INTO locker (id, location, size, status) 
            VALUES (?, ?, ?, ?)
        """, (
            locker['id'],
            locker['location'], 
            locker['size'],
            locker['status']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"💥 DESTRUCTIVE OPERATION COMPLETED")
    print(f"   Deleted: {len(existing_lockers)} existing lockers")
    print(f"   Added: {len(lockers)} new lockers")
    print(f"   Backup: {backup_path}")
    
    return True

def verify_seeding(config, db_path):
    """Verify database state without making changes"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, location, size, status FROM locker ORDER BY id")
    db_lockers = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM parcel")
    parcel_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM locker_sensor_data")
    sensor_count = cursor.fetchone()[0]
    
    conn.close()
    
    json_lockers = config.get('lockers', [])
    
    print(f"🔍 DATABASE VERIFICATION:")
    print(f"  📄 JSON config: {len(json_lockers)} lockers")
    print(f"  🗄️ Database: {len(db_lockers)} lockers")
    print(f"  📦 Active parcels: {parcel_count}")
    print(f"  📡 Sensor readings: {sensor_count}")
    
    if db_lockers:
        print(f"\n📊 Size Distribution:")
        sizes = {}
        for locker in db_lockers:
            size = locker[2]  # size is at index 2
            sizes[size] = sizes.get(size, 0) + 1
        for size, count in sorted(sizes.items()):
            print(f"     {size}: {count}")
        
        print(f"\n📍 Sample Lockers:")
        for locker in db_lockers[:3]:
            print(f"     ID {locker[0]}: {locker[1]} ({locker[2]}) - {locker[3]}")
        if len(db_lockers) > 3:
            print(f"     ... and {len(db_lockers) - 3} more")
    
    return True

def display_safety_banner():
    """Display concise safety warnings at startup"""
    print("🛡️  CAMPUS LOCKER SYSTEM - SAFE DATABASE MANAGEMENT")
    print("=" * 60)
    print("⚠️  PROTECTION MODE: Automatic backups • Conflict detection • Safe operations")
    print()
    print("SAFE OPTIONS:")
    print("  --verify-only     Check status (no changes)")
    print("  --add-new         Add new lockers safely")
    print("  --initial-seed    Seed empty database only")
    print()
    print("ADMIN ONLY:")
    print("  --admin-reset-confirm    ⚠️  DESTROYS ALL DATA")
    print("=" * 60)
    print()

def main():
    """Main script function with safety-first approach"""
    parser = argparse.ArgumentParser(description='SAFE Locker Database Management')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--verify-only', action='store_true',
                       help='🔍 SAFE: Only verify current state (no changes)')
    group.add_argument('--add-new', action='store_true',
                       help='🔒 SAFE: Add only new lockers (protects existing data)')
    group.add_argument('--initial-seed', action='store_true',
                       help='🌱 SAFE: Seed only if database is completely empty')
    group.add_argument('--admin-reset-confirm', action='store_true',
                       help='💥 DANGER: Complete reset with confirmation (DESTROYS DATA)')
    
    parser.add_argument('--file', default='databases/lockers-hwr.json',
                       help='JSON config file to use')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_json_config(args.file)
    if not config:
        sys.exit(1)
    
    db_path = get_database_path()
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("Please run the application first to create the database")
        sys.exit(1)
    
    # Execute requested operation
    success = False
    
    if args.verify_only:
        success = verify_seeding(config, db_path)
    
    elif args.add_new:
        print(f"🔒 SAFE MODE: Adding new lockers only (existing data protected)")
        success = add_new_lockers_safely(config, db_path)
    
    elif args.initial_seed:
        print(f"🌱 INITIAL SEED MODE: Only works on empty databases")
        success = initial_seed_only(config, db_path)
    
    elif args.admin_reset_confirm:
        print(f"💥 ADMIN RESET MODE: This will destroy existing data!")
        success = admin_reset_with_confirmation(config, db_path)
    
    if success:
        print(f"\n✅ Operation completed successfully!")
    else:
        print(f"\n❌ Operation failed or was cancelled.")
        sys.exit(1)

if __name__ == "__main__":
    display_safety_banner()
    main() 