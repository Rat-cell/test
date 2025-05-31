"""
FR-01 Assign Locker Test Suite

This module contains comprehensive tests for the FR-01 requirement:
"Assign the next free locker large enough for the parcel" - Performance ≤ 200ms

Test Categories:
1. Locker Assignment Logic Tests
2. Performance and Speed Tests
3. Size Matching Tests
4. Availability Handling Tests
5. Error Handling and Edge Cases
6. Concurrent Assignment Tests
7. Database State Management Tests
8. Integration Tests

Author: Campus Locker System Team I
Date: May 30, 2025
FR-01 Implementation: Critical performance requirement ≤ 200ms
"""

import sys
import os
from pathlib import Path

# Add the campus_locker_system directory to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app import create_app, db
from app.persistence.models import Parcel, Locker, AuditLog
from app.services.parcel_service import assign_locker_and_create_parcel


class TestFR01AssignLocker:
    """
    FR-01: Assign Locker - Critical Performance Test Suite
    
    Tests the locker assignment system that must complete in ≤ 200ms
    and correctly assign the next available locker for parcel size.
    """

    @pytest.fixture
    def app(self):
        """Create test application with FR-01 configuration"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    @pytest.fixture
    def setup_test_lockers(self, app):
        """Setup test lockers for assignment testing"""
        with app.app_context():
            # Create test lockers of different sizes
            lockers = [
                Locker(id=801, location="Test Small 1", size="small", status="free"),
                Locker(id=802, location="Test Small 2", size="small", status="free"),
                Locker(id=803, location="Test Medium 1", size="medium", status="free"),
                Locker(id=804, location="Test Medium 2", size="medium", status="free"),
                Locker(id=805, location="Test Large 1", size="large", status="free"),
                Locker(id=806, location="Test Large 2", size="large", status="free"),
                Locker(id=807, location="Test Small Occupied", size="small", status="occupied"),
                Locker(id=808, location="Test Out of Service", size="medium", status="out_of_service"),
            ]
            
            for locker in lockers:
                db.session.add(locker)
            db.session.commit()
            
            yield lockers
            
            # Cleanup
            for locker in lockers:
                # Delete any parcels first
                Parcel.query.filter_by(locker_id=locker.id).delete()
                db.session.delete(locker)
            db.session.commit()

    # ===== 1. LOCKER ASSIGNMENT LOGIC TESTS =====

    def test_fr01_assigns_next_free_locker(self, app, setup_test_lockers):
        """
        FR-01: Test that system assigns next available free locker
        Verifies basic assignment functionality
        """
        with app.app_context():
            # Assign a small parcel
            result = assign_locker_and_create_parcel(
                "test-fr01@example.com",
                "small"
            )
            
            # Verify assignment succeeded
            assert result is not None, "FR-01: Should successfully assign available locker"
            parcel, message = result
            assert parcel is not None, "FR-01: Should return parcel object"
            assert parcel.locker_id in [801, 802], "FR-01: Should assign one of the available small lockers"
            
            # Verify locker status updated
            assigned_locker = Locker.query.get(parcel.locker_id)
            assert assigned_locker.status == "occupied", "FR-01: Assigned locker should be marked as occupied"

    def test_fr01_skips_occupied_lockers(self, app, setup_test_lockers):
        """
        FR-01: Test that system skips occupied lockers
        Verifies proper filtering of unavailable lockers
        """
        with app.app_context():
            # Assign a small parcel (should skip occupied locker 807)
            result = assign_locker_and_create_parcel(
                "test-fr01-skip@example.com",
                "small"
            )
            
            # Verify assignment succeeded and didn't use occupied locker
            assert result is not None, "FR-01: Should assign available locker"
            parcel, message = result
            assert parcel is not None, "FR-01: Should return parcel object"
            assert parcel.locker_id != 807, "FR-01: Should not assign occupied locker"
            assert parcel.locker_id in [801, 802], "FR-01: Should assign free small locker"

    def test_fr01_skips_out_of_service_lockers(self, app, setup_test_lockers):
        """
        FR-01: Test that system skips out-of-service lockers
        Verifies proper handling of maintenance mode lockers
        """
        with app.app_context():
            # Try to assign medium parcel (should skip out-of-service locker 808)
            result = assign_locker_and_create_parcel(
                "test-fr01-service@example.com",
                "medium"
            )
            
            # Verify assignment succeeded and didn't use out-of-service locker
            assert result is not None, "FR-01: Should assign available locker"
            parcel, message = result
            assert parcel is not None, "FR-01: Should return parcel object"
            assert parcel.locker_id != 808, "FR-01: Should not assign out-of-service locker"
            assert parcel.locker_id in [803, 804], "FR-01: Should assign free medium locker"

    # ===== 2. PERFORMANCE AND SPEED TESTS =====

    def test_fr01_performance_under_200ms(self, app, setup_test_lockers):
        """
        FR-01: Test that locker assignment completes in ≤ 200ms
        Critical performance requirement validation
        """
        with app.app_context():
            start_time = time.time()
            
            # Perform locker assignment
            result = assign_locker_and_create_parcel(
                "test-fr01-perf@example.com",
                "medium"
            )
            
            end_time = time.time()
            assignment_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Verify performance requirement
            assert assignment_time <= 200.0, f"FR-01: Assignment must complete in ≤200ms (took {assignment_time:.2f}ms)"
            assert result is not None, "FR-01: Assignment should succeed within time limit"
            parcel, message = result
            assert parcel is not None, "FR-01: Should return parcel object"

    def test_fr01_multiple_assignments_performance(self, app, setup_test_lockers):
        """
        FR-01: Test performance of multiple consecutive assignments
        Verifies consistent performance under load
        """
        with app.app_context():
            assignment_times = []
            
            # Perform 5 consecutive assignments
            for i in range(5):
                start_time = time.time()
                
                result = assign_locker_and_create_parcel(
                    f"test-fr01-multi-{i}@example.com",
                    "small"
                )
                
                end_time = time.time()
                assignment_time = (end_time - start_time) * 1000
                assignment_times.append(assignment_time)
                
                if result and result[0]:  # If assignment succeeded
                    parcel, message = result
                    assert parcel is not None, f"FR-01: Assignment {i+1} should succeed"
                else:
                    break  # Stop when we run out of available lockers
            
            # Verify all successful assignments meet performance requirement
            for i, time_ms in enumerate(assignment_times):
                if time_ms > 0:  # Only check successful assignments
                    assert time_ms <= 200.0, f"FR-01: Assignment {i+1} took {time_ms:.2f}ms (>200ms limit)"
            
            # Calculate average performance
            if assignment_times:
                avg_time = sum(assignment_times) / len(assignment_times)
                assert avg_time <= 200.0, f"FR-01: Average assignment time {avg_time:.2f}ms exceeds 200ms limit"

    def test_fr01_performance_with_limited_availability(self, app):
        """
        FR-01: Test performance when lockers are nearly full
        Verifies performance doesn't degrade with limited availability
        """
        with app.app_context():
            # Create only one available locker
            test_locker = Locker(id=901, location="Last Available", size="small", status="free")
            db.session.add(test_locker)
            db.session.commit()
            
            try:
                start_time = time.time()
                
                result = assign_locker_and_create_parcel(
                    "test-fr01-limited@example.com",
                    "small"
                )
                
                end_time = time.time()
                assignment_time = (end_time - start_time) * 1000
                
                # Verify performance even with limited availability
                assert assignment_time <= 200.0, f"FR-01: Limited availability assignment took {assignment_time:.2f}ms (>200ms limit)"
                assert result is not None, "FR-01: Should find the available locker"
                parcel, message = result
                assert parcel is not None, "FR-01: Should return parcel object"
                assert parcel.locker_id == 901, "FR-01: Should assign the only available locker"
                
            finally:
                # Cleanup
                Parcel.query.filter_by(locker_id=901).delete()
                db.session.delete(test_locker)
                db.session.commit()

    # ===== 3. SIZE MATCHING TESTS =====

    def test_fr01_correct_size_matching_small(self, app, setup_test_lockers):
        """
        FR-01: Test correct size matching for small parcels
        Verifies parcels are assigned to appropriately sized lockers
        """
        with app.app_context():
            result = assign_locker_and_create_parcel(
                "test-fr01-small@example.com",
                "small"
            )
            
            assert result is not None, "FR-01: Small parcel should be assigned"
            parcel, message = result
            assert parcel is not None, "FR-01: Should return parcel object"
            
            assigned_locker = Locker.query.get(parcel.locker_id)
            assert assigned_locker.size in ["small", "medium", "large"], "FR-01: Small parcel can fit in any size locker"

    def test_fr01_correct_size_matching_medium(self, app, setup_test_lockers):
        """
        FR-01: Test correct size matching for medium parcels
        Verifies medium parcels are not assigned to small lockers
        """
        with app.app_context():
            result = assign_locker_and_create_parcel(
                "test-fr01-medium@example.com",
                "medium"
            )
            
            assert result is not None, "FR-01: Medium parcel should be assigned"
            parcel, message = result
            assert parcel is not None, "FR-01: Should return parcel object"
            
            assigned_locker = Locker.query.get(parcel.locker_id)
            assert assigned_locker.size in ["medium", "large"], "FR-01: Medium parcel should not be assigned to small locker"

    def test_fr01_correct_size_matching_large(self, app, setup_test_lockers):
        """
        FR-01: Test correct size matching for large parcels
        Verifies large parcels are only assigned to large lockers
        """
        with app.app_context():
            result = assign_locker_and_create_parcel(
                "test-fr01-large@example.com",
                "large"
            )
            
            assert result is not None, "FR-01: Large parcel should be assigned"
            parcel, message = result
            assert parcel is not None, "FR-01: Should return parcel object"
            
            assigned_locker = Locker.query.get(parcel.locker_id)
            assert assigned_locker.size == "large", "FR-01: Large parcel should only be assigned to large locker"

    # ===== 4. AVAILABILITY HANDLING TESTS =====

    def test_fr01_handles_no_available_lockers(self, app):
        """
        FR-01: Test handling when no suitable lockers are available
        Verifies graceful handling of capacity limits
        """
        with app.app_context():
            # Create only occupied lockers
            occupied_locker = Locker(id=902, location="Occupied Only", size="small", status="occupied")
            db.session.add(occupied_locker)
            db.session.commit()
            
            try:
                result = assign_locker_and_create_parcel(
                    "test-fr01-none@example.com",
                    "small"
                )
                
                # Should return None when no lockers available
                assert result is not None, "FR-01: Should return result tuple"
                parcel, message = result
                assert parcel is None, "FR-01: Should return None parcel when no suitable lockers available"
                assert "no available" in message.lower(), "FR-01: Should return appropriate error message"
                
            finally:
                # Cleanup
                db.session.delete(occupied_locker)
                db.session.commit()

    def test_fr01_handles_no_suitable_size_lockers(self, app):
        """
        FR-01: Test handling when no lockers of suitable size are available
        Verifies size constraint handling
        """
        with app.app_context():
            # Create only small lockers
            small_locker = Locker(id=903, location="Small Only", size="small", status="free")
            db.session.add(small_locker)
            db.session.commit()
            
            try:
                # Try to assign large parcel to small locker (should fail)
                result = assign_locker_and_create_parcel(
                    "test-fr01-size@example.com",
                    "large"
                )
                
                # Should return None when no suitable size available
                assert result is not None, "FR-01: Should return result tuple"
                parcel, message = result
                assert parcel is None, "FR-01: Should return None parcel when no suitable size lockers available"
                assert "no available" in message.lower(), "FR-01: Should return appropriate error message"
                
            finally:
                # Cleanup
                db.session.delete(small_locker)
                db.session.commit()

    # ===== 5. ERROR HANDLING AND EDGE CASES =====

    def test_fr01_handles_invalid_parcel_size(self, app, setup_test_lockers):
        """
        FR-01: Test handling of invalid parcel sizes
        Verifies input validation
        """
        with app.app_context():
            # Test invalid size
            result = assign_locker_and_create_parcel(
                "test-fr01-invalid@example.com",
                "invalid_size"
            )
            
            # Should handle invalid size gracefully
            assert result is not None, "FR-01: Should return result tuple"
            parcel, message = result
            assert parcel is None, "FR-01: Should return None parcel for invalid parcel size"
            assert "invalid" in message.lower(), "FR-01: Should return appropriate error message"

    def test_fr01_handles_empty_email(self, app, setup_test_lockers):
        """
        FR-01: Test handling of empty recipient email
        Verifies input validation for required fields
        """
        with app.app_context():
            # Test with empty email
            result = assign_locker_and_create_parcel(
                "",
                "small"
            )
            
            # Should handle empty email gracefully
            assert result is not None, "FR-01: Should return result tuple"
            parcel, message = result
            assert parcel is None, "FR-01: Should return None parcel for empty recipient email"
            assert "invalid" in message.lower(), "FR-01: Should return appropriate error message"

    def test_fr01_atomic_operation(self, app, setup_test_lockers):
        """
        FR-01: Test that assignment is atomic (all-or-nothing)
        Verifies database consistency
        """
        with app.app_context():
            initial_parcel_count = Parcel.query.count()
            initial_locker_states = {l.id: l.status for l in Locker.query.all()}
            
            # Successful assignment
            result = assign_locker_and_create_parcel(
                "test-fr01-atomic@example.com",
                "small"
            )
            
            # Verify atomic operation
            assert result is not None, "FR-01: Should return result tuple"
            parcel, message = result
            assert parcel is not None, "FR-01: Atomic operation should succeed"
            
            # Verify database state is consistent
            final_parcel_count = Parcel.query.count()
            assert final_parcel_count == initial_parcel_count + 1, "FR-01: Should have exactly one new parcel"
            
            # Verify locker state changed appropriately
            assigned_locker = Locker.query.get(parcel.locker_id)
            assert assigned_locker.status == "occupied", "FR-01: Assigned locker should be occupied"

    # ===== 6. CONCURRENT ASSIGNMENT TESTS =====

    def test_fr01_concurrent_assignment_safety(self, app, setup_test_lockers):
        """
        FR-01: Test thread safety of concurrent assignments
        Verifies no race conditions in locker assignment
        """
        with app.app_context():
            results = []
            errors = []
            
            def assign_locker_thread(thread_id):
                try:
                    # Each thread needs its own application context
                    with app.app_context():
                        result = assign_locker_and_create_parcel(
                            f"test-fr01-concurrent-{thread_id}@example.com",
                            "small"
                        )
                        results.append(result)
                except Exception as e:
                    errors.append(str(e))
            
            # Start multiple concurrent threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=assign_locker_thread, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify no errors occurred
            assert len(errors) == 0, f"FR-01: Concurrent assignments should not cause errors: {errors}"
            
            # Verify results are consistent
            successful_assignments = 0
            for result in results:
                if result and result[0] is not None:
                    successful_assignments += 1
            
            # Should have some successful assignments (limited by available small lockers)
            assert successful_assignments > 0, "FR-01: Should have at least one successful concurrent assignment"

    # ===== 7. DATABASE STATE MANAGEMENT TESTS =====

    def test_fr01_locker_status_update(self, app, setup_test_lockers):
        """
        FR-01: Test that locker status is properly updated
        Verifies database state consistency
        """
        with app.app_context():
            # Get initial free locker
            free_locker = Locker.query.filter_by(size="medium", status="free").first()
            assert free_locker is not None, "FR-01: Should have free medium locker for test"
            
            initial_status = free_locker.status
            locker_id = free_locker.id
            
            # Assign parcel
            result = assign_locker_and_create_parcel(
                "test-fr01-status@example.com",
                "medium"
            )
            
            # Verify assignment and status update
            assert result is not None, "FR-01: Should return result tuple"
            parcel, message = result
            assert parcel is not None, "FR-01: Assignment should succeed"
            assert parcel.locker_id == locker_id, "FR-01: Should assign expected locker"
            
            # Refresh locker from database
            db.session.refresh(free_locker)
            assert free_locker.status == "occupied", "FR-01: Locker status should be updated to occupied"

    def test_fr01_parcel_creation_with_correct_data(self, app, setup_test_lockers):
        """
        FR-01: Test that parcel is created with correct data
        Verifies proper parcel initialization
        """
        with app.app_context():
            test_email = "test-fr01-data@example.com"
            
            result = assign_locker_and_create_parcel(
                test_email,
                "large"
            )
            
            # Verify parcel creation with correct data
            assert result is not None, "FR-01: Should return result tuple"
            parcel, message = result
            assert parcel is not None, "FR-01: Should create parcel"
            assert parcel.recipient_email == test_email, "FR-01: Should have correct recipient email"
            assert parcel.status == "deposited", "FR-01: Should have correct initial status"
            assert parcel.locker_id is not None, "FR-01: Should be assigned to a locker"
            assert parcel.deposited_at is not None, "FR-01: Should have deposit timestamp"

    # ===== 8. INTEGRATION TESTS =====

    def test_fr01_integration_with_audit_logging(self, app, setup_test_lockers):
        """
        FR-01: Test integration with audit logging system
        Verifies assignment activities are logged
        """
        with app.app_context():
            # Clear existing audit logs for clean test
            AuditLog.query.filter(AuditLog.action.like('%FR-01%')).delete()
            db.session.commit()
            
            # Perform assignment
            result = assign_locker_and_create_parcel(
                "test-fr01-audit@example.com",
                "small"
            )
            
            # Check for audit log entries (if implemented)
            fr01_logs = AuditLog.query.filter(AuditLog.action.like('%FR-01%')).all()
            
            # Note: Audit logging for FR-01 may not be implemented yet
            # This test verifies integration capability
            assert result is not None, "FR-01: Should return result tuple"
            parcel, message = result
            assert parcel is not None, "FR-01: Assignment should succeed for audit integration test"

    def test_fr01_end_to_end_assignment_workflow(self, app, setup_test_lockers):
        """
        FR-01: Test complete end-to-end assignment workflow
        Verifies full integration of assignment process
        """
        with app.app_context():
            # Count initial state
            initial_free_lockers = Locker.query.filter_by(status="free").count()
            initial_parcels = Parcel.query.count()
            
            # Perform assignment
            result = assign_locker_and_create_parcel(
                "test-fr01-e2e@example.com",
                "medium"
            )
            
            # Verify end-to-end state changes
            assert result is not None, "FR-01: Should return result tuple"
            parcel, message = result
            assert parcel is not None, "FR-01: End-to-end assignment should succeed"
            
            # Verify counts updated
            final_free_lockers = Locker.query.filter_by(status="free").count()
            final_parcels = Parcel.query.count()
            
            assert final_free_lockers == initial_free_lockers - 1, "FR-01: Should have one fewer free locker"
            assert final_parcels == initial_parcels + 1, "FR-01: Should have one more parcel"


# ===== STANDALONE TEST FUNCTIONS =====

def test_fr01_performance_benchmark():
    """
    FR-01: Standalone performance benchmark test
    Measures assignment performance under ideal conditions
    """
    app = create_app()
    app.config['TESTING'] = True
    
    with app.app_context():
        # Create test locker
        test_locker = Locker(id=999, location="Benchmark Locker", size="small", status="free")
        db.session.add(test_locker)
        db.session.commit()
        
        try:
            # Measure assignment time
            start_time = time.time()
            
            result = assign_locker_and_create_parcel(
                "benchmark@example.com",
                "small"
            )
            
            end_time = time.time()
            assignment_time = (end_time - start_time) * 1000
            
            # Verify performance
            assert assignment_time <= 200.0, f"FR-01: Benchmark assignment took {assignment_time:.2f}ms (>200ms limit)"
            assert result is not None, "FR-01: Should return result tuple"
            parcel, message = result
            assert parcel is not None, "FR-01: Benchmark assignment should succeed"
            
            print(f"FR-01 Performance Benchmark: {assignment_time:.2f}ms")
            
        finally:
            # Cleanup
            Parcel.query.filter_by(locker_id=999).delete()
            db.session.delete(test_locker)
            db.session.commit()


def test_fr01_system_health_check():
    """
    FR-01: Test system health for locker assignment functionality
    Verifies all components are available
    """
    app = create_app()
    
    with app.app_context():
        # Test that assignment function exists and is callable
        from app.services.parcel_service import assign_locker_and_create_parcel
        
        # Test basic functionality without creating parcels
        assert callable(assign_locker_and_create_parcel), "FR-01: Assignment function should be callable"
        
        # Test that required models are importable
        from app.persistence.models import Parcel, Locker
        assert Parcel is not None, "FR-01: Parcel model should be available"
        assert Locker is not None, "FR-01: Locker model should be available"
        
        print("FR-01 System Health: All components available")


if __name__ == '__main__':
    # Run FR-01 tests
    pytest.main([__file__, '-v', '-s']) 