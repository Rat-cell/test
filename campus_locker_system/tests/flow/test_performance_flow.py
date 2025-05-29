#!/usr/bin/env python3
"""
Performance Test Flow - Campus Locker System
Tests locker assignment performance during deposit process
Measures response times in milliseconds for various scenarios
"""

import pytest
import time
import statistics
from app import db
from app.services.parcel_service import assign_locker_and_create_parcel
from app.business.parcel import Parcel
from app.persistence.models import Locker

def test_locker_assignment_performance_flow(app):
    """
    Complete performance test flow for locker assignment during deposit process
    Tests single assignments, multiple assignments, and size-specific performance
    """
    with app.app_context():
        print('\n🧪 Locker Assignment Performance Test Flow')
        print('=' * 55)
        
        # Test 1: Single Assignment Performance
        print('\n📊 Test 1: Single Assignment Performance')
        start_time = time.perf_counter()
        parcel, message = assign_locker_and_create_parcel('perf-single@example.com', 'medium')
        end_time = time.perf_counter()
        
        single_time_ms = (end_time - start_time) * 1000
        print(f'   Time: {single_time_ms:.3f} ms')
        
        if parcel:
            print(f'   ✅ SUCCESS - Locker {parcel.locker_id}, Parcel {parcel.id}')
            assert parcel is not None
            assert single_time_ms < 1000  # Should be under 1 second
        else:
            print(f'   ❌ FAILED: {message}')
            
        # Test 2: Multiple Assignment Performance
        print('\n📊 Test 2: Multiple Assignment Performance (10 assignments)')
        times = []
        successful = 0
        
        for i in range(10):
            start_time = time.perf_counter()
            p, m = assign_locker_and_create_parcel(f'perf-multi-{i}@example.com', 'small')
            end_time = time.perf_counter()
            
            assignment_time_ms = (end_time - start_time) * 1000
            times.append(assignment_time_ms)
            
            if p:
                successful += 1
                print(f'   Assignment {i+1}: {assignment_time_ms:.3f} ms (✅ Locker {p.locker_id})')
            else:
                print(f'   Assignment {i+1}: {assignment_time_ms:.3f} ms (❌ {m})')
        
        # Performance Statistics
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            median_time = statistics.median(times)
            
            print(f'\n📈 Performance Statistics:')
            print(f'   Successful: {successful}/10 assignments')
            print(f'   Average: {avg_time:.3f} ms')
            print(f'   Median: {median_time:.3f} ms')
            print(f'   Min: {min_time:.3f} ms')
            print(f'   Max: {max_time:.3f} ms')
            print(f'   Total: {sum(times):.3f} ms')
            
            # Performance Rating
            if avg_time < 50:
                performance_rating = "🔥 EXCELLENT"
                rating_color = "green"
            elif avg_time < 100:
                performance_rating = "✅ GOOD"
                rating_color = "yellow"
            elif avg_time < 200:
                performance_rating = "⚠️ ACCEPTABLE"
                rating_color = "orange"
            else:
                performance_rating = "❌ NEEDS OPTIMIZATION"
                rating_color = "red"
            
            print(f'\n🎯 Performance Rating: {performance_rating}')
            print(f'   Throughput: {1000/avg_time:.1f} assignments/second')
            
            # Performance assertions
            assert avg_time < 500  # Average should be reasonable
            
        # Test 3: Size-Specific Assignment Performance
        print('\n📊 Test 3: Size-Specific Assignment Performance')
        sizes = ['small', 'medium', 'large']
        size_performance = {}
        
        for size in sizes:
            size_times = []
            size_successful = 0
            
            # Test 3 assignments per size
            for i in range(3):
                start_time = time.perf_counter()
                p, m = assign_locker_and_create_parcel(f'perf-size-{size}-{i}@example.com', size)
                end_time = time.perf_counter()
                
                assignment_time_ms = (end_time - start_time) * 1000
                size_times.append(assignment_time_ms)
                
                if p:
                    size_successful += 1
            
            if size_times:
                avg_size_time = statistics.mean(size_times)
                size_performance[size] = {
                    'avg_time_ms': avg_size_time,
                    'successful': size_successful,
                    'total': 3
                }
                success_icon = "✅" if size_successful > 0 else "❌"
                print(f'   {size.upper()}: {avg_size_time:.3f} ms avg ({success_icon} {size_successful}/3 successful)')
        
        # Size Performance Comparison
        if len(size_performance) > 1:
            available_sizes = {k: v for k, v in size_performance.items() if v['successful'] > 0}
            if available_sizes:
                fastest_size = min(available_sizes.keys(), key=lambda k: available_sizes[k]['avg_time_ms'])
                slowest_size = max(available_sizes.keys(), key=lambda k: available_sizes[k]['avg_time_ms'])
                
                print(f'\n🏃 Size Performance Comparison:')
                print(f'   🚀 Fastest: {fastest_size} ({available_sizes[fastest_size]["avg_time_ms"]:.3f} ms)')
                print(f'   🐌 Slowest: {slowest_size} ({available_sizes[slowest_size]["avg_time_ms"]:.3f} ms)')
        
        # Test 4: Database Query Performance Analysis
        print('\n📊 Test 4: Database Query Performance Analysis')
        
        # Check current database state
        total_lockers = Locker.query.count()
        free_lockers = Locker.query.filter_by(status='free').count()
        occupied_lockers = Locker.query.filter_by(status='occupied').count()
        
        print(f'   Database State:')
        print(f'   - Total Lockers: {total_lockers}')
        print(f'   - Free Lockers: {free_lockers}')
        print(f'   - Occupied Lockers: {occupied_lockers}')
        
        # Measure query performance
        query_times = []
        for _ in range(5):
            start_time = time.perf_counter()
            available_lockers = Locker.query.filter_by(status='free').all()
            end_time = time.perf_counter()
            
            query_time_ms = (end_time - start_time) * 1000
            query_times.append(query_time_ms)
        
        if query_times:
            avg_query_time = statistics.mean(query_times)
            print(f'   Average Query Time: {avg_query_time:.3f} ms')
            
            # Query performance assertion
            assert avg_query_time < 100  # Queries should be fast
        
        # Test 5: Concurrent Assignment Simulation
        print('\n📊 Test 5: Concurrent Assignment Simulation')
        import threading
        import queue
        
        results_queue = queue.Queue()
        num_threads = 3
        assignments_per_thread = 2
        
        def concurrent_assign_lockers(thread_id, results_queue):
            thread_times = []
            thread_successes = 0
            
            for i in range(assignments_per_thread):
                start_time = time.perf_counter()
                parcel, message = assign_locker_and_create_parcel(
                    f'concurrent-t{thread_id}-{i}@example.com', 'large'
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
        
        print(f'   Simulating {num_threads} concurrent users...')
        print(f'   {assignments_per_thread} assignments per user...')
        
        # Start concurrent assignments
        start_time = time.perf_counter()
        threads = []
        
        for thread_id in range(num_threads):
            thread = threading.Thread(target=concurrent_assign_lockers, args=(thread_id, results_queue))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.perf_counter()
        total_execution_time = (end_time - start_time) * 1000
        
        # Collect concurrent results
        all_concurrent_times = []
        total_concurrent_successes = 0
        
        while not results_queue.empty():
            result = results_queue.get()
            all_concurrent_times.extend(result['times'])
            total_concurrent_successes += result['successes']
            
            if result['times']:
                thread_avg = statistics.mean(result['times'])
                success_icon = "✅" if result['successes'] > 0 else "❌"
                print(f'   Thread {result["thread_id"]}: {thread_avg:.3f} ms avg ({success_icon} {result["successes"]}/{assignments_per_thread})')
        
        if all_concurrent_times:
            overall_avg = statistics.mean(all_concurrent_times)
            total_attempts = num_threads * assignments_per_thread
            
            print(f'\n📈 Concurrent Performance Summary:')
            print(f'   Total Execution Time: {total_execution_time:.3f} ms')
            print(f'   Total Successful: {total_concurrent_successes}/{total_attempts}')
            print(f'   Overall Average: {overall_avg:.3f} ms per assignment')
            if total_execution_time > 0:
                throughput = total_concurrent_successes / (total_execution_time / 1000)
                print(f'   Concurrent Throughput: {throughput:.1f} assignments/second')
            
            # Concurrent performance assertion
            assert total_concurrent_successes > 0  # At least some should succeed
            assert overall_avg < 1000  # Should handle concurrent load reasonably
        
        # Final Summary
        print('\n🎯 PERFORMANCE TEST FLOW SUMMARY:')
        print('=' * 40)
        if 'single_time_ms' in locals():
            print(f'   Single Assignment: {single_time_ms:.3f} ms')
        if 'avg_time' in locals():
            print(f'   Multiple Assignment Avg: {avg_time:.3f} ms')
            print(f'   Success Rate: {successful}/10')
        if 'avg_query_time' in locals():
            print(f'   Database Query Avg: {avg_query_time:.3f} ms')
        if 'overall_avg' in locals():
            print(f'   Concurrent Avg: {overall_avg:.3f} ms')
        
        print(f'\n✅ Performance test flow completed successfully!')
        
        return {
            'single_assignment_ms': single_time_ms if 'single_time_ms' in locals() else None,
            'multiple_assignment_avg_ms': avg_time if 'avg_time' in locals() else None,
            'successful_assignments': successful if 'successful' in locals() else 0,
            'database_query_avg_ms': avg_query_time if 'avg_query_time' in locals() else None,
            'concurrent_avg_ms': overall_avg if 'overall_avg' in locals() else None,
            'size_performance': size_performance if 'size_performance' in locals() else {}
        }

def test_performance_benchmarks(app):
    """Test that performance meets specific benchmarks"""
    with app.app_context():
        print('\n📋 Performance Benchmark Validation')
        print('=' * 40)
        
        # Benchmark 1: Single assignment under 100ms
        start_time = time.perf_counter()
        parcel, message = assign_locker_and_create_parcel('benchmark@example.com', 'medium')
        end_time = time.perf_counter()
        
        assignment_time_ms = (end_time - start_time) * 1000
        
        print(f'   Benchmark 1: Single assignment under 100ms')
        print(f'   Result: {assignment_time_ms:.3f} ms - {"✅ PASS" if assignment_time_ms < 100 else "❌ FAIL"}')
        
        # Benchmark 2: Database query under 50ms
        start_time = time.perf_counter()
        free_lockers = Locker.query.filter_by(status='free').count()
        end_time = time.perf_counter()
        
        query_time_ms = (end_time - start_time) * 1000
        
        print(f'   Benchmark 2: Database query under 50ms')
        print(f'   Result: {query_time_ms:.3f} ms - {"✅ PASS" if query_time_ms < 50 else "❌ FAIL"}')
        
        # Assertions for benchmarks
        assert assignment_time_ms < 100, f"Assignment took {assignment_time_ms:.3f}ms, should be under 100ms"
        assert query_time_ms < 50, f"Query took {query_time_ms:.3f}ms, should be under 50ms"
        
        print(f'\n✅ All performance benchmarks passed!')

if __name__ == '__main__':
    # Can be run standalone for testing
    from app import create_app
    app = create_app()
    test_locker_assignment_performance_flow(app)
    test_performance_benchmarks(app) 