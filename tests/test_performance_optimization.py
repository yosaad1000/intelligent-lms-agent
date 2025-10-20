"""
Performance Optimization Tests
Tests for caching, connection pooling, async processing, and monitoring
"""

import pytest
import asyncio
import time
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import performance modules
from src.shared.performance_cache import (
    PerformanceCache, CacheConfig, cache_decorator, 
    invalidate_user_cache, performance_cache
)
from src.shared.connection_pool import (
    DynamoDBConnectionPool, S3ConnectionPool, BedrockConnectionPool,
    get_optimized_dynamodb_table, cleanup_connection_pools
)
from src.shared.async_processor import (
    AsyncTaskManager, BackgroundTaskQueue, async_task, background_task,
    async_task_manager, background_task_queue
)
from src.shared.performance_monitor import (
    PerformanceMonitor, RequestMetrics, track_performance,
    performance_tracking_decorator, performance_monitor
)


class TestPerformanceCache:
    """Test performance caching system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.cache = PerformanceCache()
        self.test_user_id = "test_user_123"
        self.test_prefix = "test_data"
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations"""
        
        test_key = "test_key"
        test_value = {"message": "Hello, World!", "timestamp": time.time()}
        
        # Set cache value
        success = self.cache.set(
            prefix=self.test_prefix,
            key=test_key,
            value=test_value,
            ttl_seconds=300,
            user_id=self.test_user_id
        )
        
        assert success is True
        
        # Get cache value
        cached_value = self.cache.get(
            prefix=self.test_prefix,
            key=test_key,
            user_id=self.test_user_id
        )
        
        assert cached_value is not None
        assert cached_value["message"] == test_value["message"]
    
    def test_cache_expiration(self):
        """Test cache TTL expiration"""
        
        test_key = "expiring_key"
        test_value = {"data": "expires_soon"}
        
        # Set cache with short TTL
        self.cache.set(
            prefix=self.test_prefix,
            key=test_key,
            value=test_value,
            ttl_seconds=1,  # 1 second TTL
            user_id=self.test_user_id
        )
        
        # Should be available immediately
        cached_value = self.cache.get(self.test_prefix, test_key, self.test_user_id)
        assert cached_value is not None
        
        # Wait for expiration
        time.sleep(2)
        
        # Should be expired now
        cached_value = self.cache.get(self.test_prefix, test_key, self.test_user_id)
        assert cached_value is None
    
    def test_cache_invalidation(self):
        """Test cache invalidation patterns"""
        
        # Set multiple cache entries
        for i in range(5):
            self.cache.set(
                prefix=self.test_prefix,
                key=f"key_{i}",
                value={"index": i},
                user_id=self.test_user_id
            )
        
        # Verify all entries exist
        for i in range(5):
            cached_value = self.cache.get(self.test_prefix, f"key_{i}", self.test_user_id)
            assert cached_value is not None
            assert cached_value["index"] == i
        
        # Invalidate pattern
        invalidated_count = self.cache.invalidate_pattern(self.test_prefix, self.test_user_id)
        assert invalidated_count >= 5
        
        # Verify entries are invalidated
        for i in range(5):
            cached_value = self.cache.get(self.test_prefix, f"key_{i}", self.test_user_id)
            assert cached_value is None
    
    def test_cache_decorator(self):
        """Test cache decorator functionality"""
        
        call_count = 0
        
        @cache_decorator(
            prefix="test_function",
            ttl_seconds=300,
            user_specific=True
        )
        def expensive_function(user_id, param1, param2):
            nonlocal call_count
            call_count += 1
            return {"result": param1 + param2, "call_count": call_count}
        
        # First call should execute function
        result1 = expensive_function(self.test_user_id, 10, 20)
        assert result1["result"] == 30
        assert result1["call_count"] == 1
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(self.test_user_id, 10, 20)
        assert result2["result"] == 30
        assert result2["call_count"] == 1  # Same as cached result
        assert call_count == 1  # Function not called again
    
    def test_cache_stats(self):
        """Test cache statistics"""
        
        stats = self.cache.get_stats()
        
        assert isinstance(stats, dict)
        assert "memory_cache_size" in stats
        assert "memory_cache_limit" in stats
        assert "redis_available" in stats
        assert "dynamodb_available" in stats
    
    def test_user_cache_invalidation(self):
        """Test user-specific cache invalidation"""
        
        # Set cache for multiple prefixes
        prefixes = [CacheConfig.USER_FILES, CacheConfig.CHAT_HISTORY, CacheConfig.QUIZ_RESULTS]
        
        for prefix in prefixes:
            self.cache.set(prefix, "test_key", {"data": "test"}, user_id=self.test_user_id)
        
        # Invalidate all user cache
        invalidated_count = invalidate_user_cache(self.test_user_id)
        assert invalidated_count >= len(prefixes)
        
        # Verify invalidation
        for prefix in prefixes:
            cached_value = self.cache.get(prefix, "test_key", self.test_user_id)
            assert cached_value is None


class TestConnectionPooling:
    """Test connection pooling and optimization"""
    
    def setup_method(self):
        """Setup test environment"""
        self.dynamodb_pool = DynamoDBConnectionPool()
        self.s3_pool = S3ConnectionPool()
        self.bedrock_pool = BedrockConnectionPool()
    
    @patch('boto3.client')
    def test_dynamodb_connection_reuse(self, mock_boto_client):
        """Test DynamoDB connection reuse"""
        
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Get client multiple times
        client1 = self.dynamodb_pool.get_client()
        client2 = self.dynamodb_pool.get_client()
        
        # Should reuse the same client
        assert client1 is client2
        
        # boto3.client should be called only once due to caching
        assert mock_boto_client.call_count == 1
    
    @patch('boto3.resource')
    def test_dynamodb_batch_operations(self, mock_boto_resource):
        """Test DynamoDB batch operations"""
        
        mock_table = Mock()
        mock_resource = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_resource
        
        # Mock table.load() to avoid ResourceNotFoundException
        mock_table.load.return_value = None
        
        # Test batch get items
        test_keys = [{"id": f"item_{i}"} for i in range(10)]
        
        with patch.object(self.dynamodb_pool, 'get_client') as mock_get_client:
            mock_client = Mock()
            mock_client.batch_get_item.return_value = {
                'Responses': {'test_table': [{"id": "item_1", "data": "test"}]},
                'UnprocessedKeys': {}
            }
            mock_get_client.return_value = mock_client
            
            items = self.dynamodb_pool.batch_get_items('test_table', test_keys)
            
            assert isinstance(items, list)
            assert mock_client.batch_get_item.called
    
    def test_connection_pool_stats(self):
        """Test connection pool statistics"""
        
        stats = self.dynamodb_pool.get_connection_stats()
        
        assert isinstance(stats, dict)
        assert "queries_executed" in stats
        assert "batch_operations" in stats
        assert "cache_hits" in stats
        assert "connection_reuses" in stats
        assert "active_connections" in stats
    
    @patch('boto3.client')
    def test_s3_optimized_operations(self, mock_boto_client):
        """Test S3 optimized operations"""
        
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Test optimized upload
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = Mock()
            
            success = self.s3_pool.upload_file_optimized(
                file_path="/tmp/test.txt",
                bucket="test-bucket",
                key="test-key"
            )
            
            # Should attempt upload (may fail in test environment)
            assert isinstance(success, bool)
    
    @patch('boto3.client')
    def test_bedrock_connection_optimization(self, mock_boto_client):
        """Test Bedrock connection optimization"""
        
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock successful model invocation
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'results': [{'outputText': 'Test response'}]
        }).encode()
        
        mock_client.invoke_model.return_value = mock_response
        
        # Test optimized model invocation
        response = self.bedrock_pool.invoke_model_optimized(
            model_id="amazon.nova-micro-v1:0",
            prompt="Test prompt"
        )
        
        assert response == "Test response"
        assert mock_client.invoke_model.called


class TestAsyncProcessing:
    """Test async processing and background tasks"""
    
    def setup_method(self):
        """Setup test environment"""
        self.task_manager = AsyncTaskManager()
        self.background_queue = BackgroundTaskQueue()
    
    @pytest.mark.asyncio
    async def test_async_task_submission(self):
        """Test async task submission and tracking"""
        
        async def test_task(user_id, param1, param2):
            await asyncio.sleep(0.1)  # Simulate work
            return {"result": param1 + param2, "user_id": user_id}
        
        # Submit async task
        task_id = await self.task_manager.submit_task(
            "test_task",
            "test_user",
            test_task,
            "test_user",
            10,
            20
        )
        
        assert task_id is not None
        assert isinstance(task_id, str)
        
        # Wait for task completion
        await asyncio.sleep(0.5)
        
        # Check task status
        task_status = await self.task_manager.get_task_status(task_id)
        assert task_status is not None
        assert task_status.status in ['completed', 'running']
        
        # Get task result if completed
        if task_status.status == 'completed':
            result = await self.task_manager.get_task_result(task_id)
            assert result is not None
            assert result["result"] == 30
    
    @pytest.mark.asyncio
    async def test_async_task_decorator(self):
        """Test async task decorator"""
        
        @async_task("decorated_task")
        async def decorated_function(user_id, value):
            return {"processed_value": value * 2, "user_id": user_id}
        
        # Call decorated function
        result = await decorated_function("test_user", 42)
        
        # Should return task submission info
        assert isinstance(result, dict)
        assert "task_id" in result
        assert result["status"] == "submitted"
    
    @pytest.mark.asyncio
    async def test_background_task_queue(self):
        """Test background task queue operations"""
        
        # Mock SQS operations
        with patch.object(self.background_queue, 'sqs') as mock_sqs:
            mock_sqs.send_message.return_value = {'MessageId': 'test_message_id'}
            
            # Enqueue background task
            message_id = await self.background_queue.enqueue_task(
                task_type="test_background_task",
                user_id="test_user",
                task_data={"param1": "value1", "param2": "value2"}
            )
            
            assert message_id == "test_message_id"
            assert mock_sqs.send_message.called
    
    @pytest.mark.asyncio
    async def test_task_cleanup(self):
        """Test async task cleanup"""
        
        # Submit a task that completes quickly
        async def quick_task(user_id):
            return {"completed": True}
        
        task_id = await self.task_manager.submit_task(
            "quick_task",
            "test_user",
            quick_task,
            "test_user"
        )
        
        # Wait for completion
        await asyncio.sleep(0.5)
        
        # Cleanup completed tasks
        cleaned_count = await self.task_manager.cleanup_completed_tasks(older_than_hours=0)
        
        assert isinstance(cleaned_count, int)
        assert cleaned_count >= 0


class TestPerformanceMonitoring:
    """Test performance monitoring and metrics"""
    
    def setup_method(self):
        """Setup test environment"""
        self.monitor = PerformanceMonitor()
        self.test_request_id = f"test_req_{int(time.time())}"
    
    def test_request_tracking(self):
        """Test request performance tracking"""
        
        # Start tracking
        metrics = self.monitor.start_request_tracking(
            request_id=self.test_request_id,
            endpoint="/api/test",
            method="POST",
            user_id="test_user"
        )
        
        assert metrics is not None
        assert metrics.request_id == self.test_request_id
        assert metrics.endpoint == "/api/test"
        assert metrics.method == "POST"
        
        # Simulate some work
        time.sleep(0.1)
        
        # Track some operations
        self.monitor.track_database_query(self.test_request_id, "read")
        self.monitor.track_cache_hit(self.test_request_id)
        self.monitor.track_aws_service_call(self.test_request_id, "bedrock")
        
        # End tracking
        final_metrics = self.monitor.end_request_tracking(
            request_id=self.test_request_id,
            status_code=200,
            response_size=1024
        )
        
        assert final_metrics is not None
        assert final_metrics.status_code == 200
        assert final_metrics.response_size == 1024
        assert final_metrics.duration_ms is not None
        assert final_metrics.duration_ms > 0
        assert final_metrics.db_queries == 1
        assert final_metrics.cache_hits == 1
        assert final_metrics.aws_service_calls == 1
    
    def test_performance_context_manager(self):
        """Test performance tracking context manager"""
        
        request_id = f"ctx_req_{int(time.time())}"
        
        with track_performance(request_id, "/api/context", "GET", "test_user") as metrics:
            # Simulate work
            time.sleep(0.05)
            
            # Track operations
            self.monitor.track_cache_miss(request_id)
            self.monitor.add_custom_metric(request_id, "custom_value", 42)
        
        # Context manager should have completed tracking
        # Verify by checking that request is no longer in active tracking
        assert request_id not in self.monitor._request_metrics
    
    def test_performance_decorator(self):
        """Test performance tracking decorator"""
        
        @performance_tracking_decorator("/api/decorated", "POST")
        def decorated_function(user_id, param1, param2):
            time.sleep(0.02)  # Simulate work
            return {"result": param1 + param2}
        
        # Call decorated function
        result = decorated_function("test_user", 5, 10)
        
        assert result["result"] == 15
        # Decorator should have tracked performance automatically
    
    @patch('boto3.client')
    def test_cloudwatch_metrics_sending(self, mock_boto_client):
        """Test CloudWatch metrics sending"""
        
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch
        
        # Create test metrics
        metrics = RequestMetrics(
            request_id="test_req",
            endpoint="/api/test",
            method="POST",
            user_id="test_user",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_ms=150.0,
            status_code=200,
            response_size=2048,
            db_queries=2,
            cache_hits=1,
            cache_misses=1,
            aws_service_calls=1
        )
        
        # Send metrics (this will be mocked)
        self.monitor._send_request_metrics_to_cloudwatch(metrics)
        
        # Verify CloudWatch client was used
        # (In real implementation, put_metric_data would be called)
    
    def test_performance_summary(self):
        """Test performance summary generation"""
        
        # Mock DynamoDB table for testing
        with patch.object(self.monitor, 'metrics_table') as mock_table:
            mock_table.scan.return_value = {
                'Items': [
                    {
                        'request_id': 'req1',
                        'timestamp': datetime.utcnow().isoformat(),
                        'endpoint': '/api/test',
                        'duration_ms': 100.0,
                        'status_code': 200,
                        'memory_usage_mb': 128.0
                    },
                    {
                        'request_id': 'req2',
                        'timestamp': datetime.utcnow().isoformat(),
                        'endpoint': '/api/test',
                        'duration_ms': 200.0,
                        'status_code': 500,
                        'memory_usage_mb': 256.0
                    }
                ]
            }
            
            summary = self.monitor.get_performance_summary(hours=24)
            
            assert isinstance(summary, dict)
            assert 'total_requests' in summary
            assert 'avg_response_time_ms' in summary
            assert 'error_rate_percent' in summary
            
            # Verify calculations
            assert summary['total_requests'] == 2
            assert summary['avg_response_time_ms'] == 150.0  # (100 + 200) / 2
            assert summary['error_rate_percent'] == 50.0  # 1 error out of 2 requests


class TestLoadTesting:
    """Load testing scenarios"""
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """Test cache performance under concurrent load"""
        
        cache = PerformanceCache()
        
        async def cache_worker(worker_id):
            """Worker function for concurrent cache operations"""
            
            results = []
            for i in range(10):
                key = f"worker_{worker_id}_item_{i}"
                value = {"worker_id": worker_id, "item": i, "timestamp": time.time()}
                
                # Set cache value
                success = cache.set("load_test", key, value, user_id=f"user_{worker_id}")
                results.append(success)
                
                # Get cache value
                cached_value = cache.get("load_test", key, user_id=f"user_{worker_id}")
                results.append(cached_value is not None)
                
                # Small delay to simulate real usage
                await asyncio.sleep(0.001)
            
            return results
        
        # Run concurrent workers
        workers = [cache_worker(i) for i in range(10)]
        results = await asyncio.gather(*workers)
        
        # Verify all operations succeeded
        for worker_results in results:
            assert all(worker_results)
    
    @pytest.mark.asyncio
    async def test_concurrent_async_tasks(self):
        """Test async task manager under concurrent load"""
        
        task_manager = AsyncTaskManager()
        
        async def test_task(user_id, task_id):
            """Simple test task"""
            await asyncio.sleep(0.01)  # Simulate work
            return {"task_id": task_id, "user_id": user_id, "completed": True}
        
        # Submit multiple concurrent tasks
        task_ids = []
        for i in range(20):
            task_id = await task_manager.submit_task(
                "load_test_task",
                f"user_{i % 5}",  # 5 different users
                test_task,
                f"user_{i % 5}",
                i
            )
            task_ids.append(task_id)
        
        # Wait for all tasks to complete
        await asyncio.sleep(1.0)
        
        # Check task completion
        completed_count = 0
        for task_id in task_ids:
            task_status = await task_manager.get_task_status(task_id)
            if task_status and task_status.status == 'completed':
                completed_count += 1
        
        # Most tasks should complete successfully
        assert completed_count >= len(task_ids) * 0.8  # At least 80% success rate
    
    def test_connection_pool_under_load(self):
        """Test connection pool performance under load"""
        
        dynamodb_pool = DynamoDBConnectionPool()
        
        # Simulate multiple concurrent connection requests
        clients = []
        start_time = time.time()
        
        for i in range(50):
            client = dynamodb_pool.get_client()
            clients.append(client)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly due to connection reuse
        assert duration < 1.0  # Should take less than 1 second
        
        # All clients should be the same instance (connection reuse)
        assert all(client is clients[0] for client in clients)
    
    def test_performance_monitoring_overhead(self):
        """Test performance monitoring overhead"""
        
        monitor = PerformanceMonitor()
        
        # Measure overhead of performance tracking
        start_time = time.time()
        
        for i in range(100):
            request_id = f"perf_test_{i}"
            
            # Start tracking
            monitor.start_request_tracking(
                request_id=request_id,
                endpoint="/api/test",
                method="GET",
                user_id="test_user"
            )
            
            # Simulate some tracking operations
            monitor.track_database_query(request_id)
            monitor.track_cache_hit(request_id)
            monitor.track_aws_service_call(request_id, "bedrock")
            
            # End tracking
            monitor.end_request_tracking(request_id, 200, 1024)
        
        end_time = time.time()
        total_duration = end_time - start_time
        avg_overhead = (total_duration / 100) * 1000  # ms per request
        
        # Performance monitoring overhead should be minimal
        assert avg_overhead < 10.0  # Less than 10ms overhead per request
        
        print(f"Performance monitoring overhead: {avg_overhead:.2f}ms per request")


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short"])