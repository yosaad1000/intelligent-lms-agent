#!/usr/bin/env python3
"""
Comprehensive Performance Optimization Testing
Tests all performance features including caching, connection pooling, async processing, and monitoring
"""

import asyncio
import time
import json
import uuid
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import performance modules
try:
    from src.shared.performance_cache import performance_cache, CacheConfig
    from src.shared.connection_pool import dynamodb_pool, s3_pool, bedrock_pool
    from src.shared.async_processor import async_task_manager, background_task_queue
    from src.shared.performance_monitor import performance_monitor, track_performance
    from src.shared.performance_integration import performance_optimizer
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Make sure you're running from the project root directory")
    exit(1)


class PerformanceTestSuite:
    """Comprehensive performance testing suite"""
    
    def __init__(self):
        self.test_results = {}
        self.test_user_id = "perf_test_user"
        
    async def run_all_tests(self):
        """Run all performance tests"""
        
        print("🚀 Starting Comprehensive Performance Testing")
        print("=" * 50)
        
        # Test 1: Cache Performance
        print("\n1️⃣ Testing Cache Performance...")
        cache_results = await self.test_cache_performance()
        self.test_results['cache'] = cache_results
        
        # Test 2: Connection Pool Performance
        print("\n2️⃣ Testing Connection Pool Performance...")
        connection_results = await self.test_connection_pool_performance()
        self.test_results['connection_pool'] = connection_results
        
        # Test 3: Async Processing Performance
        print("\n3️⃣ Testing Async Processing Performance...")
        async_results = await self.test_async_processing_performance()
        self.test_results['async_processing'] = async_results
        
        # Test 4: Performance Monitoring
        print("\n4️⃣ Testing Performance Monitoring...")
        monitoring_results = await self.test_performance_monitoring()
        self.test_results['monitoring'] = monitoring_results
        
        # Test 5: Integration Performance
        print("\n5️⃣ Testing Integration Performance...")
        integration_results = await self.test_integration_performance()
        self.test_results['integration'] = integration_results
        
        # Test 6: Load Testing
        print("\n6️⃣ Testing Load Performance...")
        load_results = await self.test_load_performance()
        self.test_results['load_testing'] = load_results
        
        # Generate summary report
        self.generate_summary_report()
        
        return self.test_results
    
    async def test_cache_performance(self):
        """Test cache performance and functionality"""
        
        results = {
            'test_name': 'Cache Performance',
            'tests_passed': 0,
            'tests_failed': 0,
            'performance_metrics': {},
            'errors': []
        }
        
        try:
            # Test 1: Basic cache operations
            print("  📝 Testing basic cache operations...")
            
            start_time = time.time()
            
            # Set cache values
            for i in range(100):
                key = f"test_key_{i}"
                value = {"index": i, "data": f"test_data_{i}", "timestamp": time.time()}
                success = performance_cache.set(
                    prefix="performance_test",
                    key=key,
                    value=value,
                    ttl_seconds=300,
                    user_id=self.test_user_id
                )
                if not success:
                    results['errors'].append(f"Failed to set cache key: {key}")
            
            set_time = time.time() - start_time
            
            # Get cache values
            start_time = time.time()
            cache_hits = 0
            
            for i in range(100):
                key = f"test_key_{i}"
                cached_value = performance_cache.get(
                    prefix="performance_test",
                    key=key,
                    user_id=self.test_user_id
                )
                if cached_value:
                    cache_hits += 1
            
            get_time = time.time() - start_time
            
            results['performance_metrics']['cache_set_time_ms'] = set_time * 1000
            results['performance_metrics']['cache_get_time_ms'] = get_time * 1000
            results['performance_metrics']['cache_hit_rate'] = cache_hits / 100
            
            if cache_hits >= 95:  # At least 95% hit rate
                results['tests_passed'] += 1
                print(f"    ✅ Basic cache operations: {cache_hits}% hit rate")
            else:
                results['tests_failed'] += 1
                print(f"    ❌ Basic cache operations: {cache_hits}% hit rate (expected ≥95%)")
            
            # Test 2: Cache invalidation
            print("  🗑️ Testing cache invalidation...")
            
            invalidated_count = performance_cache.invalidate_pattern(
                prefix="performance_test",
                user_id=self.test_user_id
            )
            
            if invalidated_count >= 50:  # Should invalidate most entries
                results['tests_passed'] += 1
                print(f"    ✅ Cache invalidation: {invalidated_count} entries invalidated")
            else:
                results['tests_failed'] += 1
                print(f"    ❌ Cache invalidation: {invalidated_count} entries invalidated (expected ≥50)")
            
            # Test 3: Cache statistics
            print("  📊 Testing cache statistics...")
            
            stats = performance_cache.get_stats()
            
            if isinstance(stats, dict) and 'memory_cache_size' in stats:
                results['tests_passed'] += 1
                print(f"    ✅ Cache statistics: {stats}")
            else:
                results['tests_failed'] += 1
                results['errors'].append("Cache statistics not available")
                print(f"    ❌ Cache statistics not available")
            
        except Exception as e:
            results['tests_failed'] += 1
            results['errors'].append(f"Cache test error: {str(e)}")
            print(f"    ❌ Cache test error: {e}")
        
        return results
    
    async def test_connection_pool_performance(self):
        """Test connection pool performance"""
        
        results = {
            'test_name': 'Connection Pool Performance',
            'tests_passed': 0,
            'tests_failed': 0,
            'performance_metrics': {},
            'errors': []
        }
        
        try:
            # Test 1: DynamoDB connection reuse
            print("  🔗 Testing DynamoDB connection reuse...")
            
            start_time = time.time()
            
            # Get multiple clients
            clients = []
            for i in range(50):
                client = dynamodb_pool.get_client()
                clients.append(client)
            
            connection_time = time.time() - start_time
            
            # Check if connections are reused (should be same instance)
            unique_clients = len(set(id(client) for client in clients))
            
            results['performance_metrics']['connection_time_ms'] = connection_time * 1000
            results['performance_metrics']['unique_clients'] = unique_clients
            results['performance_metrics']['total_requests'] = len(clients)
            
            if unique_clients <= 5:  # Should reuse connections
                results['tests_passed'] += 1
                print(f"    ✅ Connection reuse: {unique_clients} unique clients for {len(clients)} requests")
            else:
                results['tests_failed'] += 1
                print(f"    ❌ Connection reuse: {unique_clients} unique clients (expected ≤5)")
            
            # Test 2: Connection pool statistics
            print("  📈 Testing connection pool statistics...")
            
            stats = dynamodb_pool.get_connection_stats()
            
            if isinstance(stats, dict) and 'active_connections' in stats:
                results['tests_passed'] += 1
                print(f"    ✅ Connection pool stats: {stats}")
            else:
                results['tests_failed'] += 1
                results['errors'].append("Connection pool statistics not available")
                print(f"    ❌ Connection pool statistics not available")
            
        except Exception as e:
            results['tests_failed'] += 1
            results['errors'].append(f"Connection pool test error: {str(e)}")
            print(f"    ❌ Connection pool test error: {e}")
        
        return results
    
    async def test_async_processing_performance(self):
        """Test async processing performance"""
        
        results = {
            'test_name': 'Async Processing Performance',
            'tests_passed': 0,
            'tests_failed': 0,
            'performance_metrics': {},
            'errors': []
        }
        
        try:
            # Test 1: Async task submission
            print("  ⚡ Testing async task submission...")
            
            async def test_task(user_id, task_number):
                """Simple test task"""
                await asyncio.sleep(0.01)  # Simulate work
                return {"task_number": task_number, "result": f"completed_{task_number}"}
            
            start_time = time.time()
            task_ids = []
            
            # Submit multiple tasks
            for i in range(20):
                task_id = await async_task_manager.submit_task(
                    "performance_test",
                    self.test_user_id,
                    test_task,
                    self.test_user_id,
                    i
                )
                task_ids.append(task_id)
            
            submission_time = time.time() - start_time
            
            # Wait for tasks to complete
            await asyncio.sleep(2.0)
            
            # Check task completion
            completed_tasks = 0
            for task_id in task_ids:
                task_status = await async_task_manager.get_task_status(task_id)
                if task_status and task_status.status == 'completed':
                    completed_tasks += 1
            
            results['performance_metrics']['task_submission_time_ms'] = submission_time * 1000
            results['performance_metrics']['tasks_submitted'] = len(task_ids)
            results['performance_metrics']['tasks_completed'] = completed_tasks
            results['performance_metrics']['completion_rate'] = completed_tasks / len(task_ids)
            
            if completed_tasks >= len(task_ids) * 0.8:  # At least 80% completion
                results['tests_passed'] += 1
                print(f"    ✅ Async tasks: {completed_tasks}/{len(task_ids)} completed")
            else:
                results['tests_failed'] += 1
                print(f"    ❌ Async tasks: {completed_tasks}/{len(task_ids)} completed (expected ≥80%)")
            
            # Test 2: Background task queue
            print("  📋 Testing background task queue...")
            
            # Mock background task submission
            message_id = await background_task_queue.enqueue_task(
                task_type="performance_test_bg",
                user_id=self.test_user_id,
                task_data={"test": "background_task"}
            )
            
            if message_id:
                results['tests_passed'] += 1
                print(f"    ✅ Background task queued: {message_id}")
            else:
                results['tests_failed'] += 1
                results['errors'].append("Background task queue not available")
                print(f"    ❌ Background task queue not available")
            
        except Exception as e:
            results['tests_failed'] += 1
            results['errors'].append(f"Async processing test error: {str(e)}")
            print(f"    ❌ Async processing test error: {e}")
        
        return results
    
    async def test_performance_monitoring(self):
        """Test performance monitoring functionality"""
        
        results = {
            'test_name': 'Performance Monitoring',
            'tests_passed': 0,
            'tests_failed': 0,
            'performance_metrics': {},
            'errors': []
        }
        
        try:
            # Test 1: Request tracking
            print("  📊 Testing request tracking...")
            
            request_id = f"perf_test_{int(time.time())}"
            
            # Start tracking
            metrics = performance_monitor.start_request_tracking(
                request_id=request_id,
                endpoint="/api/performance/test",
                method="POST",
                user_id=self.test_user_id
            )
            
            if metrics:
                results['tests_passed'] += 1
                print(f"    ✅ Request tracking started: {request_id}")
            else:
                results['tests_failed'] += 1
                print(f"    ❌ Request tracking failed to start")
            
            # Simulate some operations
            time.sleep(0.1)
            performance_monitor.track_database_query(request_id, "read")
            performance_monitor.track_cache_hit(request_id)
            performance_monitor.track_aws_service_call(request_id, "bedrock")
            
            # End tracking
            final_metrics = performance_monitor.end_request_tracking(
                request_id=request_id,
                status_code=200,
                response_size=1024
            )
            
            if final_metrics and final_metrics.duration_ms is not None:
                results['tests_passed'] += 1
                results['performance_metrics']['request_duration_ms'] = final_metrics.duration_ms
                print(f"    ✅ Request tracking completed: {final_metrics.duration_ms:.2f}ms")
            else:
                results['tests_failed'] += 1
                print(f"    ❌ Request tracking completion failed")
            
            # Test 2: Performance context manager
            print("  🎯 Testing performance context manager...")
            
            context_request_id = f"ctx_test_{int(time.time())}"
            
            try:
                with track_performance(context_request_id, "/api/context/test", "GET", self.test_user_id):
                    time.sleep(0.05)  # Simulate work
                
                results['tests_passed'] += 1
                print(f"    ✅ Performance context manager worked")
            except Exception as e:
                results['tests_failed'] += 1
                results['errors'].append(f"Context manager error: {str(e)}")
                print(f"    ❌ Performance context manager failed: {e}")
            
        except Exception as e:
            results['tests_failed'] += 1
            results['errors'].append(f"Performance monitoring test error: {str(e)}")
            print(f"    ❌ Performance monitoring test error: {e}")
        
        return results
    
    async def test_integration_performance(self):
        """Test integrated performance optimization"""
        
        results = {
            'test_name': 'Integration Performance',
            'tests_passed': 0,
            'tests_failed': 0,
            'performance_metrics': {},
            'errors': []
        }
        
        try:
            # Test 1: Performance optimizer health check
            print("  🏥 Testing performance optimizer health...")
            
            health = await performance_optimizer.health_check()
            
            if health and health.get('status') in ['healthy', 'degraded']:
                results['tests_passed'] += 1
                print(f"    ✅ Performance optimizer health: {health['status']}")
            else:
                results['tests_failed'] += 1
                results['errors'].append("Performance optimizer health check failed")
                print(f"    ❌ Performance optimizer health check failed")
            
            # Test 2: Performance metrics retrieval
            print("  📈 Testing performance metrics retrieval...")
            
            metrics = await performance_optimizer.get_performance_metrics(hours=1)
            
            if isinstance(metrics, dict):
                results['tests_passed'] += 1
                print(f"    ✅ Performance metrics retrieved")
            else:
                results['tests_failed'] += 1
                results['errors'].append("Performance metrics retrieval failed")
                print(f"    ❌ Performance metrics retrieval failed")
            
            # Test 3: System optimization
            print("  🔧 Testing system optimization...")
            
            optimization_results = await performance_optimizer.optimize_system_performance()
            
            if isinstance(optimization_results, dict) and 'optimizations_applied' in optimization_results:
                results['tests_passed'] += 1
                optimizations = len(optimization_results['optimizations_applied'])
                print(f"    ✅ System optimization: {optimizations} optimizations applied")
            else:
                results['tests_failed'] += 1
                results['errors'].append("System optimization failed")
                print(f"    ❌ System optimization failed")
            
            # Test 4: Performance analysis
            print("  🔍 Testing performance analysis...")
            
            analysis = await performance_optimizer.analyze_performance_issues()
            
            if isinstance(analysis, dict) and 'issues' in analysis:
                results['tests_passed'] += 1
                issues_count = len(analysis['issues'])
                print(f"    ✅ Performance analysis: {issues_count} issues identified")
            else:
                results['tests_failed'] += 1
                results['errors'].append("Performance analysis failed")
                print(f"    ❌ Performance analysis failed")
            
        except Exception as e:
            results['tests_failed'] += 1
            results['errors'].append(f"Integration test error: {str(e)}")
            print(f"    ❌ Integration test error: {e}")
        
        return results
    
    async def test_load_performance(self):
        """Test performance under load"""
        
        results = {
            'test_name': 'Load Performance',
            'tests_passed': 0,
            'tests_failed': 0,
            'performance_metrics': {},
            'errors': []
        }
        
        try:
            # Test 1: Concurrent cache operations
            print("  🚀 Testing concurrent cache operations...")
            
            async def cache_worker(worker_id):
                """Worker for concurrent cache operations"""
                operations = []
                
                for i in range(10):
                    start_time = time.time()
                    
                    # Set operation
                    key = f"load_test_{worker_id}_{i}"
                    value = {"worker": worker_id, "item": i, "timestamp": time.time()}
                    
                    success = performance_cache.set(
                        prefix="load_test",
                        key=key,
                        value=value,
                        user_id=f"load_user_{worker_id}"
                    )
                    
                    # Get operation
                    cached_value = performance_cache.get(
                        prefix="load_test",
                        key=key,
                        user_id=f"load_user_{worker_id}"
                    )
                    
                    operation_time = (time.time() - start_time) * 1000
                    operations.append({
                        'set_success': success,
                        'get_success': cached_value is not None,
                        'duration_ms': operation_time
                    })
                
                return operations
            
            # Run concurrent workers
            start_time = time.time()
            workers = [cache_worker(i) for i in range(10)]
            worker_results = await asyncio.gather(*workers)
            total_time = time.time() - start_time
            
            # Analyze results
            all_operations = []
            for worker_ops in worker_results:
                all_operations.extend(worker_ops)
            
            successful_sets = sum(1 for op in all_operations if op['set_success'])
            successful_gets = sum(1 for op in all_operations if op['get_success'])
            avg_duration = statistics.mean([op['duration_ms'] for op in all_operations])
            
            results['performance_metrics']['concurrent_operations'] = len(all_operations)
            results['performance_metrics']['successful_sets'] = successful_sets
            results['performance_metrics']['successful_gets'] = successful_gets
            results['performance_metrics']['avg_operation_duration_ms'] = avg_duration
            results['performance_metrics']['total_load_test_time_s'] = total_time
            results['performance_metrics']['operations_per_second'] = len(all_operations) / total_time
            
            success_rate = (successful_sets + successful_gets) / (len(all_operations) * 2)
            
            if success_rate >= 0.9:  # 90% success rate
                results['tests_passed'] += 1
                print(f"    ✅ Concurrent cache operations: {success_rate:.1%} success rate")
            else:
                results['tests_failed'] += 1
                print(f"    ❌ Concurrent cache operations: {success_rate:.1%} success rate (expected ≥90%)")
            
            # Test 2: Connection pool under load
            print("  🔗 Testing connection pool under load...")
            
            start_time = time.time()
            
            # Get many connections concurrently
            connection_tasks = []
            for i in range(50):
                task = asyncio.create_task(self.get_connection_async())
                connection_tasks.append(task)
            
            connection_results = await asyncio.gather(*connection_tasks, return_exceptions=True)
            connection_time = time.time() - start_time
            
            successful_connections = sum(1 for result in connection_results if not isinstance(result, Exception))
            
            results['performance_metrics']['connection_requests'] = len(connection_tasks)
            results['performance_metrics']['successful_connections'] = successful_connections
            results['performance_metrics']['connection_load_time_s'] = connection_time
            
            if successful_connections >= len(connection_tasks) * 0.9:  # 90% success
                results['tests_passed'] += 1
                print(f"    ✅ Connection pool load: {successful_connections}/{len(connection_tasks)} successful")
            else:
                results['tests_failed'] += 1
                print(f"    ❌ Connection pool load: {successful_connections}/{len(connection_tasks)} successful")
            
        except Exception as e:
            results['tests_failed'] += 1
            results['errors'].append(f"Load test error: {str(e)}")
            print(f"    ❌ Load test error: {e}")
        
        return results
    
    async def get_connection_async(self):
        """Async helper for connection testing"""
        try:
            client = dynamodb_pool.get_client()
            return client is not None
        except Exception as e:
            return e
    
    def generate_summary_report(self):
        """Generate comprehensive test summary report"""
        
        print("\n" + "="*60)
        print("🎯 PERFORMANCE OPTIMIZATION TEST SUMMARY")
        print("="*60)
        
        total_tests_passed = 0
        total_tests_failed = 0
        total_errors = []
        
        for test_name, results in self.test_results.items():
            passed = results.get('tests_passed', 0)
            failed = results.get('tests_failed', 0)
            errors = results.get('errors', [])
            
            total_tests_passed += passed
            total_tests_failed += failed
            total_errors.extend(errors)
            
            status = "✅ PASS" if failed == 0 else "❌ FAIL"
            print(f"\n{status} {results.get('test_name', test_name)}")
            print(f"  Passed: {passed}, Failed: {failed}")
            
            # Show key performance metrics
            metrics = results.get('performance_metrics', {})
            if metrics:
                print(f"  Key Metrics:")
                for metric, value in list(metrics.items())[:3]:  # Show top 3 metrics
                    if isinstance(value, float):
                        print(f"    {metric}: {value:.2f}")
                    else:
                        print(f"    {metric}: {value}")
        
        # Overall summary
        total_tests = total_tests_passed + total_tests_failed
        success_rate = (total_tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {total_tests_passed}")
        print(f"  Failed: {total_tests_failed}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # Performance recommendations
        print(f"\n💡 PERFORMANCE RECOMMENDATIONS:")
        
        if success_rate >= 90:
            print("  🎉 Excellent! Performance optimization is working well.")
            print("  ✅ All major performance features are functional.")
        elif success_rate >= 70:
            print("  ⚠️ Good performance with some issues to address.")
            print("  🔧 Review failed tests and optimize accordingly.")
        else:
            print("  🚨 Performance optimization needs attention.")
            print("  🛠️ Multiple systems require fixes and optimization.")
        
        # Show critical errors
        if total_errors:
            print(f"\n🚨 CRITICAL ERRORS ({len(total_errors)}):")
            for i, error in enumerate(total_errors[:5], 1):  # Show first 5 errors
                print(f"  {i}. {error}")
            
            if len(total_errors) > 5:
                print(f"  ... and {len(total_errors) - 5} more errors")
        
        print(f"\n✅ Performance testing completed at {datetime.utcnow().isoformat()}")
        print("="*60)


async def main():
    """Main performance testing function"""
    
    print("🚀 Comprehensive Performance Optimization Testing")
    print("Testing all performance features and optimizations")
    print("=" * 60)
    
    # Create test suite
    test_suite = PerformanceTestSuite()
    
    # Run all tests
    results = await test_suite.run_all_tests()
    
    # Return success based on overall results
    total_passed = sum(r.get('tests_passed', 0) for r in results.values())
    total_failed = sum(r.get('tests_failed', 0) for r in results.values())
    
    success_rate = total_passed / (total_passed + total_failed) if (total_passed + total_failed) > 0 else 0
    
    return success_rate >= 0.8  # 80% success rate required


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)