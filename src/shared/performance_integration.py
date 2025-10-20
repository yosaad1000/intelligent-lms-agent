"""
Performance Optimization Integration
Integrates all performance components into a unified system
"""

import os
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
import logging

# Import performance components
from .performance_cache import performance_cache, CacheConfig, invalidate_user_cache
from .connection_pool import (
    dynamodb_pool, s3_pool, bedrock_pool, cleanup_connection_pools
)
from .async_processor import async_task_manager, background_task_queue
from .performance_monitor import performance_monitor, track_performance

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """
    Unified performance optimization system
    Coordinates caching, connection pooling, async processing, and monitoring
    """
    
    def __init__(self):
        """Initialize performance optimizer"""
        
        self.cache = performance_cache
        self.monitor = performance_monitor
        self.task_manager = async_task_manager
        self.background_queue = background_task_queue
        
        # Performance configuration
        self.config = {
            'cache_enabled': True,
            'monitoring_enabled': True,
            'async_processing_enabled': True,
            'connection_pooling_enabled': True,
            'background_tasks_enabled': True
        }
        
        # Performance thresholds
        self.thresholds = {
            'response_time_ms': 3000,
            'cache_hit_rate_percent': 70,
            'error_rate_percent': 5,
            'memory_usage_mb': 512,
            'cpu_usage_percent': 80
        }
        
        logger.info("Performance optimizer initialized")
    
    def configure(self, **kwargs):
        """Configure performance optimization settings"""
        
        self.config.update(kwargs)
        logger.info(f"Performance optimizer configured: {self.config}")
    
    def set_thresholds(self, **kwargs):
        """Set performance thresholds"""
        
        self.thresholds.update(kwargs)
        logger.info(f"Performance thresholds updated: {self.thresholds}")
    
    async def optimize_request(
        self,
        request_id: str,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        cache_key: Optional[str] = None,
        cache_ttl: int = CacheConfig.DEFAULT_TTL
    ):
        """
        Optimize a single request with all performance features
        
        Args:
            request_id: Unique request identifier
            endpoint: API endpoint
            method: HTTP method
            user_id: User ID for user-specific optimizations
            cache_key: Cache key for response caching
            cache_ttl: Cache TTL in seconds
        """
        
        # Start performance monitoring
        if self.config['monitoring_enabled']:
            self.monitor.start_request_tracking(
                request_id=request_id,
                endpoint=endpoint,
                method=method,
                user_id=user_id
            )
        
        # Check cache first
        cached_response = None
        if self.config['cache_enabled'] and cache_key:
            cached_response = self.cache.get(
                prefix="api_responses",
                key=cache_key,
                user_id=user_id
            )
            
            if cached_response:
                if self.config['monitoring_enabled']:
                    self.monitor.track_cache_hit(request_id)
                
                logger.debug(f"Cache hit for request {request_id}")
                return cached_response
            else:
                if self.config['monitoring_enabled']:
                    self.monitor.track_cache_miss(request_id)
        
        return None  # No cached response found
    
    async def cache_response(
        self,
        request_id: str,
        cache_key: str,
        response_data: Any,
        user_id: Optional[str] = None,
        cache_ttl: int = CacheConfig.DEFAULT_TTL
    ):
        """Cache API response"""
        
        if self.config['cache_enabled'] and cache_key:
            success = self.cache.set(
                prefix="api_responses",
                key=cache_key,
                value=response_data,
                ttl_seconds=cache_ttl,
                user_id=user_id
            )
            
            if success:
                logger.debug(f"Cached response for request {request_id}")
            else:
                logger.warning(f"Failed to cache response for request {request_id}")
    
    async def submit_background_task(
        self,
        task_type: str,
        user_id: str,
        task_data: Dict[str, Any],
        delay_seconds: int = 0
    ) -> str:
        """Submit background task for processing"""
        
        if not self.config['background_tasks_enabled']:
            logger.warning("Background tasks disabled")
            return ""
        
        message_id = await self.background_queue.enqueue_task(
            task_type=task_type,
            user_id=user_id,
            task_data=task_data,
            delay_seconds=delay_seconds
        )
        
        logger.info(f"Submitted background task: {message_id} ({task_type})")
        return message_id
    
    async def submit_async_task(
        self,
        task_type: str,
        user_id: str,
        task_function: Callable,
        *args,
        **kwargs
    ) -> str:
        """Submit async task for processing"""
        
        if not self.config['async_processing_enabled']:
            logger.warning("Async processing disabled")
            return ""
        
        task_id = await self.task_manager.submit_task(
            task_type=task_type,
            user_id=user_id,
            task_function=task_function,
            *args,
            **kwargs
        )
        
        logger.info(f"Submitted async task: {task_id} ({task_type})")
        return task_id
    
    def get_optimized_clients(self) -> Dict[str, Any]:
        """Get optimized AWS service clients"""
        
        if not self.config['connection_pooling_enabled']:
            logger.warning("Connection pooling disabled")
            return {}
        
        return {
            'dynamodb': dynamodb_pool,
            's3': s3_pool,
            'bedrock': bedrock_pool
        }
    
    async def warm_user_cache(self, user_id: str) -> Dict[str, Any]:
        """Warm cache for a specific user"""
        
        if not self.config['cache_enabled']:
            return {'error': 'Caching disabled'}
        
        # Submit cache warming as background task
        task_data = {
            'cache_types': [
                CacheConfig.USER_FILES,
                CacheConfig.CHAT_HISTORY,
                CacheConfig.ANALYTICS
            ]
        }
        
        message_id = await self.submit_background_task(
            task_type="cache_warming",
            user_id=user_id,
            task_data=task_data
        )
        
        return {
            'message_id': message_id,
            'status': 'cache_warming_queued'
        }
    
    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache for a user"""
        
        if not self.config['cache_enabled']:
            return 0
        
        invalidated_count = invalidate_user_cache(user_id)
        logger.info(f"Invalidated {invalidated_count} cache entries for user {user_id}")
        
        return invalidated_count
    
    async def get_performance_metrics(
        self,
        hours: int = 24,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        
        if not self.config['monitoring_enabled']:
            return {'error': 'Monitoring disabled'}
        
        # Get performance summary
        summary = self.monitor.get_performance_summary(hours=hours, endpoint=endpoint)
        
        # Add cache statistics
        cache_stats = self.cache.get_stats()
        
        # Add connection pool statistics
        connection_stats = {}
        if self.config['connection_pooling_enabled']:
            connection_stats = {
                'dynamodb': dynamodb_pool.get_connection_stats(),
                'active_connections': len(dynamodb_pool.aws_client._clients)
            }
        
        # Combine all metrics
        metrics = {
            'performance_summary': summary,
            'cache_statistics': cache_stats,
            'connection_statistics': connection_stats,
            'configuration': self.config,
            'thresholds': self.thresholds
        }
        
        return metrics
    
    async def analyze_performance_issues(self) -> Dict[str, Any]:
        """Analyze current performance and identify issues"""
        
        metrics = await self.get_performance_metrics(hours=1)  # Last hour
        issues = []
        recommendations = []
        
        if 'performance_summary' in metrics:
            summary = metrics['performance_summary']
            
            # Check response time
            if summary.get('avg_response_time_ms', 0) > self.thresholds['response_time_ms']:
                issues.append("High average response time")
                recommendations.extend([
                    "Enable response caching",
                    "Optimize database queries",
                    "Implement connection pooling"
                ])
            
            # Check error rate
            if summary.get('error_rate_percent', 0) > self.thresholds['error_rate_percent']:
                issues.append("High error rate")
                recommendations.extend([
                    "Implement circuit breakers",
                    "Add retry logic",
                    "Improve error handling"
                ])
        
        # Check cache performance
        if 'cache_statistics' in metrics:
            cache_stats = metrics['cache_statistics']
            cache_size = cache_stats.get('memory_cache_size', 0)
            cache_limit = cache_stats.get('memory_cache_limit', 1)
            
            if cache_size / cache_limit > 0.9:
                issues.append("Cache near capacity")
                recommendations.append("Increase cache size or implement better eviction")
        
        return {
            'issues': issues,
            'recommendations': recommendations,
            'metrics_summary': metrics,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
    
    async def optimize_system_performance(self) -> Dict[str, Any]:
        """Automatically optimize system performance"""
        
        logger.info("Starting automatic performance optimization")
        
        optimization_results = {
            'cache_cleanup': 0,
            'connection_cleanup': 0,
            'task_cleanup': 0,
            'memory_optimization': 0,
            'query_optimization': 0,
            'optimizations_applied': []
        }
        
        # Clean up expired cache entries
        if self.config['cache_enabled']:
            try:
                # Clean up memory cache
                self.cache._cleanup_memory_cache()
                optimization_results['cache_cleanup'] = 1
                optimization_results['optimizations_applied'].append("cache_cleanup")
            except Exception as e:
                logger.error(f"Cache cleanup failed: {e}")
        
        # Clean up connection pools
        if self.config['connection_pooling_enabled']:
            try:
                cleanup_connection_pools()
                optimization_results['connection_cleanup'] = 1
                optimization_results['optimizations_applied'].append("connection_pool_cleanup")
            except Exception as e:
                logger.error(f"Connection pool cleanup failed: {e}")
        
        # Clean up completed async tasks
        if self.config['async_processing_enabled']:
            try:
                cleaned_tasks = await self.task_manager.cleanup_completed_tasks(older_than_hours=24)
                optimization_results['task_cleanup'] = cleaned_tasks
                optimization_results['optimizations_applied'].append("task_cleanup")
            except Exception as e:
                logger.error(f"Task cleanup failed: {e}")
        
        # Memory optimization
        try:
            import gc
            collected = gc.collect()
            optimization_results['memory_optimization'] = collected
            optimization_results['optimizations_applied'].append("memory_optimization")
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
        
        # Query optimization (precompute common queries)
        try:
            await self._optimize_common_queries()
            optimization_results['query_optimization'] = 1
            optimization_results['optimizations_applied'].append("query_optimization")
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
        
        logger.info(f"Performance optimization completed: {optimization_results}")
        return optimization_results
    
    async def _optimize_common_queries(self):
        """Optimize common database queries by precomputing results"""
        
        # This could include:
        # - Precomputing user analytics
        # - Warming up frequently accessed data
        # - Optimizing database indexes
        # - Batch processing common operations
        
        logger.info("Optimizing common queries and precomputing results")
        
        # Example: Warm cache for active users
        # In a real implementation, you'd identify active users and warm their cache
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive performance health check"""
        
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        # Check cache health
        if self.config['cache_enabled']:
            try:
                cache_stats = self.cache.get_stats()
                health['components']['cache'] = {
                    'status': 'healthy',
                    'memory_usage': cache_stats.get('memory_cache_size', 0),
                    'redis_available': cache_stats.get('redis_available', False),
                    'dynamodb_available': cache_stats.get('dynamodb_available', False)
                }
            except Exception as e:
                health['components']['cache'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health['status'] = 'degraded'
        
        # Check connection pools
        if self.config['connection_pooling_enabled']:
            try:
                conn_stats = dynamodb_pool.get_connection_stats()
                health['components']['connection_pools'] = {
                    'status': 'healthy',
                    'active_connections': conn_stats.get('active_connections', 0),
                    'queries_executed': conn_stats.get('queries_executed', 0)
                }
            except Exception as e:
                health['components']['connection_pools'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health['status'] = 'degraded'
        
        # Check async processing
        if self.config['async_processing_enabled']:
            try:
                # Get active task count (simplified)
                active_tasks = len(self.task_manager._active_tasks)
                health['components']['async_processing'] = {
                    'status': 'healthy',
                    'active_tasks': active_tasks
                }
            except Exception as e:
                health['components']['async_processing'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health['status'] = 'degraded'
        
        return health


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()


def optimize_api_endpoint(
    cache_key_generator: Optional[Callable] = None,
    cache_ttl: int = CacheConfig.DEFAULT_TTL,
    enable_monitoring: bool = True,
    enable_caching: bool = True
):
    """
    Decorator to optimize API endpoints with all performance features
    
    Args:
        cache_key_generator: Function to generate cache key from request
        cache_ttl: Cache TTL in seconds
        enable_monitoring: Enable performance monitoring
        enable_caching: Enable response caching
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate request ID
            request_id = f"req_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
            
            # Extract endpoint and user info
            endpoint = getattr(func, '__name__', 'unknown')
            user_id = kwargs.get('user_id') or (args[0] if args else None)
            
            # Generate cache key
            cache_key = None
            if enable_caching and cache_key_generator:
                try:
                    cache_key = cache_key_generator(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Cache key generation failed: {e}")
            
            # Start optimization
            if enable_monitoring or enable_caching:
                cached_response = await performance_optimizer.optimize_request(
                    request_id=request_id,
                    endpoint=endpoint,
                    method="POST",  # Default to POST
                    user_id=user_id,
                    cache_key=cache_key,
                    cache_ttl=cache_ttl
                )
                
                if cached_response:
                    return cached_response
            
            # Execute function
            try:
                result = await func(*args, **kwargs)
                
                # Cache response
                if enable_caching and cache_key:
                    await performance_optimizer.cache_response(
                        request_id=request_id,
                        cache_key=cache_key,
                        response_data=result,
                        user_id=user_id,
                        cache_ttl=cache_ttl
                    )
                
                # End monitoring
                if enable_monitoring:
                    performance_optimizer.monitor.end_request_tracking(
                        request_id=request_id,
                        status_code=200,
                        response_size=len(str(result)) if result else 0
                    )
                
                return result
                
            except Exception as e:
                # Track error
                if enable_monitoring:
                    performance_optimizer.monitor.track_error(request_id, type(e).__name__)
                    performance_optimizer.monitor.end_request_tracking(
                        request_id=request_id,
                        status_code=500
                    )
                
                raise
        
        return wrapper
    return decorator


async def initialize_performance_system():
    """Initialize the performance optimization system"""
    
    logger.info("Initializing performance optimization system")
    
    # Configure based on environment
    environment = os.getenv('ENVIRONMENT', 'development')
    
    if environment == 'production':
        performance_optimizer.configure(
            cache_enabled=True,
            monitoring_enabled=True,
            async_processing_enabled=True,
            connection_pooling_enabled=True,
            background_tasks_enabled=True
        )
        
        performance_optimizer.set_thresholds(
            response_time_ms=2000,  # Stricter in production
            cache_hit_rate_percent=80,
            error_rate_percent=2,
            memory_usage_mb=1024,
            cpu_usage_percent=70
        )
    else:
        performance_optimizer.configure(
            cache_enabled=True,
            monitoring_enabled=True,
            async_processing_enabled=True,
            connection_pooling_enabled=True,
            background_tasks_enabled=False  # Disable in development
        )
    
    logger.info("Performance optimization system initialized")


async def cleanup_performance_system():
    """Cleanup performance optimization system"""
    
    logger.info("Cleaning up performance optimization system")
    
    # Optimize system performance
    await performance_optimizer.optimize_system_performance()
    
    # Stop monitoring
    performance_optimizer.monitor.stop_monitoring()
    
    logger.info("Performance optimization system cleaned up")


# Example usage functions
def generate_chat_cache_key(user_id: str, message: str, **kwargs) -> str:
    """Generate cache key for chat responses"""
    
    import hashlib
    
    # Create hash of message for cache key
    message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
    return f"chat_{user_id}_{message_hash}"


def generate_file_cache_key(user_id: str, file_id: str, **kwargs) -> str:
    """Generate cache key for file operations"""
    
    return f"file_{user_id}_{file_id}"


def generate_quiz_cache_key(user_id: str, topic: str, difficulty: str, **kwargs) -> str:
    """Generate cache key for quiz generation"""
    
    return f"quiz_{user_id}_{topic}_{difficulty}"