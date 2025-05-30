#!/usr/bin/env python3
"""
NFR-04 Backup Standalone Tests

Simplified standalone tests for NFR-04 that focus on the backup mechanisms
without full Flask app dependencies.
"""

import pytest
import tempfile
import os
import shutil
import sqlite3
import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to sys.path to import from seed_lockers.py
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from seed_lockers import create_backup, add_new_lockers_safely


def test_nfr04_backup_creation():
    """Test 1: Basic backup creation functionality"""
    print("🧪 NFR-04 Test 1: Basic backup creation")
    
    # Create temporary database
    test_dir = tempfile.mkdtemp(prefix='nfr04_standalone_')
    db_path = Path(test_dir) / 'campus_locker.db'
    
    try:
        # Create test database with data
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE locker (
                id INTEGER PRIMARY KEY,
                location VARCHAR(100) NOT NULL,
                size VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL
            )
        ''')
        
        cursor.execute(
            "INSERT INTO locker (id, location, size, status) VALUES (?, ?, ?, ?)",
            (1, "Test Locker 1", "small", "free")
        )
        
        conn.commit()
        conn.close()
        
        # Test backup creation
        backup_path = create_backup(db_path)
        
        # Verify backup was created
        assert backup_path is not None, "Backup path should not be None"
        assert backup_path.exists(), "Backup file should exist"
        assert backup_path.name.startswith('campus_locker_backup_'), "Backup should have correct naming"
        assert backup_path.name.endswith('.db'), "Backup should be a .db file"
        
        # Verify backup contains data
        backup_conn = sqlite3.connect(str(backup_path))
        backup_cursor = backup_conn.cursor()
        backup_cursor.execute("SELECT COUNT(*) FROM locker")
        locker_count = backup_cursor.fetchone()[0]
        backup_conn.close()
        
        assert locker_count == 1, "Backup should contain original data"
        
        print("✅ NFR-04 Test 1: Basic backup creation - PASSED")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_nfr04_overwrite_protection():
    """Test 2: Overwrite protection with backup creation"""
    print("🧪 NFR-04 Test 2: Overwrite protection")
    
    # Create temporary database
    test_dir = tempfile.mkdtemp(prefix='nfr04_protection_')
    db_path = Path(test_dir) / 'campus_locker.db'
    
    try:
        # Create test database with existing data
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE locker (
                id INTEGER PRIMARY KEY,
                location VARCHAR(100) NOT NULL,
                size VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL
            )
        ''')
        
        # Insert existing test data
        existing_lockers = [
            (1, "Existing Locker 1", "small", "free"),
            (2, "Existing Locker 2", "medium", "occupied"),
        ]
        
        cursor.executemany(
            "INSERT INTO locker (id, location, size, status) VALUES (?, ?, ?, ?)",
            existing_lockers
        )
        
        conn.commit()
        conn.close()
        
        # Test conflicting configuration (should be blocked)
        conflict_config = {
            "lockers": [
                {"id": 1, "location": "Conflicting Locker 1", "size": "small", "status": "free"},
                {"id": 3, "location": "New Locker 3", "size": "large", "status": "free"}
            ]
        }
        
        # Count backups before
        backup_dir = db_path.parent / 'backups'
        initial_backups = len(list(backup_dir.glob('*.db'))) if backup_dir.exists() else 0
        
        # Attempt conflicting operation (should be blocked)
        import io
        import contextlib
        
        captured_output = io.StringIO()
        with contextlib.redirect_stdout(captured_output):
            success = add_new_lockers_safely(conflict_config, db_path)
        
        output = captured_output.getvalue()
        
        # Verify operation was blocked
        assert not success, "Conflicting operation should be blocked"
        assert "CRITICAL DATA PROTECTION ALERT" in output, "Should show protection alert"
        assert "Found ID conflicts" in output, "Should identify conflicts"
        
        # Verify original data is unchanged
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM locker")
        count_after = cursor.fetchone()[0]
        conn.close()
        
        assert count_after == 2, "Original data should be unchanged"
        
        # Test safe configuration (should work and create backup)
        safe_config = {
            "lockers": [
                {"id": 100, "location": "Safe New Locker 100", "size": "large", "status": "free"}
            ]
        }
        
        success = add_new_lockers_safely(safe_config, db_path)
        
        # Verify safe operation succeeded
        assert success, "Safe operation should succeed"
        
        # Verify backup was created
        if backup_dir.exists():
            final_backups = len(list(backup_dir.glob('*.db')))
            assert final_backups > initial_backups, "Backup should be created for safe operation"
        
        # Verify new locker was added
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM locker")
        count_final = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM locker WHERE id = 100")
        new_locker_count = cursor.fetchone()[0]
        conn.close()
        
        assert count_final == 3, "Should have one more locker after safe addition"
        assert new_locker_count == 1, "New locker should be added"
        
        print("✅ NFR-04 Test 2: Overwrite protection - PASSED")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_nfr04_backup_directory_structure():
    """Test 3: Backup directory structure and organization"""
    print("🧪 NFR-04 Test 3: Backup directory structure")
    
    # Create temporary database
    test_dir = tempfile.mkdtemp(prefix='nfr04_structure_')
    db_path = Path(test_dir) / 'campus_locker.db'
    
    try:
        # Create minimal test database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE locker (
                id INTEGER PRIMARY KEY,
                location VARCHAR(100) NOT NULL,
                size VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL
            )
        ''')
        
        cursor.execute(
            "INSERT INTO locker (id, location, size, status) VALUES (?, ?, ?, ?)",
            (1, "Test Locker", "small", "free")
        )
        
        conn.commit()
        conn.close()
        
        # Create multiple backups
        backup1 = create_backup(db_path)
        time.sleep(1)  # Ensure different timestamps
        backup2 = create_backup(db_path)
        
        # Verify backup directory structure
        backup_dir = db_path.parent / 'backups'
        assert backup_dir.exists(), "Backups directory should be created"
        assert backup_dir.is_dir(), "Backups should be a directory"
        
        # Verify backup files
        backup_files = list(backup_dir.glob('campus_locker_backup_*.db'))
        assert len(backup_files) >= 2, "Should have created multiple backup files"
        
        # Verify naming convention
        for backup_file in backup_files:
            assert backup_file.name.startswith('campus_locker_backup_'), "Correct prefix"
            assert backup_file.name.endswith('.db'), "Correct extension"
            assert len(backup_file.name.split('_')) >= 4, "Should contain timestamp components"
        
        # Verify backups are valid SQLite files
        for backup_file in backup_files:
            backup_conn = sqlite3.connect(str(backup_file))
            backup_cursor = backup_conn.cursor()
            backup_cursor.execute("SELECT COUNT(*) FROM locker")
            count = backup_cursor.fetchone()[0]
            backup_conn.close()
            assert count == 1, f"Backup {backup_file.name} should contain data"
        
        print("✅ NFR-04 Test 3: Backup directory structure - PASSED")
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def run_nfr04_standalone_tests():
    """Run all standalone NFR-04 tests"""
    print("=" * 80)
    print("🛡️  NFR-04 BACKUP STANDALONE TESTS")
    print("=" * 80)
    print("Simplified tests for NFR-04 backup functionality")
    print("- Backup creation and file management")
    print("- Overwrite protection mechanisms")
    print("- Backup directory organization")
    print("=" * 80)
    print()
    
    test_results = []
    
    try:
        test_nfr04_backup_creation()
        test_results.append(("Backup Creation", True))
        
        test_nfr04_overwrite_protection()
        test_results.append(("Overwrite Protection", True))
        
        test_nfr04_backup_directory_structure()
        test_results.append(("Directory Structure", True))
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        test_results.append(("Failed Test", False))
        raise
    
    # Summary
    print()
    print("=" * 80)
    print("📊 NFR-04 STANDALONE TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"📈 Results: {passed}/{total} tests passed")
    print()
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print()
    
    if passed == total:
        print("🏆 NFR-04 STANDALONE COMPLIANCE: FULLY FUNCTIONAL")
        print("   ✅ Backup creation and file management")
        print("   ✅ Overwrite protection with safety alerts")
        print("   ✅ Proper backup directory organization")
        print("   ✅ Data preservation and recovery capability")
    else:
        print("❌ NFR-04 STANDALONE COMPLIANCE: ISSUES DETECTED")
        print(f"   {passed}/{total} tests passed")
    
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    """Run standalone NFR-04 tests when executed directly"""
    run_nfr04_standalone_tests() 