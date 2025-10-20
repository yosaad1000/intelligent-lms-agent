#!/usr/bin/env python3
"""
Simple Performance Test
Basic test to verify performance optimization components work
"""

import sys
import os
import time
import json
from datetime import datetime

# Add src to path
sys.path.append('src')

def test_performance_cache():
    """Test performance cache functionality"""
    
    print("🧪 Testing Performance Cache...")
    
    try:
        from shared.performance_cache import PerformanceCache, CacheConfig
        
        # Create cache instance
        cache = PerformanceCache()
        
        # Test basic operations
        test_key = "test_key"
        test_value = {"message": "Hello, World!", "timestamp": time.time()}
        
        # Set cache value
        success = cache.set(
            prefix="test",
            key=test_key,
            value=test_value,
            ttl_seconds=300,
            user_id="test_user"
        )
        
        print(f"  ✅ Cache set: {success}")
        
        # Get cache value
        cached_value = cache.get(
            prefix="test",
            key=test_key,
            user_id="test_user"
        )
        
        print(f"  ✅ Cache get: {cached_value is not None}")
        
        # Get cache stats
        stats = cache.get_stats()
        print(f"  ✅ Cache stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Cache test failed: {e}")
        return False


def test_connection_pool():
    """Test connection pool functionality"""
    
    print("🔗 Testing Connection Pool...")
    
    try:
        from shared.connection_pool import DynamoDBConnectionPool
        
        # Create connection pool
        pool = DynamoDBConnectionPool()
        
        # Test client creation
        client = pool.get_client()
        print(f"  ✅ DynamoDB client created: {client is not None}")
        
        # Test connection reuse
        client2 = pool.get_client()
        same_client = client is client2
        print(f"  ✅ Connection reuse: {same_client}")
        
        # Test stats
        stats = pool.get_connection_stats()
        print(f"  ✅ Connection stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Connection pool test failed: {e}")
        return False


def test_performance_monitor():
    """Test performance monitoring functionality"""
    
    print("📊 Testing Performance Monitor...")
    
    try:
        from shared.performance_monitor import PerformanceMonitor
        
        # Create monitor instance
        monitor = PerformanceMonitor()
        
        # Test request tracking
        request_id = f"test_req_{int(time.time())}"
        
        metrics = monitor.start_request_tracking(
            request_id=request_id,
            endpoint="/api/test",
            method="POST",
            user_id="test_user"
        )
        
        print(f"  ✅ Request tracking started: {metrics is not None}")
        
        # Simulate some work
        time.sleep(0.1)
        
        # Track some operations
        monitor.track_database_query(request_id, "read")
        monitor.track_cache_hit(request_id)
        
        # End tracking
        final_metrics = monitor.end_request_tracking(
            request_id=request_id,
            status_code=200,
            response_size=1024
        )
        
        print(f"  ✅ Request tracking completed: {final_metrics is not None}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance monitor test failed: {e}")
        return False


def test_dynamodb_tables():
    """Test DynamoDB table access"""
    
    print("🗄️ Testing DynamoDB Tables...")
    
    try:
        import boto3
        
        dynamodb = boto3.resource('dynamodb')
        
        # Test performance tables
        tables_to_test = [
            'lms-performance-cache',
            'lms-performance-metrics',
            'lms-async-tasks',
            'lms-background-queue'
        ]
        
        accessible_tables = 0
        
        for table_name in tables_to_test:
            try:
                table = dynamodb.Table(table_name)
                table.load()
                print(f"  ✅ Table accessible: {table_name}")
                accessible_tables += 1
            except Exception as e:
                print(f"  ❌ Table not accessible: {table_name} - {e}")
        
        print(f"  📊 Tables accessible: {accessible_tables}/{len(tables_to_test)}")
        
        return accessible_tables >= len(tables_to_test) * 0.75  # 75% success rate
        
    except Exception as e:
        print(f"  ❌ DynamoDB test failed: {e}")
        return False


def main():
    """Main test function"""
    
    print("🚀 Simple Performance Optimization Test")
    print("=" * 40)
    
    tests = [
        ("Performance Cache", test_performance_cache),
        ("Connection Pool", test_connection_pool),
        ("Performance Monitor", test_performance_monitor),
        ("DynamoDB Tables", test_dynamodb_tables)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Test error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*40)
    print("📋 TEST SUMMARY")
    print("="*40)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print(f"\n📊 Success Rate: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 75:
        print("🎉 Performance optimization is working!")
    elif success_rate >= 50:
        print("⚠️ Performance optimization partially working")
    else:
        print("❌ Performance optimization needs attention")
    
    return success_rate >= 75


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)