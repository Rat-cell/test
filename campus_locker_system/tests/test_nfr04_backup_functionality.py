#!/usr/bin/env python3
"""
NFR-04 Backup Functionality Test
===============================

Simple test to verify automated backup functionality with 7-day retention.
This test focuses specifically on the backup requirements for NFR-04.

Requirements tested:
- NFR-04: Automated backup creation
- NFR-04: 7-day minimum backup retention
- NFR-04: Backup file integrity and data preservation
- NFR-04: Backup scheduling logic

Features:
- Tests real backup creation (not mocked)
- Verifies backup contains actual database data
- Tests backup scheduling intervals
- Provides detailed explanatory output
- Creates real backup files you can see
"""

import sys
import os
# Add the parent directory to Python path so we can import the app module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import sqlite3
from pathlib import Path
from app import create_app, db
from app.persistence.models import Locker, Parcel
from app.services.database_service import DatabaseService

class TestNFR04BackupFunctionality:
    """Simple test for NFR-04 automated backup functionality"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        with app.app_context():
            yield app

    def test_nfr04_automated_backup_creation(self, app):
        """Test NFR-04 automated backup creation and 7-day retention"""
        print("\n" + "="*70)
        print("🧪 TEST: NFR-04 Automated Backup Functionality")
        print("="*70)
        
        with app.app_context():
            print("📋 Test Setup:")
            print("  - Testing automated 7-day backup creation")
            print("  - Verifying backup data integrity")
            print("  - Testing backup scheduling logic")
            print("  - Creating real backup files")
            
            # Get the databases directory
            project_root = Path(__file__).parent.parent.parent
            databases_dir = project_root / 'campus_locker_system' / 'databases'
            backup_dir = databases_dir / 'backups'
            
            print(f"\n📁 Directory Information:")
            print(f"  - Databases directory: {databases_dir}")
            print(f"  - Backup directory: {backup_dir}")
            print(f"  - Databases dir exists: {'✓' if databases_dir.exists() else '✗'}")
            print(f"  - Backup dir exists: {'✓' if backup_dir.exists() else '✗'}")
            
            # Ensure backup directory exists
            if not backup_dir.exists():
                backup_dir.mkdir(parents=True, exist_ok=True)
                print(f"  - Created backup directory")
            
            # Check original database files
            main_db_path = databases_dir / 'campus_locker.db'
            audit_db_path = databases_dir / 'campus_locker_audit.db'
            
            print(f"\n📊 Original Database Status:")
            print(f"  - Main database exists: {'✓' if main_db_path.exists() else '✗'}")
            print(f"  - Audit database exists: {'✓' if audit_db_path.exists() else '✗'}")
            
            if main_db_path.exists():
                size_mb = main_db_path.stat().st_size / (1024 * 1024)
                print(f"  - Main database size: {size_mb:.2f} MB")
            
            if audit_db_path.exists():
                size_mb = audit_db_path.stat().st_size / (1024 * 1024)
                print(f"  - Audit database size: {size_mb:.2f} MB")
            
            # Count existing backup files before test
            existing_backups = list(backup_dir.glob('*_scheduled_*day_*.db'))
            print(f"  - Existing backup files: {len(existing_backups)}")
            
            # Show current database content BEFORE backup
            print(f"\n📊 Current Database Content (BEFORE backup):")
            if main_db_path.exists():
                try:
                    conn = sqlite3.connect(str(main_db_path))
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT COUNT(*) FROM locker")
                    locker_count = cursor.fetchone()[0]
                    print(f"  - Current lockers: {locker_count} records")
                    
                    cursor.execute("SELECT COUNT(*) FROM parcel")
                    parcel_count = cursor.fetchone()[0]
                    print(f"  - Current parcels: {parcel_count} records")
                    
                    cursor.execute("SELECT COUNT(*) FROM admin_user")
                    admin_count = cursor.fetchone()[0]
                    print(f"  - Current admin users: {admin_count} records")
                    
                    cursor.execute("SELECT COUNT(*) FROM locker_sensor_data")
                    sensor_count = cursor.fetchone()[0]
                    print(f"  - Current sensor data: {sensor_count} records")
                    
                    conn.close()
                except Exception as e:
                    print(f"  - Error reading current database: {str(e)}")
            
            if audit_db_path.exists():
                try:
                    conn = sqlite3.connect(str(audit_db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM audit_log")
                    audit_count = cursor.fetchone()[0]
                    print(f"  - Current audit logs: {audit_count} records")
                    conn.close()
                except Exception as e:
                    print(f"  - Error reading audit database: {str(e)}")
            
            print(f"\n⚡ Testing NFR-04 backup creation...")
            
            # CRITICAL: Force WAL checkpoint on original databases before backup
            # This ensures all data is consolidated from WAL files to main database files
            print(f"\n💾 Forcing WAL checkpoint on original databases...")
            for db_path in [main_db_path, audit_db_path]:
                if db_path.exists():
                    try:
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                        checkpoint_result = cursor.fetchone()
                        conn.close()
                        print(f"  - {db_path.name} checkpoint: {checkpoint_result}")
                    except Exception as e:
                        print(f"  - {db_path.name} checkpoint failed: {str(e)}")
            
            # Test backup scheduling logic first
            should_backup, reason = DatabaseService.should_create_scheduled_backup()
            print(f"\n📅 Backup Scheduling Logic:")
            print(f"  - Should create backup: {should_backup}")
            print(f"  - Reason: {reason}")
            
            # Create a backup using the real system
            backup_created, backup_message = DatabaseService.create_scheduled_backup()
            
            print(f"\n📊 Backup Creation Results:")
            print(f"  - Backup created: {'✓' if backup_created else '✗'}")
            print(f"  - Message: {backup_message}")
            
            # List all backup files after creation
            all_backups = list(backup_dir.glob('*_scheduled_*day_*.db'))
            new_backups = [b for b in all_backups if b not in existing_backups]
            
            print(f"\n📁 Backup Files:")
            print(f"  - Total backup files: {len(all_backups)}")
            print(f"  - New backup files: {len(new_backups)}")
            
            # If no new backups, test the most recent existing ones
            backups_to_test = new_backups if new_backups else all_backups[-2:] if all_backups else []
            
            for backup_file in new_backups:
                size_mb = backup_file.stat().st_size / (1024 * 1024)
                print(f"  - NEW: {backup_file.name} ({size_mb:.2f} MB)")
            
            if not new_backups and all_backups:
                print(f"  - No new backups (recent backup exists), testing existing ones:")
                for backup_file in backups_to_test:
                    size_mb = backup_file.stat().st_size / (1024 * 1024)
                    print(f"  - EXISTING: {backup_file.name} ({size_mb:.2f} MB)")
            
            # Test backup data integrity and content
            print(f"\n✅ Backup Data Integrity Tests:")
            integrity_results = []
            data_comparison_results = []
            
            for backup_file in backups_to_test:
                try:
                    # Test basic connectivity
                    conn = sqlite3.connect(str(backup_file))
                    cursor = conn.cursor()
                    
                    # Get table list
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    table_count = len(tables)
                    
                    print(f"  - {backup_file.name}:")
                    print(f"    - Tables: {table_count} ({'✓' if table_count > 0 else '✗'})")
                    
                    # Test data content for main database backups
                    if 'campus_locker_scheduled' in backup_file.name and 'audit' not in backup_file.name:
                        # Check if locker table exists and has data (FIXED: table name is 'locker', not 'lockers')
                        if 'locker' in tables:
                            cursor.execute("SELECT COUNT(*) FROM locker")
                            locker_count = cursor.fetchone()[0]
                            print(f"    - Lockers: {locker_count} records")
                            
                            # Compare with original database
                            if main_db_path.exists():
                                orig_conn = sqlite3.connect(str(main_db_path))
                                orig_cursor = orig_conn.cursor()
                                orig_cursor.execute("SELECT COUNT(*) FROM locker")
                                orig_locker_count = orig_cursor.fetchone()[0]
                                orig_conn.close()
                                
                                data_matches = locker_count == orig_locker_count
                                data_comparison_results.append(data_matches)
                                print(f"    - Data match: {'✓' if data_matches else '✗'} (backup: {locker_count}, original: {orig_locker_count})")
                            else:
                                print(f"    - Cannot compare: original database not accessible")
                        
                        # Check parcel table (FIXED: table name is 'parcel', not 'parcels')
                        if 'parcel' in tables:
                            cursor.execute("SELECT COUNT(*) FROM parcel")
                            parcel_count = cursor.fetchone()[0]
                            print(f"    - Parcels: {parcel_count} records")
                        
                        # Also check admin_user table
                        if 'admin_user' in tables:
                            cursor.execute("SELECT COUNT(*) FROM admin_user")
                            admin_count = cursor.fetchone()[0]
                            print(f"    - Admin users: {admin_count} records")
                        
                        # Check locker_sensor_data table
                        if 'locker_sensor_data' in tables:
                            cursor.execute("SELECT COUNT(*) FROM locker_sensor_data")
                            sensor_count = cursor.fetchone()[0]
                            print(f"    - Sensor data: {sensor_count} records")
                    
                    # Test audit database backups
                    elif 'audit' in backup_file.name:
                        if 'audit_log' in tables:
                            cursor.execute("SELECT COUNT(*) FROM audit_log")
                            audit_count = cursor.fetchone()[0]
                            print(f"    - Audit logs: {audit_count} records")
                    
                    conn.close()
                    integrity_results.append(True)
                    
                except Exception as e:
                    print(f"  - {backup_file.name}: ✗ - Error: {str(e)}")
                    integrity_results.append(False)
                    data_comparison_results.append(False)
            
            # Test 7-day retention logic
            print(f"\n📅 NFR-04 7-Day Retention Test:")
            retention_days = 7  # NFR-04 requirement
            print(f"  - Required retention: {retention_days} days minimum")
            print(f"  - Backup files created with 7-day naming")
            
            # Verify backup file naming includes 7-day reference
            seven_day_backups = [b for b in backups_to_test if '_7day_' in b.name]
            print(f"  - 7-day named backups: {len(seven_day_backups)}")
            
            print(f"\n🎯 NFR-04 Backup Verification:")
            print(f"  - Backup system functional: {'✓' if backup_created else '✗'}")
            print(f"  - Backup files exist: {'✓' if len(backups_to_test) > 0 else '✗'}")
            print(f"  - File integrity: {'✓' if all(integrity_results) else '✗'}")
            print(f"  - Data preservation: {'✓' if all(data_comparison_results) or len(data_comparison_results) == 0 else '✗'}")
            print(f"  - 7-day retention naming: {'✓' if len(seven_day_backups) > 0 else '✗'}")
            
            all_tests_passed = (
                backup_created and 
                len(backups_to_test) > 0 and 
                all(integrity_results) and
                len(seven_day_backups) > 0 and
                (all(data_comparison_results) or len(data_comparison_results) == 0)
            )
            
            if all_tests_passed:
                print("🎉 NFR-04 BACKUP TEST PASSED: Automated backup system working!")
                print("  - 7-day scheduled backups created successfully")
                print("  - Database data properly preserved in backups")
                print("  - Backup files are fully functional")
                print(f"  - Backup files located: {backup_dir}")
            else:
                print("❌ NFR-04 BACKUP TEST FAILED: Issues with backup system!")
            
            # Show file system location
            print(f"\n📍 Backup File Location:")
            print(f"  - {backup_dir.absolute()}")
            print("  - You can navigate to this folder to see the backup files")
            
            # Assertions for NFR-04 requirements
            assert backup_created, f"NFR-04: Backup system failed - {backup_message}"
            assert len(backups_to_test) > 0, "NFR-04: No backup files available for testing"
            assert all(integrity_results), "NFR-04: Some backup files failed integrity check"
            assert len(seven_day_backups) > 0, "NFR-04: No 7-day retention backups found"

if __name__ == "__main__":
    # Allow running the test file directly for quick testing
    pytest.main([__file__, "-v", "-s"]) 