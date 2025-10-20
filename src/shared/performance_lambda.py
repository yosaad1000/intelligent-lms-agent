"""
Performance Optimization Lambda Handler
Provides performance optimization endpoints and background processing
"""

import json
import os
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Import performance components
from .performance_integration import (
    performance_optimizer, initialize_performance_system, cleanup_performance_system
)
from .performance_cache import performance_cache, CacheConfig
from .connection_pool import cleanup_connection_pools
from .async_processor import async_task_manager, background_task_queue
from .performance_monitor import performance_monitor

import logging
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    """
    Lambda handler for performance optimization endpoints
    """
    
    try:
        # Initialize performance system
        asyncio.run(initialize_performance_system())
        
        # Parse request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        query_params = event.get('queryStringParameters') or {}
        body = event.get('body')
        
        # Parse body if present
        request_data = {}
        if body:
            try:
                request_data = json.loads(body)
            except json.JSONDecodeError:
                pass
        
        # Extract user info from context (if available)
        user_id = None
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        if authorizer:
            user_id = authorizer.get('user_id')
        
        # Route to appropriate handler
        if path.endswith('/performance/health'):
            return asyncio.run(handle_performance_health(query_params))
        
        elif path.endswith('/performance/metrics'):
            return asyncio.run(handle_performance_metrics(query_params))
        
        elif path.endswith('/performance/cache'):
            if http_method == 'GET':
                return asyncio.run(handle_cache_stats(query_params))
            elif http_method == 'POST':
                return asyncio.run(handle_cache_operation(request_data, user_id))
            elif http_method == 'DELETE':
                return asyncio.run(handle_cache_invalidation(request_data, user_id))
        
        elif path.endswith('/performance/tasks'):
            if http_method == 'GET':
                return asyncio.run(handle_task_status(query_params, user_id))
            elif http_method == 'POST':
                return asyncio.run(handle_task_submission(request_data, user_id))
        
        elif path.endswith('/performance/optimize'):
            return asyncio.run(handle_system_optimization(request_data))
        
        elif path.endswith('/performance/analyze'):
            return asyncio.run(handle_performance_analysis(query_params))
        
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Performance endpoint not found',
                    'available_endpoints': [
                        '/performance/health',
                        '/performance/metrics',
                        '/performance/cache',
                        '/performance/tasks',
                        '/performance/optimize',
                        '/performance/analyze'
                    ]
                })
            }
    
    except Exception as e:
        logger.error(f"Performance Lambda error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
    
    finally:
        # Cleanup
        try:
            asyncio.run(cleanup_performance_system())
        except:
            pass


async def handle_performance_health(query_params: Dict[str, str]) -> Dict[str, Any]:
    """Handle performance health check"""
    
    try:
        health_check = await performance_optimizer.health_check()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'health': health_check,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Health check failed',
                'message': str(e)
            })
        }


async def handle_performance_metrics(query_params: Dict[str, str]) -> Dict[str, Any]:
    """Handle performance metrics retrieval"""
    
    try:
        hours = int(query_params.get('hours', '24'))
        endpoint = query_params.get('endpoint')
        
        metrics = await performance_optimizer.get_performance_metrics(
            hours=hours,
            endpoint=endpoint
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'metrics': metrics,
                'query_params': {
                    'hours': hours,
                    'endpoint': endpoint
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    
    except Exception as e:
        logger.error(f"Metrics retrieval error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Metrics retrieval failed',
                'message': str(e)
            })
        }


async def handle_cache_stats(query_params: Dict[str, str]) -> Dict[str, Any]:
    """Handle cache statistics retrieval"""
    
    try:
        stats = performance_cache.get_stats()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'cache_stats': stats,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Cache stats retrieval failed',
                'message': str(e)
            })
        }


async def handle_cache_operation(request_data: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
    """Handle cache set/get operations"""
    
    try:
        operation = request_data.get('operation', 'get')
        prefix = request_data.get('prefix', 'api_responses')
        key = request_data.get('key')
        value = request_data.get('value')
        ttl_seconds = request_data.get('ttl_seconds', CacheConfig.DEFAULT_TTL)
        
        if not key:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Cache key is required'
                })
            }
        
        if operation == 'get':
            cached_value = performance_cache.get(prefix, key, user_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'operation': 'get',
                    'key': key,
                    'value': cached_value,
                    'found': cached_value is not None,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        elif operation == 'set':
            if value is None:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Cache value is required for set operation'
                    })
                }
            
            success = performance_cache.set(prefix, key, value, ttl_seconds, user_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'operation': 'set',
                    'key': key,
                    'success': success,
                    'ttl_seconds': ttl_seconds,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'Unknown cache operation: {operation}',
                    'supported_operations': ['get', 'set']
                })
            }
    
    except Exception as e:
        logger.error(f"Cache operation error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Cache operation failed',
                'message': str(e)
            })
        }


async def handle_cache_invalidation(request_data: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
    """Handle cache invalidation"""
    
    try:
        invalidation_type = request_data.get('type', 'user')
        prefix = request_data.get('prefix')
        key = request_data.get('key')
        
        if invalidation_type == 'user' and user_id:
            # Invalidate all cache for user
            invalidated_count = await performance_optimizer.invalidate_user_cache(user_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'invalidation_type': 'user',
                    'user_id': user_id,
                    'invalidated_count': invalidated_count,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        elif invalidation_type == 'key' and prefix and key:
            # Invalidate specific key
            success = performance_cache.delete(prefix, key, user_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'invalidation_type': 'key',
                    'prefix': prefix,
                    'key': key,
                    'success': success,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        elif invalidation_type == 'pattern' and prefix:
            # Invalidate pattern
            invalidated_count = performance_cache.invalidate_pattern(prefix, user_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'invalidation_type': 'pattern',
                    'prefix': prefix,
                    'invalidated_count': invalidated_count,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Invalid invalidation request',
                    'supported_types': ['user', 'key', 'pattern'],
                    'required_params': {
                        'user': ['user_id'],
                        'key': ['prefix', 'key'],
                        'pattern': ['prefix']
                    }
                })
            }
    
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Cache invalidation failed',
                'message': str(e)
            })
        }


async def handle_task_status(query_params: Dict[str, str], user_id: Optional[str]) -> Dict[str, Any]:
    """Handle async task status retrieval"""
    
    try:
        task_id = query_params.get('task_id')
        status_filter = query_params.get('status')
        limit = int(query_params.get('limit', '50'))
        
        if task_id:
            # Get specific task status
            task_status = await async_task_manager.get_task_status(task_id)
            
            if task_status:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'task': {
                            'task_id': task_status.task_id,
                            'task_type': task_status.task_type,
                            'user_id': task_status.user_id,
                            'status': task_status.status,
                            'progress': task_status.progress,
                            'created_at': task_status.created_at.isoformat(),
                            'started_at': task_status.started_at.isoformat() if task_status.started_at else None,
                            'completed_at': task_status.completed_at.isoformat() if task_status.completed_at else None,
                            'error': task_status.error
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    })
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': f'Task not found: {task_id}'
                    })
                }
        
        elif user_id:
            # Get user tasks
            tasks = await async_task_manager.list_user_tasks(
                user_id=user_id,
                status_filter=status_filter,
                limit=limit
            )
            
            task_list = []
            for task in tasks:
                task_list.append({
                    'task_id': task.task_id,
                    'task_type': task.task_type,
                    'status': task.status,
                    'progress': task.progress,
                    'created_at': task.created_at.isoformat(),
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                    'error': task.error
                })
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'tasks': task_list,
                    'user_id': user_id,
                    'status_filter': status_filter,
                    'count': len(task_list),
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Either task_id or user_id is required'
                })
            }
    
    except Exception as e:
        logger.error(f"Task status error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Task status retrieval failed',
                'message': str(e)
            })
        }


async def handle_task_submission(request_data: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
    """Handle async task submission"""
    
    try:
        task_type = request_data.get('task_type')
        task_data = request_data.get('task_data', {})
        background = request_data.get('background', False)
        delay_seconds = request_data.get('delay_seconds', 0)
        
        if not task_type:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'task_type is required'
                })
            }
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'user_id is required'
                })
            }
        
        if background:
            # Submit as background task
            message_id = await performance_optimizer.submit_background_task(
                task_type=task_type,
                user_id=user_id,
                task_data=task_data,
                delay_seconds=delay_seconds
            )
            
            return {
                'statusCode': 202,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message_id': message_id,
                    'task_type': task_type,
                    'status': 'queued',
                    'background': True,
                    'delay_seconds': delay_seconds,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        else:
            # Submit as async task (for functions that can be executed)
            # This would require the actual function to be available
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Direct async task submission not supported in this endpoint',
                    'suggestion': 'Use background=true for background task processing'
                })
            }
    
    except Exception as e:
        logger.error(f"Task submission error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Task submission failed',
                'message': str(e)
            })
        }


async def handle_system_optimization(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle system optimization"""
    
    try:
        optimization_results = await performance_optimizer.optimize_system_performance()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'optimization_results': optimization_results,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    
    except Exception as e:
        logger.error(f"System optimization error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'System optimization failed',
                'message': str(e)
            })
        }


async def handle_performance_analysis(query_params: Dict[str, str]) -> Dict[str, Any]:
    """Handle performance analysis"""
    
    try:
        analysis = await performance_optimizer.analyze_performance_issues()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'analysis': analysis,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    
    except Exception as e:
        logger.error(f"Performance analysis error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Performance analysis failed',
                'message': str(e)
            })
        }