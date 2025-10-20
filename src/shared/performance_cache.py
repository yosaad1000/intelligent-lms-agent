"""
Performance Caching System for LMS API
Provides Redis-compatible caching with DynamoDB fallback for Lambda environments
"""

import json
import boto3
import os
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, List
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration settings"""
    
    # Cache TTL settings (in seconds)
    DEFAULT_TTL = 300  # 5 minutes
    SHORT_TTL = 60     # 1 minute
    MEDIUM_TTL = 900   # 15 minutes
    LONG_TTL = 3600    # 1 hour
    VERY_LONG_TTL = 86400  # 24 hours
    
    # Cache key prefixes
    USER_FILES = "user_files"
    CHAT_HISTORY = "chat_history"
    QUIZ_RESULTS = "quiz_results"
    ANALYTICS = "analytics"
    BEDROCK_RESPONSES = "bedrock_responses"
    VECTOR_SEARCH = "vector_search"
    TRANSLATION = "translation"
    DOCUMENT_PROCESSING = "doc_processing"
    
    # Cache size limits
    MAX_VALUE_SIZE = 400 * 1024  # 400KB (DynamoDB limit)
    MAX_CACHE_ENTRIES = 10000


class PerformanceCache:
    """
    High-performance caching system with multiple backends
    Supports in-memory, DynamoDB, and optional Redis caching
    """
    
    def __init__(self):
        """Initialize cache with available backends"""
        
        # In-memory cache (Lambda container reuse)
        self._memory_cache = {}
        self._memory_cache_ttl = {}
        
        # DynamoDB cache table
        self.dynamodb = boto3.resource('dynamodb')
        self.cache_table_name = os.getenv('CACHE_TABLE_NAME', 'lms-performance-cache')
        
        try:
            self.cache_table = self.dynamodb.Table(self.cache_table_name)
        except Exception as e:
            logger.warning(f"Cache table not available: {e}")
            self.cache_table = None
        
        # Redis cache (optional for production)
        self.redis_client = None
        redis_endpoint = os.getenv('REDIS_ENDPOINT')
        if redis_endpoint:
            try:
                import redis
                self.redis_client = redis.Redis.from_url(redis_endpoint)
                logger.info("Redis cache initialized")
            except ImportError:
                logger.warning("Redis not available - install with: pip install redis")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")
    
    def _generate_cache_key(self, prefix: str, key: str, user_id: str = None) -> str:
        """Generate standardized cache key"""
        
        if user_id:
            cache_key = f"{prefix}:{user_id}:{key}"
        else:
            cache_key = f"{prefix}:{key}"
        
        # Hash long keys to avoid DynamoDB key length limits
        if len(cache_key) > 255:
            cache_key = f"{prefix}:{hashlib.md5(cache_key.encode()).hexdigest()}"
        
        return cache_key
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage"""
        
        def decimal_serializer(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return json.dumps(value, default=decimal_serializer, separators=(',', ':'))
    
    def _deserialize_value(self, value: str) -> Any:
        """Deserialize value from storage"""
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    def _is_expired(self, ttl_timestamp: float) -> bool:
        """Check if cache entry is expired"""
        return time.time() > ttl_timestamp
    
    def get(self, prefix: str, key: str, user_id: str = None) -> Optional[Any]:
        """
        Get value from cache with multi-tier lookup
        
        Args:
            prefix: Cache key prefix
            key: Cache key
            user_id: User ID for user-specific caching
            
        Returns:
            Cached value or None if not found/expired
        """
        
        cache_key = self._generate_cache_key(prefix, key, user_id)
        
        # 1. Check in-memory cache first (fastest)
        if cache_key in self._memory_cache:
            ttl = self._memory_cache_ttl.get(cache_key, 0)
            if not self._is_expired(ttl):
                logger.debug(f"Cache HIT (memory): {cache_key}")
                return self._memory_cache[cache_key]
            else:
                # Remove expired entry
                del self._memory_cache[cache_key]
                del self._memory_cache_ttl[cache_key]
        
        # 2. Check Redis cache (if available)
        if self.redis_client:
            try:
                cached_value = self.redis_client.get(cache_key)
                if cached_value:
                    value = self._deserialize_value(cached_value.decode('utf-8'))
                    # Store in memory cache for faster subsequent access
                    self._memory_cache[cache_key] = value
                    self._memory_cache_ttl[cache_key] = time.time() + CacheConfig.SHORT_TTL
                    logger.debug(f"Cache HIT (Redis): {cache_key}")
                    return value
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # 3. Check DynamoDB cache (persistent)
        if self.cache_table:
            try:
                response = self.cache_table.get_item(Key={'cache_key': cache_key})
                if 'Item' in response:
                    item = response['Item']
                    ttl = float(item.get('ttl', 0))
                    
                    if not self._is_expired(ttl):
                        value = self._deserialize_value(item['value'])
                        # Store in higher-tier caches
                        self._memory_cache[cache_key] = value
                        self._memory_cache_ttl[cache_key] = ttl
                        logger.debug(f"Cache HIT (DynamoDB): {cache_key}")
                        return value
                    else:
                        # Remove expired entry
                        self.cache_table.delete_item(Key={'cache_key': cache_key})
            except Exception as e:
                logger.warning(f"DynamoDB cache error: {e}")
        
        logger.debug(f"Cache MISS: {cache_key}")
        return None
    
    def set(
        self, 
        prefix: str, 
        key: str, 
        value: Any, 
        ttl_seconds: int = CacheConfig.DEFAULT_TTL,
        user_id: str = None
    ) -> bool:
        """
        Set value in cache with multi-tier storage
        
        Args:
            prefix: Cache key prefix
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
            user_id: User ID for user-specific caching
            
        Returns:
            True if successfully cached
        """
        
        cache_key = self._generate_cache_key(prefix, key, user_id)
        serialized_value = self._serialize_value(value)
        
        # Check size limit
        if len(serialized_value) > CacheConfig.MAX_VALUE_SIZE:
            logger.warning(f"Cache value too large: {len(serialized_value)} bytes")
            return False
        
        ttl_timestamp = time.time() + ttl_seconds
        success = False
        
        # 1. Store in memory cache
        try:
            self._memory_cache[cache_key] = value
            self._memory_cache_ttl[cache_key] = ttl_timestamp
            success = True
            
            # Cleanup memory cache if too large
            if len(self._memory_cache) > CacheConfig.MAX_CACHE_ENTRIES:
                self._cleanup_memory_cache()
                
        except Exception as e:
            logger.warning(f"Memory cache error: {e}")
        
        # 2. Store in Redis cache (if available)
        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, ttl_seconds, serialized_value)
                success = True
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # 3. Store in DynamoDB cache
        if self.cache_table:
            try:
                self.cache_table.put_item(
                    Item={
                        'cache_key': cache_key,
                        'value': serialized_value,
                        'ttl': int(ttl_timestamp),
                        'created_at': datetime.utcnow().isoformat()
                    }
                )
                success = True
            except Exception as e:
                logger.warning(f"DynamoDB cache error: {e}")
        
        if success:
            logger.debug(f"Cache SET: {cache_key} (TTL: {ttl_seconds}s)")
        
        return success
    
    def delete(self, prefix: str, key: str, user_id: str = None) -> bool:
        """
        Delete value from all cache tiers
        
        Args:
            prefix: Cache key prefix
            key: Cache key
            user_id: User ID for user-specific caching
            
        Returns:
            True if successfully deleted from at least one tier
        """
        
        cache_key = self._generate_cache_key(prefix, key, user_id)
        success = False
        
        # Delete from memory cache
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
            del self._memory_cache_ttl[cache_key]
            success = True
        
        # Delete from Redis cache
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
                success = True
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        # Delete from DynamoDB cache
        if self.cache_table:
            try:
                self.cache_table.delete_item(Key={'cache_key': cache_key})
                success = True
            except Exception as e:
                logger.warning(f"DynamoDB delete error: {e}")
        
        if success:
            logger.debug(f"Cache DELETE: {cache_key}")
        
        return success
    
    def invalidate_pattern(self, prefix: str, user_id: str = None) -> int:
        """
        Invalidate all cache entries matching a pattern
        
        Args:
            prefix: Cache key prefix to match
            user_id: User ID for user-specific invalidation
            
        Returns:
            Number of entries invalidated
        """
        
        pattern = self._generate_cache_key(prefix, "", user_id).rstrip(":")
        invalidated = 0
        
        # Invalidate memory cache
        keys_to_delete = [k for k in self._memory_cache.keys() if k.startswith(pattern)]
        for key in keys_to_delete:
            del self._memory_cache[key]
            if key in self._memory_cache_ttl:
                del self._memory_cache_ttl[key]
            invalidated += 1
        
        # Invalidate Redis cache (if available)
        if self.redis_client:
            try:
                keys = self.redis_client.keys(f"{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
                    invalidated += len(keys)
            except Exception as e:
                logger.warning(f"Redis pattern delete error: {e}")
        
        # Note: DynamoDB doesn't support pattern deletion efficiently
        # We rely on TTL for cleanup
        
        logger.info(f"Cache invalidated {invalidated} entries for pattern: {pattern}")
        return invalidated
    
    def _cleanup_memory_cache(self) -> None:
        """Clean up expired entries from memory cache"""
        
        current_time = time.time()
        expired_keys = [
            key for key, ttl in self._memory_cache_ttl.items()
            if current_time > ttl
        ]
        
        for key in expired_keys:
            del self._memory_cache[key]
            del self._memory_cache_ttl[key]
        
        # If still too large, remove oldest entries
        if len(self._memory_cache) > CacheConfig.MAX_CACHE_ENTRIES:
            # Sort by TTL and remove oldest
            sorted_keys = sorted(
                self._memory_cache_ttl.items(),
                key=lambda x: x[1]
            )
            
            keys_to_remove = sorted_keys[:len(self._memory_cache) - CacheConfig.MAX_CACHE_ENTRIES + 100]
            for key, _ in keys_to_remove:
                if key in self._memory_cache:
                    del self._memory_cache[key]
                del self._memory_cache_ttl[key]
        
        logger.debug(f"Memory cache cleanup: {len(expired_keys)} expired, {len(self._memory_cache)} remaining")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        
        stats = {
            'memory_cache_size': len(self._memory_cache),
            'memory_cache_limit': CacheConfig.MAX_CACHE_ENTRIES,
            'redis_available': self.redis_client is not None,
            'dynamodb_available': self.cache_table is not None
        }
        
        # Redis stats
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_memory_usage'] = info.get('used_memory_human', 'unknown')
                stats['redis_connected_clients'] = info.get('connected_clients', 0)
            except Exception as e:
                stats['redis_error'] = str(e)
        
        return stats


# Global cache instance
performance_cache = PerformanceCache()


def cache_decorator(
    prefix: str,
    ttl_seconds: int = CacheConfig.DEFAULT_TTL,
    user_specific: bool = True,
    key_generator: callable = None
):
    """
    Decorator for caching function results
    
    Args:
        prefix: Cache key prefix
        ttl_seconds: Time to live in seconds
        user_specific: Whether to include user_id in cache key
        key_generator: Custom function to generate cache key from args
    """
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Default key generation from function name and args
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args[:3]])  # Limit to first 3 args
                cache_key = "_".join(key_parts)
            
            # Extract user_id if user_specific
            user_id = None
            if user_specific:
                # Try to find user_id in args or kwargs
                if args and isinstance(args[0], str):
                    user_id = args[0]
                elif 'user_id' in kwargs:
                    user_id = kwargs['user_id']
            
            # Try to get from cache
            cached_result = performance_cache.get(prefix, cache_key, user_id)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            performance_cache.set(prefix, cache_key, result, ttl_seconds, user_id)
            
            return result
        
        return wrapper
    return decorator


def invalidate_user_cache(user_id: str, prefixes: List[str] = None) -> int:
    """
    Invalidate all cache entries for a specific user
    
    Args:
        user_id: User ID
        prefixes: Specific prefixes to invalidate (all if None)
        
    Returns:
        Number of entries invalidated
    """
    
    if prefixes is None:
        prefixes = [
            CacheConfig.USER_FILES,
            CacheConfig.CHAT_HISTORY,
            CacheConfig.QUIZ_RESULTS,
            CacheConfig.ANALYTICS
        ]
    
    total_invalidated = 0
    for prefix in prefixes:
        total_invalidated += performance_cache.invalidate_pattern(prefix, user_id)
    
    return total_invalidated


def warm_cache_for_user(user_id: str) -> Dict[str, Any]:
    """
    Pre-warm cache with commonly accessed user data
    
    Args:
        user_id: User ID
        
    Returns:
        Cache warming results
    """
    
    results = {
        'user_id': user_id,
        'warmed_entries': 0,
        'errors': []
    }
    
    try:
        # This would be implemented to pre-load common data
        # For now, just return placeholder
        logger.info(f"Cache warming initiated for user: {user_id}")
        results['warmed_entries'] = 0
        
    except Exception as e:
        results['errors'].append(str(e))
        logger.error(f"Cache warming error for user {user_id}: {e}")
    
    return results