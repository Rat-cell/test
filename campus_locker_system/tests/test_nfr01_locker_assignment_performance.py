#!/usr/bin/env python3
"""
NFR-01 Locker Assignment Performance Test
=========================================

Simple test to verify that locker assignment completes within 25ms.
This test focuses specifically on the performance requirement for NFR-01.

Requirements tested:
- NFR-01: Locker assignment completes in ≤ 25ms
- FR-01: Assign locker functionality works correctly

Features:
- Measures actual assignment time
- Tests with real database operations
- Provides detailed timing output
- Verifies both performance and functionality
- Ensures database state is properly restored after tests
"""

import sys
import os
# Add the parent directory to Python path so we can import the app module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import time
from app import create_app, db
from app.persistence.models import Locker, Parcel
from app.services.parcel_service import assign_locker_and_create_parcel

class TestNFR01LockerAssignmentPerformance:
    """Simple performance test for NFR-01 locker assignment with proper database cleanup"""

    @pytest.fixture
    def app(self):
        """Create test app with in-memory database and complete isolation"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SKIP_DATABASE_INITIALIZATION'] = True  # Prevent real database access
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()

    @pytest.fixture
    def setup_test_data(self, app):
        """Setup test data with proper cleanup"""
        with app.app_context():
            # Store original state for verification
            original_locker_count = Locker.query.count()
            original_parcel_count = Parcel.query.count()
            
            print(f"\n🔄 Database Setup:")
            print(f"  - Original lockers: {original_locker_count}")
            print(f"  - Original parcels: {original_parcel_count}")
            
            # Create test lockers (let database auto-assign IDs)
            test_lockers = [
                Locker(location="Test Locker 1", size="small", status="free"),
                Locker(location="Test Locker 2", size="small", status="free"),
                Locker(location="Test Locker 3", size="small", status="free"),
                Locker(location="Test Locker 4", size="medium", status="free"),
                Locker(location="Test Locker 5", size="medium", status="free"),
                Locker(location="Test Locker 6", size="large", status="free"),
            ]
            
            db.session.add_all(test_lockers)
            db.session.commit()
            
            # Store test locker IDs for cleanup
            test_locker_ids = [locker.id for locker in test_lockers]
            
            print(f"  - Added test lockers: {len(test_lockers)}")
            print(f"  - Test locker IDs: {test_locker_ids}")
            
            yield {
                'test_locker_ids': test_locker_ids,
                'original_locker_count': original_locker_count,
                'original_parcel_count': original_parcel_count
            }
            
            # Cleanup: Remove all test data
            print(f"\n🧹 Database Cleanup:")
            
            # Remove ALL parcels created after the original count (not just those in test lockers)
            # This handles cases where parcels might be assigned to existing lockers
            all_parcels = Parcel.query.all()
            parcels_to_remove = all_parcels[original_parcel_count:]  # Remove parcels beyond original count
            parcel_count = len(parcels_to_remove)
            
            for parcel in parcels_to_remove:
                # Also free up any lockers that were occupied by test parcels
                if parcel.locker_id:
                    locker = db.session.get(Locker, parcel.locker_id)
                    if locker:
                        locker.status = "free"
                db.session.delete(parcel)
            
            # Remove test lockers
            test_lockers_cleanup = Locker.query.filter(Locker.id.in_(test_locker_ids)).all()
            locker_count = len(test_lockers_cleanup)
            for locker in test_lockers_cleanup:
                db.session.delete(locker)
            
            db.session.commit()
            
            # Verify cleanup
            final_locker_count = Locker.query.count()
            final_parcel_count = Parcel.query.count()
            
            print(f"  - Removed parcels: {parcel_count}")
            print(f"  - Removed lockers: {locker_count}")
            print(f"  - Final lockers: {final_locker_count}")
            print(f"  - Final parcels: {final_parcel_count}")
            
            # Verify database is back to original state
            assert final_locker_count == original_locker_count, f"Locker cleanup failed: {final_locker_count} != {original_locker_count}"
            assert final_parcel_count == original_parcel_count, f"Parcel cleanup failed: {final_parcel_count} != {original_parcel_count}"
            
            print("  ✅ Database successfully restored to original state")

    def test_nfr01_locker_assignment_performance_25ms(self, app, setup_test_data):
        """Test that locker assignment completes within 25ms (NFR-01)"""
        print("\n" + "="*60)
        print("🧪 TEST: NFR-01 Locker Assignment Performance (≤ 25ms)")
        print("="*60)
        
        with app.app_context():
            print("📋 Test Setup:")
            print("  - 6 test lockers created (3 small, 2 medium, 1 large)")
            print("  - All lockers set to 'free' status")
            print("  - Testing locker assignment performance")
            print("  - Database will be restored after test")
            
            # Test data
            test_email = "performance.test@example.com"
            test_size = "medium"
            
            print(f"\n⚡ Testing assignment for:")
            print(f"  - Email: {test_email}")
            print(f"  - Size: {test_size}")
            
            # Measure assignment time
            print(f"\n⏱️  Measuring assignment time...")
            start_time = time.time()
            
            # Perform the locker assignment
            result_parcel, result_message = assign_locker_and_create_parcel(test_email, test_size)
            
            end_time = time.time()
            assignment_time_ms = (end_time - start_time) * 1000  # Convert to milliseconds
            
            print(f"\n📊 Performance Results:")
            print(f"  - Assignment time: {assignment_time_ms:.2f}ms")
            print(f"  - Target requirement: ≤ 25ms")
            print(f"  - Performance status: {'✅ PASSED' if assignment_time_ms <= 25 else '❌ FAILED'}")
            
            # Verify functionality worked
            functionality_passed = result_parcel is not None
            print(f"\n✅ Functionality Check:")
            print(f"  - Assignment successful: {'✓' if functionality_passed else '✗'}")
            if functionality_passed:
                print(f"  - Parcel ID: {result_parcel.id}")
                print(f"  - Locker ID: {result_parcel.locker_id}")
                print(f"  - Status: {result_parcel.status}")
            else:
                print(f"  - Error: {result_message}")
            
            # Performance verification
            print(f"\n🎯 NFR-01 Verification:")
            performance_passed = assignment_time_ms <= 25.0
            print(f"  - Performance requirement (≤ 25ms): {'✓' if performance_passed else '✗'}")
            print(f"  - Functional requirement (assignment works): {'✓' if functionality_passed else '✗'}")
            
            if performance_passed and functionality_passed:
                print("🎉 NFR-01 TEST PASSED: Locker assignment meets performance requirement!")
            elif functionality_passed:
                print("⚠️  NFR-01 TEST FAILED: Assignment works but too slow!")
            else:
                print("❌ NFR-01 TEST FAILED: Assignment failed!")
            
            # Performance assertions
            assert functionality_passed, f"Locker assignment failed: {result_message}"
            assert performance_passed, f"Assignment took {assignment_time_ms:.2f}ms, exceeds 25ms requirement"
            
            print(f"\n📈 Performance Summary:")
            print(f"  - Measured: {assignment_time_ms:.2f}ms")
            print(f"  - Required: ≤ 25ms")
            print(f"  - Margin: {25.0 - assignment_time_ms:.2f}ms under limit")

    def test_nfr01_multiple_assignments_consistency(self, app, setup_test_data):
        """Test that performance is consistent across multiple assignments"""
        print("\n" + "="*60)
        print("🧪 TEST: NFR-01 Multiple Assignment Performance Consistency")
        print("="*60)
        
        with app.app_context():
            print("📋 Test Setup:")
            print("  - Testing 3 consecutive assignments")
            print("  - Measuring consistency of performance")
            print("  - Database will be restored after test")
            
            assignment_times = []
            
            for i in range(3):
                test_email = f"test{i}@example.com"
                test_size = "small"
                
                # Measure assignment time
                start_time = time.time()
                result_parcel, result_message = assign_locker_and_create_parcel(test_email, test_size)
                end_time = time.time()
                
                assignment_time_ms = (end_time - start_time) * 1000
                assignment_times.append(assignment_time_ms)
                
                print(f"  - Assignment {i+1}: {assignment_time_ms:.2f}ms {'✓' if assignment_time_ms <= 25 else '✗'}")
                
                # Verify assignment worked
                assert result_parcel is not None, f"Assignment {i+1} failed: {result_message}"
            
            # Calculate statistics
            avg_time = sum(assignment_times) / len(assignment_times)
            max_time = max(assignment_times)
            min_time = min(assignment_times)
            
            print(f"\n📊 Performance Statistics:")
            print(f"  - Average: {avg_time:.2f}ms")
            print(f"  - Fastest: {min_time:.2f}ms")
            print(f"  - Slowest: {max_time:.2f}ms")
            print(f"  - Range: {max_time - min_time:.2f}ms")
            
            print(f"\n✅ Consistency Check:")
            all_under_25ms = all(t <= 25.0 for t in assignment_times)
            print(f"  - All assignments ≤ 25ms: {'✓' if all_under_25ms else '✗'}")
            print(f"  - Average ≤ 25ms: {'✓' if avg_time <= 25.0 else '✗'}")
            
            if all_under_25ms:
                print("🎉 CONSISTENCY TEST PASSED: All assignments meet performance requirement!")
            else:
                print("❌ CONSISTENCY TEST FAILED: Some assignments too slow!")
            
            # Assertions
            assert all_under_25ms, f"Some assignments exceeded 25ms: max={max_time:.2f}ms"
            assert avg_time <= 25.0, f"Average time {avg_time:.2f}ms exceeds 25ms requirement"

if __name__ == "__main__":
    # Allow running the test file directly for quick testing
    pytest.main([__file__, "-v", "-s"]) 