"""
LangChain DynamoDB Memory Integration
Provides conversation memory storage using DynamoDB for LangChain/LangGraph workflows
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory

from .config import config
from .dynamodb_utils import db_utils

# Configure logging
logger = logging.getLogger(__name__)


class DynamoDBChatMessageHistory(BaseChatMessageHistory):
    """
    DynamoDB-based chat message history for LangChain
    Stores conversation messages in DynamoDB with session management
    """
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        table_name: str = "lms-chat-memory",
        ttl_seconds: int = 86400 * 30  # 30 days
    ):
        """
        Initialize DynamoDB chat message history
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            table_name: DynamoDB table name
            ttl_seconds: TTL for messages in seconds
        """
        
        self.session_id = session_id
        self.user_id = user_id
        self.table_name = table_name
        self.ttl_seconds = ttl_seconds
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource('dynamodb', **config.get_aws_config())
        self.table = self.dynamodb.Table(table_name)
        
        # Cache for messages
        self._messages_cache: Optional[List[BaseMessage]] = None
        
        logger.info(f"Initialized DynamoDB chat history for session {session_id}")
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Get all messages for this session"""
        
        if self._messages_cache is None:
            self._messages_cache = self._load_messages()
        
        return self._messages_cache
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the conversation history"""
        
        try:
            # Convert message to DynamoDB item
            message_item = self._message_to_item(message)
            
            # Store in DynamoDB
            self.table.put_item(Item=message_item)
            
            # Update cache
            if self._messages_cache is not None:
                self._messages_cache.append(message)
            
            logger.debug(f"Added message to session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error adding message to DynamoDB: {str(e)}")
            raise
    
    def add_user_message(self, message: str) -> None:
        """Add a user message"""
        self.add_message(HumanMessage(content=message))
    
    def add_ai_message(self, message: str) -> None:
        """Add an AI message"""
        self.add_message(AIMessage(content=message))
    
    def clear(self) -> None:
        """Clear all messages for this session"""
        
        try:
            # Query all messages for this session
            response = self.table.query(
                KeyConditionExpression='session_id = :session_id',
                ExpressionAttributeValues={':session_id': self.session_id}
            )
            
            # Delete all messages
            with self.table.batch_writer() as batch:
                for item in response['Items']:
                    batch.delete_item(
                        Key={
                            'session_id': item['session_id'],
                            'timestamp': item['timestamp']
                        }
                    )
            
            # Clear cache
            self._messages_cache = []
            
            logger.info(f"Cleared all messages for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error clearing messages from DynamoDB: {str(e)}")
            raise
    
    def _load_messages(self) -> List[BaseMessage]:
        """Load messages from DynamoDB"""
        
        try:
            # Query messages for this session
            response = self.table.query(
                KeyConditionExpression='session_id = :session_id',
                ExpressionAttributeValues={':session_id': self.session_id},
                ScanIndexForward=True  # Ascending order by timestamp
            )
            
            # Convert DynamoDB items to messages
            messages = []
            for item in response['Items']:
                message = self._item_to_message(item)
                if message:
                    messages.append(message)
            
            logger.debug(f"Loaded {len(messages)} messages for session {self.session_id}")
            return messages
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.warning(f"DynamoDB table {self.table_name} not found")
                return []
            else:
                logger.error(f"Error loading messages from DynamoDB: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error loading messages: {str(e)}")
            return []
    
    def _message_to_item(self, message: BaseMessage) -> Dict[str, Any]:
        """Convert LangChain message to DynamoDB item"""
        
        # Determine message type
        if isinstance(message, HumanMessage):
            message_type = "human"
        elif isinstance(message, AIMessage):
            message_type = "ai"
        elif isinstance(message, SystemMessage):
            message_type = "system"
        else:
            message_type = "unknown"
        
        # Calculate TTL
        ttl_timestamp = int(datetime.utcnow().timestamp()) + self.ttl_seconds
        
        return {
            'session_id': self.session_id,
            'timestamp': int(datetime.utcnow().timestamp() * 1000),  # Milliseconds for sorting
            'user_id': self.user_id,
            'message_type': message_type,
            'content': message.content,
            'additional_kwargs': message.additional_kwargs,
            'ttl': ttl_timestamp,
            'created_at': datetime.utcnow().isoformat()
        }
    
    def _item_to_message(self, item: Dict[str, Any]) -> Optional[BaseMessage]:
        """Convert DynamoDB item to LangChain message"""
        
        try:
            message_type = item.get('message_type', 'unknown')
            content = item.get('content', '')
            additional_kwargs = item.get('additional_kwargs', {})
            
            if message_type == "human":
                return HumanMessage(content=content, additional_kwargs=additional_kwargs)
            elif message_type == "ai":
                return AIMessage(content=content, additional_kwargs=additional_kwargs)
            elif message_type == "system":
                return SystemMessage(content=content, additional_kwargs=additional_kwargs)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error converting item to message: {str(e)}")
            return None
    
    def get_recent_messages(self, limit: int = 10) -> List[BaseMessage]:
        """Get recent messages with limit"""
        
        messages = self.messages
        return messages[-limit:] if len(messages) > limit else messages
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get conversation summary statistics"""
        
        messages = self.messages
        
        user_messages = [m for m in messages if isinstance(m, HumanMessage)]
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]
        
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'ai_messages': len(ai_messages),
            'first_message_time': messages[0].additional_kwargs.get('timestamp') if messages else None,
            'last_message_time': messages[-1].additional_kwargs.get('timestamp') if messages else None
        }


class LangChainMemoryManager:
    """
    Manager for LangChain memory instances
    Provides centralized memory management for different sessions
    """
    
    def __init__(self):
        """Initialize memory manager"""
        self._memory_instances: Dict[str, DynamoDBChatMessageHistory] = {}
        logger.info("LangChain memory manager initialized")
    
    def get_memory(
        self,
        session_id: str,
        user_id: str,
        table_name: str = "lms-chat-memory"
    ) -> DynamoDBChatMessageHistory:
        """
        Get or create memory instance for session
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            table_name: DynamoDB table name
            
        Returns:
            DynamoDB chat message history instance
        """
        
        memory_key = f"{session_id}_{user_id}"
        
        if memory_key not in self._memory_instances:
            self._memory_instances[memory_key] = DynamoDBChatMessageHistory(
                session_id=session_id,
                user_id=user_id,
                table_name=table_name
            )
        
        return self._memory_instances[memory_key]
    
    def clear_memory(self, session_id: str, user_id: str) -> None:
        """Clear memory for specific session"""
        
        memory_key = f"{session_id}_{user_id}"
        
        if memory_key in self._memory_instances:
            self._memory_instances[memory_key].clear()
            del self._memory_instances[memory_key]
    
    def get_all_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for a user"""
        
        try:
            # Query DynamoDB for all sessions for this user
            dynamodb = boto3.resource('dynamodb', **config.get_aws_config())
            table = dynamodb.Table("lms-chat-memory")
            
            # Use GSI to query by user_id
            response = table.query(
                IndexName='user-id-index',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id},
                ProjectionExpression='session_id'
            )
            
            # Extract unique session IDs
            session_ids = list(set(item['session_id'] for item in response['Items']))
            
            return session_ids
            
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {str(e)}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (handled by DynamoDB TTL)"""
        
        # DynamoDB TTL handles automatic cleanup
        # This method is for manual cleanup if needed
        
        logger.info("DynamoDB TTL handles automatic cleanup of expired sessions")
        return 0


# Global memory manager instance
memory_manager = LangChainMemoryManager()