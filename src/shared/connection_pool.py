"""
Connection Pooling and Database Optimization for LMS API
Provides optimized connections to AWS services with connection reuse and query optimization
"""

import boto3
import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class ConnectionPoolConfig:
    """Configuration for connection pooling"""
    
    # Connection pool settings
    MAX_POOL_CONNECTIONS = 50
    RETRIES = 3
    CONNECT_TIMEOUT = 10
    READ_TIMEOUT = 30
    
    # Connection reuse settings
    CONNECTION_TTL = 300  # 5 minutes
    MAX_IDLE_TIME = 60    # 1 minute
    
    # Query optimization settings
    BATCH_SIZE = 25
    MAX_BATCH_ITEMS = 100
    PARALLEL_REQUESTS = 10


class OptimizedAWSClient:
    """
    Optimized AWS client with connection pooling and retry logic
    """
    
    def __init__(self, service_name: str, region_name: str = None):
        """Initialize optimized AWS client"""
        
        self.service_name = service_name
        self.region_name = region_name or os.getenv('AWS_REGION', 'us-east-1')
        
        # Connection pool configuration
        self.config = Config(
            region_name=self.region_name,
            retries={
                'max_attempts': ConnectionPoolConfig.RETRIES,
                'mode': 'adaptive'
            },
            max_pool_connections=ConnectionPoolConfig.MAX_POOL_CONNECTIONS,
            connect_timeout=ConnectionPoolConfig.CONNECT_TIMEOUT,
            read_timeout=ConnectionPoolConfig.READ_TIMEOUT
        )
        
        # Client cache with TTL
        self._clients = {}
        self._client_created_at = {}
        self._lock = threading.Lock()
        
        logger.info(f"Initialized optimized AWS client for {service_name}")
    
    def get_client(self):
        """Get or create optimized AWS client with connection reuse"""
        
        current_time = time.time()
        
        with self._lock:
            # Check if we have a valid cached client
            if (self.service_name in self._clients and 
                self.service_name in self._client_created_at):
                
                created_at = self._client_created_at[self.service_name]
                age = current_time - created_at
                
                # Reuse client if within TTL
                if age < ConnectionPoolConfig.CONNECTION_TTL:
                    return self._clients[self.service_name]
                else:
                    # Client expired, remove from cache
                    del self._clients[self.service_name]
                    del self._client_created_at[self.service_name]
            
            # Create new client
            try:
                client = boto3.client(self.service_name, config=self.config)
                self._clients[self.service_name] = client
                self._client_created_at[self.service_name] = current_time
                
                logger.debug(f"Created new AWS client for {self.service_name}")
                return client
                
            except Exception as e:
                logger.error(f"Error creating AWS client for {self.service_name}: {e}")
                raise
    
    def cleanup_expired_clients(self):
        """Clean up expired clients from cache"""
        
        current_time = time.time()
        expired_services = []
        
        with self._lock:
            for service, created_at in self._client_created_at.items():
                age = current_time - created_at
                if age > ConnectionPoolConfig.CONNECTION_TTL:
                    expired_services.append(service)
            
            for service in expired_services:
                if service in self._clients:
                    del self._clients[service]
                del self._client_created_at[service]
        
        if expired_services:
            logger.debug(f"Cleaned up {len(expired_services)} expired AWS clients")


class DynamoDBConnectionPool:
    """
    Optimized DynamoDB connection pool with query optimization
    """
    
    def __init__(self):
        """Initialize DynamoDB connection pool"""
        
        self.aws_client = OptimizedAWSClient('dynamodb')
        self.resource_client = OptimizedAWSClient('dynamodb')
        
        # Query optimization settings
        self.batch_size = ConnectionPoolConfig.BATCH_SIZE
        self.max_batch_items = ConnectionPoolConfig.MAX_BATCH_ITEMS
        
        # Connection statistics
        self.stats = {
            'queries_executed': 0,
            'batch_operations': 0,
            'cache_hits': 0,
            'connection_reuses': 0
        }
        
        logger.info("DynamoDB connection pool initialized")
    
    def get_client(self):
        """Get DynamoDB client"""
        return self.aws_client.get_client()
    
    def get_resource(self):
        """Get DynamoDB resource"""
        client = self.resource_client.get_client()
        return boto3.resource('dynamodb', region_name=client.meta.region_name)
    
    def get_table(self, table_name: str):
        """Get DynamoDB table with connection reuse"""
        
        resource = self.get_resource()
        table = resource.Table(table_name)
        
        # Verify table exists (cached check)
        try:
            table.load()
            return table
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.error(f"DynamoDB table not found: {table_name}")
                raise
            else:
                logger.error(f"Error accessing DynamoDB table {table_name}: {e}")
                raise
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        
        return {
            'queries_executed': self.stats['queries_executed'],
            'batch_operations': self.stats['batch_operations'],
            'cache_hits': self.stats['cache_hits'],
            'connection_reuses': self.stats['connection_reuses'],
            'active_connections': len(self.aws_client._clients)
        }


class S3ConnectionPool:
    """
    Optimized S3 connection pool with transfer optimization
    """
    
    def __init__(self):
        """Initialize S3 connection pool"""
        
        self.aws_client = OptimizedAWSClient('s3')
        
        logger.info("S3 connection pool initialized")
    
    def get_client(self):
        """Get S3 client"""
        return self.aws_client.get_client()


class BedrockConnectionPool:
    """
    Optimized Bedrock connection pool for AI model inference
    """
    
    def __init__(self):
        """Initialize Bedrock connection pool"""
        
        self.runtime_client = OptimizedAWSClient('bedrock-runtime')
        self.agent_client = OptimizedAWSClient('bedrock-agent-runtime')
        
        logger.info("Bedrock connection pool initialized")
    
    def get_runtime_client(self):
        """Get Bedrock runtime client"""
        return self.runtime_client.get_client()
    
    def get_agent_client(self):
        """Get Bedrock agent runtime client"""
        return self.agent_client.get_client()


# Global connection pool instances
dynamodb_pool = DynamoDBConnectionPool()
s3_pool = S3ConnectionPool()
bedrock_pool = BedrockConnectionPool()


# Global connection pool instances
dynamodb_pool = DynamoDBConnectionPool()
s3_pool = S3ConnectionPool()
bedrock_pool = BedrockConnectionPool()


def get_optimized_dynamodb_table(table_name: str):
    """Get optimized DynamoDB table"""
    return dynamodb_pool.get_table(table_name)


def get_optimized_s3_client():
    """Get optimized S3 client"""
    return s3_pool.get_client()


def get_optimized_bedrock_client():
    """Get optimized Bedrock runtime client"""
    return bedrock_pool.get_runtime_client()


def get_optimized_bedrock_agent_client():
    """Get optimized Bedrock agent client"""
    return bedrock_pool.get_agent_client()


def cleanup_connection_pools():
    """Clean up all connection pools"""
    
    try:
        dynamodb_pool.aws_client.cleanup_expired_clients()
        s3_pool.aws_client.cleanup_expired_clients()
        bedrock_pool.runtime_client.cleanup_expired_clients()
        bedrock_pool.agent_client.cleanup_expired_clients()
        
        logger.info("Connection pools cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Error cleaning up connection pools: {e}")


# Connection pool decorator
def use_connection_pool(service_type: str):
    """
    Decorator to use optimized connection pools
    
    Args:
        service_type: Type of service ('dynamodb', 's3', 'bedrock')
    """
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Inject optimized client based on service type
            if service_type == 'dynamodb':
                kwargs['dynamodb_pool'] = dynamodb_pool
            elif service_type == 's3':
                kwargs['s3_client'] = get_optimized_s3_client()
            elif service_type == 'bedrock':
                kwargs['bedrock_client'] = get_optimized_bedrock_client()
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator