"""
Performance tests for locker assignment during deposit process
Measures response times in milliseconds for various scenarios
"""

import pytest
import time
import statistics
from app import db
from app.services.parcel_service import assign_locker_and_create_parcel
from app.business.parcel import Parcel
from app.persistence.models import Locker

# Repository Imports
from app.persistence.repositories.locker_repository import LockerRepository
from app.persistence.repositories.parcel_repository import ParcelRepository

class TestLockerAssignmentPerformance:
    
    def test_single_locker_assignment_performance(self, init_database, app):
        """Test performance of single locker assignment"""
        with app.app_context():
            # Warm up the database connection
            LockerRepository.get_count()
            
            # Measure single assignment
            start_time = time.perf_counter()
            parcel, message = assign_locker_and_create_parcel('perf-test@example.com', 'medium')
            end_time = time.perf_counter()
            
            assignment_time_ms = (end_time - start_time) * 1000
            
            print(f"\n📊 Single Locker Assignment Performance:")
            print(f"   Time: {assignment_time_ms:.3f} ms")
            print(f"   Result: {'SUCCESS' if parcel else 'FAILED'}")
            if parcel:
                print(f"   Assigned Locker: {parcel.locker_id}")
                print(f"   Parcel ID: {parcel.id}")
            
            assert parcel is not None
            assert assignment_time_ms < 1000  # Should be under 1 second
            
            return assignment_time_ms

    def test_multiple_assignments_performance(self, init_database, app):
        """Test performance of multiple consecutive locker assignments"""
        with app.app_context():
            times = []
            successful_assignments = 0
            
            print(f"\n📊 Multiple Locker Assignment Performance Test:")
            print(f"   Testing 10 consecutive assignments...")
            
            for i in range(10):
                start_time = time.perf_counter()
                parcel, message = assign_locker_and_create_parcel(f'perf-test-{i}@example.com', 'small')
                end_time = time.perf_counter()
                
                assignment_time_ms = (end_time - start_time) * 1000
                times.append(assignment_time_ms)
                
                if parcel:
                    successful_assignments += 1
                    print(f"   Assignment {i+1}: {assignment_time_ms:.3f} ms (Locker {parcel.locker_id})")
                else:
                    print(f"   Assignment {i+1}: {assignment_time_ms:.3f} ms (FAILED: {message})")
            
            if times:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                median_time = statistics.median(times)
                
                print(f"\n📈 Performance Statistics:")
                print(f"   Successful Assignments: {successful_assignments}/10")
                print(f"   Average Time: {avg_time:.3f} ms")
                print(f"   Median Time: {median_time:.3f} ms")
                print(f"   Min Time: {min_time:.3f} ms")
                print(f"   Max Time: {max_time:.3f} ms")
                print(f"   Total Time: {sum(times):.3f} ms")
                
                # Performance assertions
                assert avg_time < 500  # Average should be under 500ms
                assert max_time < 1000  # No single assignment should take over 1s
                
                return {
                    'successful_assignments': successful_assignments,
                    'average_ms': avg_time,
                    'median_ms': median_time,
                    'min_ms': min_time,
                    'max_ms': max_time,
                    'total_ms': sum(times)
                }

    def test_locker_size_assignment_performance(self, init_database, app):
        """Test performance across different locker sizes"""
        with app.app_context():
            sizes = ['small', 'medium', 'large']
            size_performance = {}
            
            print(f"\n📊 Locker Size Assignment Performance:")
            
            for size in sizes:
                times = []
                successful = 0
                
                # Test 5 assignments per size
                for i in range(5):
                    start_time = time.perf_counter()
                    parcel, message = assign_locker_and_create_parcel(f'size-test-{size}-{i}@example.com', size)
                    end_time = time.perf_counter()
                    
                    assignment_time_ms = (end_time - start_time) * 1000
                    times.append(assignment_time_ms)
                    
                    if parcel:
                        successful += 1
                
                if times:
                    avg_time = statistics.mean(times)
                    size_performance[size] = {
                        'average_ms': avg_time,
                        'successful': successful,
                        'total_attempts': 5
                    }
                    
                    print(f"   {size.upper()} lockers: {avg_time:.3f} ms avg ({successful}/5 successful)")
            
            # Performance comparison
            if len(size_performance) > 1:
                fastest_size = min(size_performance.keys(), key=lambda k: size_performance[k]['average_ms'])
                slowest_size = max(size_performance.keys(), key=lambda k: size_performance[k]['average_ms'])
                
                print(f"\n🏃 Performance Comparison:")
                print(f"   Fastest: {fastest_size} ({size_performance[fastest_size]['average_ms']:.3f} ms)")
                print(f"   Slowest: {slowest_size} ({size_performance[slowest_size]['average_ms']:.3f} ms)")
            
            return size_performance

    def test_concurrent_assignment_simulation(self, init_database, app):
        """Test performance under simulated concurrent load"""
        with app.app_context():
            import threading
            import queue
            
            results_queue = queue.Queue()
            num_threads = 5
            assignments_per_thread = 3
            
            def assign_lockers(thread_id, results_queue):
                thread_times = []
                thread_successes = 0
                
                for i in range(assignments_per_thread):
                    start_time = time.perf_counter()
                    parcel, message = assign_locker_and_create_parcel(
                        f'concurrent-t{thread_id}-{i}@example.com', 'medium'
                    )
                    end_time = time.perf_counter()
                    
                    assignment_time_ms = (end_time - start_time) * 1000
                    thread_times.append(assignment_time_ms)
                    
                    if parcel:
                        thread_successes += 1
                
                results_queue.put({
                    'thread_id': thread_id,
                    'times': thread_times,
                    'successes': thread_successes
                })
            
            print(f"\n📊 Concurrent Assignment Performance Test:")
            print(f"   Simulating {num_threads} concurrent users...")
            print(f"   {assignments_per_thread} assignments per user...")
            
            # Start concurrent assignments
            start_time = time.perf_counter()
            threads = []
            
            for thread_id in range(num_threads):
                thread = threading.Thread(target=assign_lockers, args=(thread_id, results_queue))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            end_time = time.perf_counter()
            total_execution_time = (end_time - start_time) * 1000
            
            # Collect results
            all_times = []
            total_successes = 0
            
            while not results_queue.empty():
                result = results_queue.get()
                all_times.extend(result['times'])
                total_successes += result['successes']
                
                thread_avg = statistics.mean(result['times'])
                print(f"   Thread {result['thread_id']}: {thread_avg:.3f} ms avg ({result['successes']}/{assignments_per_thread} successful)")
            
            if all_times:
                overall_avg = statistics.mean(all_times)
                total_attempts = num_threads * assignments_per_thread
                
                print(f"\n📈 Concurrent Performance Summary:")
                print(f"   Total Execution Time: {total_execution_time:.3f} ms")
                print(f"   Total Successful: {total_successes}/{total_attempts}")
                print(f"   Overall Average: {overall_avg:.3f} ms per assignment")
                print(f"   Throughput: {total_successes/(total_execution_time/1000):.1f} assignments/second")
                
                # Performance assertions for concurrent load
                assert total_successes > 0  # At least some should succeed
                assert overall_avg < 2000  # Should handle concurrent load reasonably
                
                return {
                    'total_execution_ms': total_execution_time,
                    'successful_assignments': total_successes,
                    'total_attempts': total_attempts,
                    'average_assignment_ms': overall_avg,
                    'throughput_per_second': total_successes/(total_execution_time/1000)
                }

    def test_database_performance_under_load(self, init_database, app):
        """Test database performance during locker assignment"""
        with app.app_context():
            print(f"\n📊 Database Performance Analysis:")
            
            # Check initial database state using repositories
            initial_locker_count = LockerRepository.get_count()
            initial_parcel_count = ParcelRepository.get_count()
            
            print(f"   Initial State:")
            print(f"   - Total Lockers: {initial_locker_count}")
            print(f"   - Total Parcels: {initial_parcel_count}")
            print(f"   - Free Lockers: {LockerRepository.get_count_by_status('free')}")
            
            # Measure database query performance
            query_times = []
            
            # Test locker availability queries
            for _ in range(10):
                start_time = time.perf_counter()
                all_lockers = LockerRepository.get_all()
                available_lockers = [l for l in all_lockers if l.status == 'free']
                end_time = time.perf_counter()
                
                query_time_ms = (end_time - start_time) * 1000
                query_times.append(query_time_ms)
            
            avg_query_time = statistics.mean(query_times)
            print(f"   Average Query Time: {avg_query_time:.3f} ms")
            
            # Test assignment with database timing
            assignment_times = []
            db_operation_times = []
            
            for i in range(5):
                # Time the entire assignment
                total_start = time.perf_counter()
                
                # Time just the database operations
                db_start = time.perf_counter()
                parcel, message = assign_locker_and_create_parcel(f'db-perf-{i}@example.com', 'large')
                db_end = time.perf_counter()
                
                total_end = time.perf_counter()
                
                total_time_ms = (total_end - total_start) * 1000
                db_time_ms = (db_end - db_start) * 1000
                
                assignment_times.append(total_time_ms)
                db_operation_times.append(db_time_ms)
                
                if parcel:
                    print(f"   Assignment {i+1}: {total_time_ms:.3f} ms total, {db_time_ms:.3f} ms DB ops")
            
            print(f"\n📈 Database Performance Summary:")
            print(f"   Average Query Time: {avg_query_time:.3f} ms")
            print(f"   Average DB Operations: {statistics.mean(db_operation_times):.3f} ms")
            print(f"   Average Total Assignment: {statistics.mean(assignment_times):.3f} ms")
            
            return {
                'average_query_ms': avg_query_time,
                'average_db_operations_ms': statistics.mean(db_operation_times),
                'average_total_assignment_ms': statistics.mean(assignment_times)
            }

def test_comprehensive_performance_report(init_database, app):
    """Generate a comprehensive performance report"""
    print(f"\n🚀 COMPREHENSIVE LOCKER ASSIGNMENT PERFORMANCE REPORT")
    print(f"=" * 60)
    
    test_instance = TestLockerAssignmentPerformance()
    
    # Run all performance tests
    single_time = test_instance.test_single_locker_assignment_performance(init_database, app)
    multiple_stats = test_instance.test_multiple_assignments_performance(init_database, app)
    size_stats = test_instance.test_locker_size_assignment_performance(init_database, app)
    concurrent_stats = test_instance.test_concurrent_assignment_simulation(init_database, app)
    db_stats = test_instance.test_database_performance_under_load(init_database, app)
    
    print(f"\n🎯 PERFORMANCE SUMMARY:")
    print(f"   Single Assignment: {single_time:.3f} ms")
    if multiple_stats:
        print(f"   Multiple Avg: {multiple_stats['average_ms']:.3f} ms")
        print(f"   Success Rate: {multiple_stats['successful_assignments']}/10")
    if concurrent_stats:
        print(f"   Concurrent Throughput: {concurrent_stats['throughput_per_second']:.1f} assignments/sec")
    if db_stats:
        print(f"   Database Query Avg: {db_stats['average_query_ms']:.3f} ms")
    
    print(f"\n✅ Performance tests completed successfully!")
    
    return {
        'single_assignment_ms': single_time,
        'multiple_assignment_stats': multiple_stats,
        'size_performance': size_stats,
        'concurrent_performance': concurrent_stats,
        'database_performance': db_stats
    } 