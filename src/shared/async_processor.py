"""
Async Processing System for LMS API
Handles long-running operations with proper async/await patterns and background processing
"""

import asyncio
import boto3
import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AsyncTask:
    """Represents an async task"""
    task_id: str
    task_type: str
    user_id: str
    status: str  # pending, running, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AsyncTaskManager:
    """
    Manages async tasks with progress tracking and result storage
    """
    
    def __init__(self):
        """Initialize async task manager"""
        
        # DynamoDB for task tracking
        self.dynamodb = boto3.resource('dynamodb')
        self.tasks_table_name = os.getenv('ASYNC_TASKS_TABLE', 'lms-async-tasks')
        
        try:
            self.tasks_table = self.dynamodb.Table(self.tasks_table_name)
        except Exception as e:
            logger.warning(f"Async tasks table not available: {e}")
            self.tasks_table = None
        
        # In-memory task tracking for Lambda container reuse
        self._active_tasks = {}
        self._task_results = {}
        
        # Thread pool for CPU-intensive tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        
        # SQS for background task queue (optional)
        self.sqs = boto3.client('sqs')
        self.queue_url = os.getenv('BACKGROUND_QUEUE_URL')
    
    async def submit_task(
        self,
        task_type: str,
        user_id: str,
        task_function: Callable,
        *args,
        **kwargs
    ) -> str:
        """
        Submit an async task for processing
        
        Args:
            task_type: Type of task (e.g., 'file_processing', 'quiz_generation')
            user_id: User ID
            task_function: Function to execute
            *args, **kwargs: Arguments for the task function
            
        Returns:
            Task ID for tracking
        """
        
        task_id = str(uuid.uuid4())
        task = AsyncTask(
            task_id=task_id,
            task_type=task_type,
            user_id=user_id,
            status='pending',
            created_at=datetime.utcnow(),
            metadata={
                'args_count': len(args),
                'kwargs_keys': list(kwargs.keys())
            }
        )
        
        # Store task in DynamoDB
        await self._store_task(task)
        
        # Store in memory for immediate access
        self._active_tasks[task_id] = task
        
        # Execute task asynchronously
        asyncio.create_task(self._execute_task(task, task_function, *args, **kwargs))
        
        logger.info(f"Submitted async task: {task_id} ({task_type}) for user: {user_id}")
        return task_id
    
    async def _execute_task(
        self,
        task: AsyncTask,
        task_function: Callable,
        *args,
        **kwargs
    ) -> None:
        """Execute async task with error handling and progress tracking"""
        
        try:
            # Update task status to running
            task.status = 'running'
            task.started_at = datetime.utcnow()
            await self._store_task(task)
            
            # Execute task function
            if asyncio.iscoroutinefunction(task_function):
                # Async function
                result = await task_function(*args, **kwargs)
            else:
                # Sync function - run in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.thread_pool,
                    task_function,
                    *args,
                    **kwargs
                )
            
            # Task completed successfully
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.progress = 100.0
            task.result = result
            
            # Store result
            self._task_results[task.task_id] = result
            
            logger.info(f"Async task completed: {task.task_id}")
            
        except Exception as e:
            # Task failed
            task.status = 'failed'
            task.completed_at = datetime.utcnow()
            task.error = str(e)
            
            logger.error(f"Async task failed: {task.task_id} - {str(e)}")
        
        finally:
            # Update task in storage
            await self._store_task(task)
            
            # Update in-memory tracking
            self._active_tasks[task.task_id] = task
    
    async def get_task_status(self, task_id: str) -> Optional[AsyncTask]:
        """Get task status and progress"""
        
        # Check in-memory first
        if task_id in self._active_tasks:
            return self._active_tasks[task_id]
        
        # Check DynamoDB
        if self.tasks_table:
            try:
                response = self.tasks_table.get_item(Key={'task_id': task_id})
                if 'Item' in response:
                    item = response['Item']
                    return AsyncTask(
                        task_id=item['task_id'],
                        task_type=item['task_type'],
                        user_id=item['user_id'],
                        status=item['status'],
                        created_at=datetime.fromisoformat(item['created_at']),
                        started_at=datetime.fromisoformat(item['started_at']) if item.get('started_at') else None,
                        completed_at=datetime.fromisoformat(item['completed_at']) if item.get('completed_at') else None,
                        progress=float(item.get('progress', 0.0)),
                        result=item.get('result'),
                        error=item.get('error'),
                        metadata=item.get('metadata')
                    )
            except Exception as e:
                logger.error(f"Error getting task status: {e}")
        
        return None
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result if completed"""
        
        # Check in-memory cache first
        if task_id in self._task_results:
            return self._task_results[task_id]
        
        # Get task status
        task = await self.get_task_status(task_id)
        if task and task.status == 'completed' and task.result:
            # Cache result in memory
            self._task_results[task_id] = task.result
            return task.result
        
        return None
    
    async def list_user_tasks(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[AsyncTask]:
        """List tasks for a user"""
        
        tasks = []
        
        # Get from in-memory first
        for task in self._active_tasks.values():
            if task.user_id == user_id:
                if status_filter is None or task.status == status_filter:
                    tasks.append(task)
        
        # Get from DynamoDB if available
        if self.tasks_table:
            try:
                if status_filter:
                    response = self.tasks_table.query(
                        IndexName='user-status-index',
                        KeyConditionExpression='user_id = :user_id AND #status = :status',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={
                            ':user_id': user_id,
                            ':status': status_filter
                        },
                        Limit=limit,
                        ScanIndexForward=False
                    )
                else:
                    response = self.tasks_table.query(
                        IndexName='user-id-index',
                        KeyConditionExpression='user_id = :user_id',
                        ExpressionAttributeValues={':user_id': user_id},
                        Limit=limit,
                        ScanIndexForward=False
                    )
                
                for item in response.get('Items', []):
                    task_id = item['task_id']
                    # Avoid duplicates from in-memory
                    if task_id not in self._active_tasks:
                        tasks.append(AsyncTask(
                            task_id=task_id,
                            task_type=item['task_type'],
                            user_id=item['user_id'],
                            status=item['status'],
                            created_at=datetime.fromisoformat(item['created_at']),
                            started_at=datetime.fromisoformat(item['started_at']) if item.get('started_at') else None,
                            completed_at=datetime.fromisoformat(item['completed_at']) if item.get('completed_at') else None,
                            progress=float(item.get('progress', 0.0)),
                            result=item.get('result'),
                            error=item.get('error'),
                            metadata=item.get('metadata')
                        ))
                        
            except Exception as e:
                logger.error(f"Error listing user tasks: {e}")
        
        # Sort by created_at descending
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks[:limit]
    
    async def _store_task(self, task: AsyncTask) -> None:
        """Store task in DynamoDB"""
        
        if not self.tasks_table:
            return
        
        try:
            item = {
                'task_id': task.task_id,
                'task_type': task.task_type,
                'user_id': task.user_id,
                'status': task.status,
                'created_at': task.created_at.isoformat(),
                'progress': task.progress,
                'ttl': int((datetime.utcnow() + timedelta(days=7)).timestamp())  # 7 day TTL
            }
            
            if task.started_at:
                item['started_at'] = task.started_at.isoformat()
            if task.completed_at:
                item['completed_at'] = task.completed_at.isoformat()
            if task.result:
                item['result'] = task.result
            if task.error:
                item['error'] = task.error
            if task.metadata:
                item['metadata'] = task.metadata
            
            self.tasks_table.put_item(Item=item)
            
        except Exception as e:
            logger.error(f"Error storing task: {e}")
    
    async def cleanup_completed_tasks(self, older_than_hours: int = 24) -> int:
        """Clean up completed tasks older than specified hours"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        cleaned_count = 0
        
        # Clean up in-memory tasks
        tasks_to_remove = []
        for task_id, task in self._active_tasks.items():
            if (task.status in ['completed', 'failed'] and 
                task.completed_at and 
                task.completed_at < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self._active_tasks[task_id]
            if task_id in self._task_results:
                del self._task_results[task_id]
            cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} completed async tasks")
        return cleaned_count


class BackgroundTaskQueue:
    """
    Background task queue for file processing and indexing
    Uses SQS for reliable task queuing
    """
    
    def __init__(self):
        """Initialize background task queue"""
        
        self.sqs = boto3.client('sqs')
        self.queue_url = os.getenv('BACKGROUND_QUEUE_URL')
        self.dlq_url = os.getenv('BACKGROUND_DLQ_URL')
        
        # Task processors
        self.task_processors = {
            'file_processing': self._process_file_task,
            'document_indexing': self._process_indexing_task,
            'quiz_generation': self._process_quiz_task,
            'analytics_calculation': self._process_analytics_task,
            'cache_warming': self._process_cache_warming_task
        }
    
    async def enqueue_task(
        self,
        task_type: str,
        user_id: str,
        task_data: Dict[str, Any],
        delay_seconds: int = 0
    ) -> str:
        """
        Enqueue a background task
        
        Args:
            task_type: Type of background task
            user_id: User ID
            task_data: Task-specific data
            delay_seconds: Delay before processing
            
        Returns:
            Message ID
        """
        
        if not self.queue_url:
            logger.warning("Background queue not configured")
            return ""
        
        message_body = {
            'task_id': str(uuid.uuid4()),
            'task_type': task_type,
            'user_id': user_id,
            'task_data': task_data,
            'created_at': datetime.utcnow().isoformat(),
            'retry_count': 0
        }
        
        try:
            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body),
                DelaySeconds=delay_seconds,
                MessageAttributes={
                    'task_type': {
                        'StringValue': task_type,
                        'DataType': 'String'
                    },
                    'user_id': {
                        'StringValue': user_id,
                        'DataType': 'String'
                    }
                }
            )
            
            message_id = response['MessageId']
            logger.info(f"Enqueued background task: {message_id} ({task_type}) for user: {user_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error enqueuing background task: {e}")
            return ""
    
    async def process_queue_messages(self, max_messages: int = 10) -> int:
        """
        Process messages from the background queue
        
        Args:
            max_messages: Maximum messages to process
            
        Returns:
            Number of messages processed
        """
        
        if not self.queue_url:
            return 0
        
        processed_count = 0
        
        try:
            # Receive messages from queue
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=min(max_messages, 10),
                WaitTimeSeconds=5,  # Long polling
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            
            # Process messages concurrently
            tasks = []
            for message in messages:
                task = asyncio.create_task(self._process_message(message))
                tasks.append(task)
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Error processing message: {result}")
                    elif result:
                        processed_count += 1
                        # Delete successfully processed message
                        try:
                            self.sqs.delete_message(
                                QueueUrl=self.queue_url,
                                ReceiptHandle=messages[i]['ReceiptHandle']
                            )
                        except Exception as e:
                            logger.error(f"Error deleting message: {e}")
            
        except Exception as e:
            logger.error(f"Error processing queue messages: {e}")
        
        return processed_count
    
    async def _process_message(self, message: Dict[str, Any]) -> bool:
        """Process a single queue message"""
        
        try:
            # Parse message body
            body = json.loads(message['Body'])
            task_type = body['task_type']
            user_id = body['user_id']
            task_data = body['task_data']
            
            # Get task processor
            processor = self.task_processors.get(task_type)
            if not processor:
                logger.error(f"Unknown task type: {task_type}")
                return False
            
            # Process task
            result = await processor(user_id, task_data)
            
            if result:
                logger.info(f"Successfully processed background task: {task_type} for user: {user_id}")
                return True
            else:
                logger.warning(f"Background task processing failed: {task_type} for user: {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error processing background message: {e}")
            return False
    
    async def _process_file_task(self, user_id: str, task_data: Dict[str, Any]) -> bool:
        """Process file processing task"""
        
        try:
            file_key = task_data.get('file_key')
            file_name = task_data.get('file_name')
            
            if not file_key or not file_name:
                logger.error("Missing file_key or file_name in task data")
                return False
            
            # Import and use file processing service
            from .file_processing_service import FileProcessingService
            
            processor = FileProcessingService()
            result = await processor.process_file_async(user_id, file_key, file_name)
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error processing file task: {e}")
            return False
    
    async def _process_indexing_task(self, user_id: str, task_data: Dict[str, Any]) -> bool:
        """Process document indexing task"""
        
        try:
            document_id = task_data.get('document_id')
            content = task_data.get('content')
            
            if not document_id or not content:
                logger.error("Missing document_id or content in task data")
                return False
            
            # Import and use indexing service
            from .vector_indexing_service import VectorIndexingService
            
            indexer = VectorIndexingService()
            result = await indexer.index_document_async(user_id, document_id, content)
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error processing indexing task: {e}")
            return False
    
    async def _process_quiz_task(self, user_id: str, task_data: Dict[str, Any]) -> bool:
        """Process quiz generation task"""
        
        try:
            topic = task_data.get('topic')
            difficulty = task_data.get('difficulty', 'medium')
            question_count = task_data.get('question_count', 5)
            
            if not topic:
                logger.error("Missing topic in quiz task data")
                return False
            
            # Import and use quiz service
            from ..quiz_generator.enhanced_quiz_handler import EnhancedQuizGenerator
            
            generator = EnhancedQuizGenerator()
            result = await generator.generate_quiz_with_translation(
                topic=topic,
                difficulty=difficulty,
                question_count=question_count,
                user_id=user_id
            )
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error processing quiz task: {e}")
            return False
    
    async def _process_analytics_task(self, user_id: str, task_data: Dict[str, Any]) -> bool:
        """Process analytics calculation task"""
        
        try:
            analytics_type = task_data.get('analytics_type')
            
            if not analytics_type:
                logger.error("Missing analytics_type in task data")
                return False
            
            # Import and use analytics service
            from ..analytics.learning_analytics_handler import LearningAnalyticsService
            
            analytics = LearningAnalyticsService()
            
            if analytics_type == 'progress_update':
                result = await analytics.update_learning_progress(user_id, task_data)
            elif analytics_type == 'concept_mastery':
                result = await analytics.calculate_concept_mastery(user_id, task_data)
            else:
                logger.error(f"Unknown analytics type: {analytics_type}")
                return False
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Error processing analytics task: {e}")
            return False
    
    async def _process_cache_warming_task(self, user_id: str, task_data: Dict[str, Any]) -> bool:
        """Process cache warming task"""
        
        try:
            cache_types = task_data.get('cache_types', ['user_files', 'chat_history'])
            
            # Import cache service
            from .performance_cache import warm_cache_for_user
            
            result = warm_cache_for_user(user_id)
            
            return result.get('warmed_entries', 0) > 0
            
        except Exception as e:
            logger.error(f"Error processing cache warming task: {e}")
            return False


# Global instances
async_task_manager = AsyncTaskManager()
background_task_queue = BackgroundTaskQueue()


# Decorator for async processing
def async_task(task_type: str):
    """
    Decorator to make a function run as an async task
    
    Args:
        task_type: Type of async task
    """
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user_id from args or kwargs
            user_id = None
            if args and isinstance(args[0], str):
                user_id = args[0]
            elif 'user_id' in kwargs:
                user_id = kwargs['user_id']
            
            if not user_id:
                # Execute synchronously if no user_id
                return await func(*args, **kwargs)
            
            # Submit as async task
            task_id = await async_task_manager.submit_task(
                task_type=task_type,
                user_id=user_id,
                task_function=func,
                *args,
                **kwargs
            )
            
            return {'task_id': task_id, 'status': 'submitted'}
        
        return wrapper
    return decorator


# Background task decorator
def background_task(task_type: str, delay_seconds: int = 0):
    """
    Decorator to make a function run as a background task
    
    Args:
        task_type: Type of background task
        delay_seconds: Delay before processing
    """
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user_id from args or kwargs
            user_id = None
            if args and isinstance(args[0], str):
                user_id = args[0]
            elif 'user_id' in kwargs:
                user_id = kwargs['user_id']
            
            if not user_id:
                logger.warning("No user_id found for background task")
                return {'error': 'user_id required for background tasks'}
            
            # Prepare task data
            task_data = {
                'function_name': func.__name__,
                'args': args[1:] if args else [],  # Skip user_id
                'kwargs': {k: v for k, v in kwargs.items() if k != 'user_id'}
            }
            
            # Enqueue background task
            message_id = await background_task_queue.enqueue_task(
                task_type=task_type,
                user_id=user_id,
                task_data=task_data,
                delay_seconds=delay_seconds
            )
            
            return {'message_id': message_id, 'status': 'queued'}
        
        return wrapper
    return decorator