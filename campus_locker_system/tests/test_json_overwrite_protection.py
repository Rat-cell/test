#!/usr/bin/env python3
"""
Simple Test: JSON Configuration with Overwrite Protection

This test demonstrates:
1. First run: Successfully adds lockers from JSON file
2. Second run: Shows overwrite protection when trying to use same JSON again
"""

import pytest
import tempfile
import json
import os
import sqlite3
from pathlib import Path

class TestJSONOverwriteProtection:
    """Simple test for JSON configuration and overwrite protection"""

    def test_json_configuration_overwrite_protection(self):
        """
        Test JSON configuration loading with overwrite protection
        
        Scenario:
        1. First run: Add lockers from JSON (should succeed)
        2. Second run: Try same JSON again (should be blocked by overwrite protection)
        """
        print("\n" + "="*60)
        print("🧪 TEST: JSON Configuration Overwrite Protection")
        print("="*60)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test database
            test_db_path = Path(temp_dir) / 'test_campus_locker.db'
            
            # Create database schema
            self._create_test_database(test_db_path)
            
            # Create test JSON config
            test_json_path = Path(temp_dir) / 'test_lockers.json'
            test_config = self._create_test_json_config(test_json_path)
            
            print(f"📋 Test Setup:")
            print(f"  - Test database: {test_db_path}")
            print(f"  - Test JSON config: {test_json_path}")
            print(f"  - Lockers in JSON: {len(test_config['lockers'])}")
            
            # === FIRST RUN: Should succeed ===
            print(f"\n🆕 FIRST RUN: Adding lockers from JSON")
            success_first = self._run_add_new_lockers(test_db_path, test_json_path)
            
            # Verify first run succeeded
            locker_count_after_first = self._count_lockers(test_db_path)
            print(f"  ✅ First run result: {success_first}")
            print(f"  📊 Lockers in database after first run: {locker_count_after_first}")
            
            assert success_first, "First run should succeed"
            assert locker_count_after_first == len(test_config['lockers']), "All lockers should be added"
            
            # === SECOND RUN: Should show overwrite protection ===
            print(f"\n🛡️  SECOND RUN: Trying same JSON again (should trigger protection)")
            success_second = self._run_add_new_lockers(test_db_path, test_json_path)
            
            # Verify second run was blocked by protection
            locker_count_after_second = self._count_lockers(test_db_path)
            print(f"  🛡️  Second run result: {success_second}")
            print(f"  📊 Lockers in database after second run: {locker_count_after_second}")
            
            # Note: success_second might be True if no new lockers were added (which is correct)
            # The key test is that no additional lockers were created
            assert locker_count_after_second == locker_count_after_first, "No additional lockers should be added on second run"
            
            print(f"\n🎉 TEST PASSED: Overwrite protection working correctly!")
            print(f"  - First run: ✅ Added {locker_count_after_first} lockers")
            print(f"  - Second run: 🛡️  Protected existing data (no duplicates)")

    def _create_test_database(self, db_path: Path):
        """Create a test database with proper schema"""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create locker table
        cursor.execute("""
            CREATE TABLE locker (
                id INTEGER PRIMARY KEY,
                location VARCHAR(100) NOT NULL,
                size VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'free'
            )
        """)
        
        conn.commit()
        conn.close()

    def _create_test_json_config(self, json_path: Path) -> dict:
        """Create a test JSON configuration file"""
        config = {
            "metadata": {
                "description": "Test Locker Configuration",
                "version": "1.0",
                "total_count": 3,
                "size_distribution": {
                    "small": 1,
                    "medium": 1,
                    "large": 1
                }
            },
            "lockers": [
                {"id": 101, "location": "Test Locker 101", "size": "small", "status": "free"},
                {"id": 102, "location": "Test Locker 102", "size": "medium", "status": "free"},
                {"id": 103, "location": "Test Locker 103", "size": "large", "status": "free"}
            ]
        }
        
        with open(json_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config

    def _run_add_new_lockers(self, db_path: Path, json_path: Path) -> bool:
        """
        Simulate the seed_lockers.py --add-new functionality
        Returns True if operation completed successfully (not necessarily if lockers were added)
        """
        try:
            # Load JSON config
            with open(json_path, 'r') as f:
                config = json.load(f)
            
            # Get existing lockers
            existing_lockers = self._get_existing_lockers(db_path)
            existing_ids = set(locker[0] for locker in existing_lockers)
            
            # Check for conflicts
            new_lockers = config.get('lockers', [])
            new_ids = set(locker['id'] for locker in new_lockers)
            conflicts = existing_ids.intersection(new_ids)
            
            if conflicts:
                print(f"    🚫 OVERWRITE PROTECTION: Found ID conflicts: {sorted(conflicts)}")
                print(f"    🛡️  Protection activated - no changes made to database")
                return True  # Protection worked correctly
            
            # Add only new lockers
            truly_new = [locker for locker in new_lockers if locker['id'] not in existing_ids]
            
            if not truly_new:
                print(f"    ℹ️  No new lockers to add - all IDs already exist")
                return True
            
            # Add new lockers to database
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            added_count = 0
            for locker in truly_new:
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
                print(f"    ✅ Added: ID {locker['id']} - {locker['location']} ({locker['size']})")
            
            conn.commit()
            conn.close()
            
            print(f"    🎉 Successfully added {added_count} new lockers")
            return True
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            return False

    def _get_existing_lockers(self, db_path: Path) -> list:
        """Get existing lockers from database"""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT id, location, size, status FROM locker ORDER BY id")
        result = cursor.fetchall()
        conn.close()
        return result

    def _count_lockers(self, db_path: Path) -> int:
        """Count total lockers in database"""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM locker")
        count = cursor.fetchone()[0]
        conn.close()
        return count


if __name__ == "__main__":
    # Allow running the test file directly
    test_instance = TestJSONOverwriteProtection()
    test_instance.test_json_configuration_overwrite_protection() 