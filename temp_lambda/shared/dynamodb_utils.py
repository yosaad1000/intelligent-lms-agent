"""
DynamoDB utility functions for LMS system
Provides common database operations and helpers
"""

import boto3
import json
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from boto3.dynamodb.conditions import Key, Attr


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for DynamoDB Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


class DynamoDBUtils:
    """Utility class for DynamoDB operations"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.tables = {
            'user_files': self.dynamodb.Table('lms-user-files'),
            'chat_conversations': self.dynamodb.Table('lms-chat-conversations'),
            'chat_messages': self.dynamodb.Table('lms-chat-messages'),
            'quizzes': self.dynamodb.Table('lms-quizzes'),
            'quiz_submissions': self.dynamodb.Table('lms-quiz-submissions'),
            'interviews': self.dynamodb.Table('lms-interviews'),
            'interview_sessions': self.dynamodb.Table('lms-interview-sessions'),
            'user_analytics': self.dynamodb.Table('lms-user-analytics'),
            'learning_progress': self.dynamodb.Table('lms-learning-progress')
        }
    
    def get_table(self, table_name: str):
        """Get DynamoDB table resource"""
        if table_name not in self.tables:
            raise ValueError(f"Unknown table: {table_name}")
        return self.tables[table_name]
    
    def put_item(self, table_name: str, item: Dict[str, Any]) -> bool:
        """Put item into DynamoDB table"""
        try:
            table = self.get_table(table_name)
            table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error putting item to {table_name}: {str(e)}")
            return False
    
    def get_item(self, table_name: str, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get item from DynamoDB table"""
        try:
            table = self.get_table(table_name)
            response = table.get_item(Key=key)
            return response.get('Item')
        except Exception as e:
            print(f"Error getting item from {table_name}: {str(e)}")
            return None
    
    def query_items(self, table_name: str, key_condition: Any, 
                   index_name: Optional[str] = None, 
                   filter_expression: Optional[Any] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query items from DynamoDB table"""
        try:
            table = self.get_table(table_name)
            
            query_params = {
                'KeyConditionExpression': key_condition
            }
            
            if index_name:
                query_params['IndexName'] = index_name
            if filter_expression:
                query_params['FilterExpression'] = filter_expression
            if limit:
                query_params['Limit'] = limit
            
            response = table.query(**query_params)
            return response.get('Items', [])
        except Exception as e:
            print(f"Error querying {table_name}: {str(e)}")
            return []
    
    def update_item(self, table_name: str, key: Dict[str, Any], 
                   update_expression: str, expression_values: Dict[str, Any]) -> bool:
        """Update item in DynamoDB table"""
        try:
            table = self.get_table(table_name)
            table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            return True
        except Exception as e:
            print(f"Error updating item in {table_name}: {str(e)}")
            return False
    
    def delete_item(self, table_name: str, key: Dict[str, Any]) -> bool:
        """Delete item from DynamoDB table"""
        try:
            table = self.get_table(table_name)
            table.delete_item(Key=key)
            return True
        except Exception as e:
            print(f"Error deleting item from {table_name}: {str(e)}")
            return False
    
    def serialize_for_json(self, data: Any) -> Any:
        """Serialize DynamoDB data for JSON response"""
        return json.loads(json.dumps(data, cls=DecimalEncoder))


# Specific helper functions for common operations

def create_file_record(user_id: str, filename: str, s3_key: str, 
                      subject_id: Optional[str] = None, file_size: int = 0) -> Dict[str, Any]:
    """Create a file record for DynamoDB"""
    file_id = str(uuid.uuid4())
    return {
        'file_id': file_id,
        'user_id': user_id,
        'filename': filename,
        's3_key': s3_key,
        'subject_id': subject_id,
        'file_size': file_size,
        'status': 'pending_upload',
        'upload_timestamp': datetime.utcnow().isoformat(),
        'processing_status': 'pending',
        'ttl': int((datetime.utcnow() + timedelta(days=365)).timestamp())
    }


def create_conversation_record(user_id: str, subject_id: Optional[str] = None, 
                             conversation_type: str = 'general') -> Dict[str, Any]:
    """Create a conversation record for DynamoDB"""
    conversation_id = str(uuid.uuid4())
    title = f"Subject Chat - {subject_id}" if subject_id else "General Chat"
    
    return {
        'conversation_id': conversation_id,
        'user_id': user_id,
        'subject_id': subject_id,
        'conversation_type': conversation_type,
        'title': title,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'message_count': 0,
        'status': 'active'
    }


def create_message_record(conversation_id: str, user_id: str, content: str, 
                         message_type: str = 'user', citations: List[str] = None) -> Dict[str, Any]:
    """Create a message record for DynamoDB"""
    message_id = str(uuid.uuid4())
    timestamp = int(datetime.utcnow().timestamp() * 1000)  # Milliseconds
    
    return {
        'conversation_id': conversation_id,
        'timestamp': timestamp,
        'message_id': message_id,
        'user_id': user_id,
        'message_type': message_type,  # 'user' or 'assistant'
        'content': content,
        'citations': citations or [],
        'context_used': {},
        'created_at': datetime.utcnow().isoformat()
    }


def create_quiz_record(created_by: str, subject_id: str, title: str, 
                      questions: List[Dict], difficulty: str = 'medium') -> Dict[str, Any]:
    """Create a quiz record for DynamoDB"""
    quiz_id = str(uuid.uuid4())
    
    return {
        'quiz_id': quiz_id,
        'subject_id': subject_id,
        'created_by': created_by,
        'title': title,
        'description': '',
        'questions': questions,
        'difficulty': difficulty,
        'time_limit': 30,  # minutes
        'max_attempts': 3,
        'status': 'active',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'total_questions': len(questions)
    }


def create_quiz_submission_record(quiz_id: str, user_id: str, answers: List[Dict], 
                                score: float, time_taken: int) -> Dict[str, Any]:
    """Create a quiz submission record for DynamoDB"""
    submission_id = str(uuid.uuid4())
    submitted_at = int(datetime.utcnow().timestamp() * 1000)
    
    return {
        'submission_id': submission_id,
        'quiz_id': quiz_id,
        'user_id': user_id,
        'answers': answers,
        'score': score,
        'time_taken': time_taken,  # seconds
        'submitted_at': submitted_at,
        'status': 'completed',
        'created_at': datetime.utcnow().isoformat()
    }


def create_analytics_record(user_id: str, subject_id: str, 
                          metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Create a user analytics record for DynamoDB"""
    updated_at = int(datetime.utcnow().timestamp() * 1000)
    
    return {
        'user_id': user_id,
        'subject_id': subject_id,
        'metrics': metrics,
        'updated_at': updated_at,
        'created_at': datetime.utcnow().isoformat()
    }


# Global instance for easy import
db_utils = DynamoDBUtils()