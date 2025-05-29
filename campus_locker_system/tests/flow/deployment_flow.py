#!/usr/bin/env python3
"""
Deployment Flow Test
===================

Tests the complete fresh deployment workflow from database removal to seeding verification.
This test mimics the exact process performed manually to ensure the deployment process works correctly.

Test Flow:
1. Remove existing database files
2. Rebuild Docker containers 
3. Start containers and verify fresh initialization
4. Verify database files are created locally
5. Verify correct seeding with expected locker count
6. Verify safety protection against re-seeding

Usage:
    python tests/flow/deployment_flow.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class DeploymentFlowTest:
    """Tests the complete deployment flow from fresh install to running system."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.databases_dir = self.project_root / "databases"
        self.main_db = self.databases_dir / "campus_locker.db"
        self.audit_db = self.databases_dir / "campus_locker_audit.db"
        self.config_json = self.databases_dir / "lockers-hwr.json"
        
    def run_command(self, command, check=True, capture_output=True):
        """Run a shell command and return the result."""
        print(f"🔧 Running: {command}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=self.project_root,
                check=check,
                capture_output=capture_output,
                text=True
            )
            if capture_output:
                print(f"   ✅ Exit code: {result.returncode}")
                if result.stdout.strip():
                    print(f"   📝 Output: {result.stdout.strip()[:200]}...")
                if result.stderr.strip():
                    print(f"   ⚠️  Error: {result.stderr.strip()[:200]}...")
            return result
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Command failed with exit code {e.returncode}")
            if e.stdout:
                print(f"   📝 Output: {e.stdout}")
            if e.stderr:
                print(f"   ⚠️  Error: {e.stderr}")
            raise

    def test_step_1_remove_existing_databases(self):
        """Step 1: Remove existing database files to simulate fresh deployment."""
        print("\n" + "="*80)
        print("📋 STEP 1: Remove Existing Database Files")
        print("="*80)
        
        files_removed = []
        
        if self.main_db.exists():
            os.remove(self.main_db)
            files_removed.append(str(self.main_db))
            print(f"🗑️  Removed: {self.main_db}")
            
        if self.audit_db.exists():
            os.remove(self.audit_db)
            files_removed.append(str(self.audit_db))
            print(f"🗑️  Removed: {self.audit_db}")
            
        if not files_removed:
            print("ℹ️  No database files to remove (already clean)")
        
        # Verify only JSON config remains
        remaining_files = list(self.databases_dir.glob("*"))
        expected_files = [self.config_json] if self.config_json.exists() else []
        
        assert len(remaining_files) == len(expected_files), f"Expected only JSON config, found: {remaining_files}"
        print(f"✅ Verified: Only configuration file remains: {remaining_files}")
        
        return {"files_removed": files_removed}

    def test_step_2_rebuild_containers(self):
        """Step 2: Rebuild Docker containers with no cache."""
        print("\n" + "="*80)
        print("📋 STEP 2: Rebuild Docker Containers")
        print("="*80)
        
        # Stop containers
        print("🛑 Stopping containers...")
        self.run_command("docker compose down", capture_output=False)
        
        # Rebuild with no cache
        print("🔨 Rebuilding containers with no cache...")
        self.run_command("docker compose build --no-cache", capture_output=False)
        
        print("✅ Containers rebuilt successfully")
        return {"status": "rebuilt"}

    def test_step_3_start_containers_verify_initialization(self):
        """Step 3: Start containers and verify fresh database initialization."""
        print("\n" + "="*80)
        print("📋 STEP 3: Start Containers & Verify Fresh Initialization")
        print("="*80)
        
        # Start containers
        print("🚀 Starting containers...")
        self.run_command("docker compose up -d", capture_output=False)
        
        # Wait for containers to be ready
        print("⏳ Waiting for containers to be ready...")
        time.sleep(10)
        
        # Check container status
        result = self.run_command("docker compose ps")
        assert "healthy" in result.stdout or "running" in result.stdout, "Containers not running properly"
        
        # Check logs for fresh initialization
        print("📋 Checking initialization logs...")
        logs_result = self.run_command('docker compose logs app | grep -E "(MISSING|seed|🆕|🏗️|🌱)"')
        
        # Verify fresh database detection
        assert "MISSING" in logs_result.stdout, "Should detect missing databases"
        assert "🆕 New databases detected" in logs_result.stdout or "seed" in logs_result.stdout, "Should trigger seeding"
        
        print("✅ Fresh initialization detected in logs")
        return {"logs_checked": True}

    def test_step_4_verify_database_files_created(self):
        """Step 4: Verify database files are created in local filesystem."""
        print("\n" + "="*80)
        print("📋 STEP 4: Verify Database Files Created Locally")
        print("="*80)
        
        # Wait a bit more for file creation
        time.sleep(5)
        
        # Check if database files exist
        main_db_exists = self.main_db.exists()
        audit_db_exists = self.audit_db.exists()
        
        print(f"📁 Main database file: {self.main_db} - {'✅ EXISTS' if main_db_exists else '❌ MISSING'}")
        print(f"📁 Audit database file: {self.audit_db} - {'✅ EXISTS' if audit_db_exists else '❌ MISSING'}")
        
        assert main_db_exists, f"Main database file should exist: {self.main_db}"
        assert audit_db_exists, f"Audit database file should exist: {self.audit_db}"
        
        # Check file sizes (should be non-empty)
        main_size = self.main_db.stat().st_size
        audit_size = self.audit_db.stat().st_size
        
        print(f"📊 Main database size: {main_size} bytes")
        print(f"📊 Audit database size: {audit_size} bytes")
        
        assert main_size > 1000, f"Main database too small: {main_size} bytes"
        assert audit_size > 1000, f"Audit database too small: {audit_size} bytes"
        
        print("✅ Database files created successfully with expected sizes")
        return {"main_size": main_size, "audit_size": audit_size}

    def test_step_5_verify_seeding_results(self):
        """Step 5: Verify correct seeding with expected locker count."""
        print("\n" + "="*80)
        print("📋 STEP 5: Verify Seeding Results")
        print("="*80)
        
        # Query locker count from database
        print("📊 Checking locker count in database...")
        count_result = self.run_command(
            'docker compose exec app python -c "from app.business.locker import Locker; from app import create_app; app = create_app(); app.app_context().push(); print(f\'LOCKER_COUNT:{Locker.query.count()}\')"'
        )
        
        # Extract locker count from output
        for line in count_result.stdout.split('\n'):
            if 'LOCKER_COUNT:' in line:
                locker_count = int(line.split('LOCKER_COUNT:')[1].strip())
                break
        else:
            raise AssertionError("Could not find locker count in output")
        
        print(f"🔢 Total lockers found: {locker_count}")
        
        # Verify expected count (15 HWR lockers)
        expected_count = 15
        assert locker_count == expected_count, f"Expected {expected_count} lockers, found {locker_count}"
        
        print(f"✅ Correct locker count verified: {locker_count}")
        return {"locker_count": locker_count}

    def test_step_6_verify_safety_protection(self):
        """Step 6: Verify safety protection against re-seeding."""
        print("\n" + "="*80)
        print("📋 STEP 6: Verify Safety Protection Against Re-seeding")
        print("="*80)
        
        # Restart containers to trigger initialization again
        print("🔄 Restarting containers to test re-seeding protection...")
        self.run_command("docker compose restart app", capture_output=False)
        
        # Wait for restart
        time.sleep(8)
        
        # Check logs for safety protection
        print("📋 Checking logs for safety protection...")
        safety_logs = self.run_command('docker compose logs app --tail=20 | grep -E "(existing lockers|skipping seeding|📊)"')
        
        # Verify safety message appears
        assert "existing lockers" in safety_logs.stdout or "skipping seeding" in safety_logs.stdout, \
            "Should show safety protection against re-seeding"
        
        print("✅ Safety protection verified - no re-seeding occurred")
        return {"safety_verified": True}

    def run_complete_test(self):
        """Run the complete deployment flow test."""
        print("🚀 CAMPUS LOCKER SYSTEM - DEPLOYMENT FLOW TEST")
        print("=" * 80)
        print("Testing complete fresh deployment workflow...")
        print("This test simulates the exact manual process performed during development.")
        print("=" * 80)
        
        results = {}
        
        try:
            # Execute all test steps
            results["step_1"] = self.test_step_1_remove_existing_databases()
            results["step_2"] = self.test_step_2_rebuild_containers()
            results["step_3"] = self.test_step_3_start_containers_verify_initialization()
            results["step_4"] = self.test_step_4_verify_database_files_created()
            results["step_5"] = self.test_step_5_verify_seeding_results()
            results["step_6"] = self.test_step_6_verify_safety_protection()
            
            # Test completed successfully
            print("\n" + "="*80)
            print("🎉 DEPLOYMENT FLOW TEST - SUCCESS!")
            print("="*80)
            print("✅ All deployment flow steps completed successfully")
            print("✅ Fresh deployment process verified working")
            print("✅ Database files created in local filesystem")
            print("✅ Automatic seeding verified")
            print("✅ Safety protection verified")
            print("\n🏆 The Campus Locker System deployment flow is production-ready!")
            
            return True, results
            
        except Exception as e:
            print("\n" + "="*80)
            print("❌ DEPLOYMENT FLOW TEST - FAILED!")
            print("="*80)
            print(f"💥 Error during deployment flow test: {str(e)}")
            print("\n🔧 Check the logs above for detailed error information.")
            
            return False, results

def main():
    """Main entry point for the deployment flow test."""
    test = DeploymentFlowTest()
    success, results = test.run_complete_test()
    
    if success:
        print(f"\n📋 Test Results Summary:")
        for step, result in results.items():
            print(f"   {step}: {result}")
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main() 