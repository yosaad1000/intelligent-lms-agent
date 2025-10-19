"""
Integration tests for RAG File Processing Lambda Function
Tests the complete Lambda function with mocked AWS services
"""

import json
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import boto3

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from file_processing.file_handler import lambda_handler


class TestRAGLambdaIntegration:
    """Test RAG Lambda function integration"""
    
    @pytest.fixture
    def setup_aws_environment(self):
        """Set up AWS environment for testing"""
        with mock_aws():
            # Set environment variables
            os.environ['DOCUMENTS_BUCKET'] = 'test-lms-documents'
            os.environ['AWS_ACCOUNT_ID'] = 'test-account'
            os.environ['AWS_REGION'] = 'us-east-1'
            os.environ['USE_MOCK_EMBEDDINGS'] = 'true'
            
            # Create S3 bucket
            s3_client = boto3.client('s3', region_name='us-east-1')
            s3_client.create_bucket(Bucket='test-lms-documents')
            
            # Create DynamoDB table
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            table = dynamodb.create_table(
                TableName='lms-user-files',
                KeySchema=[
                    {'AttributeName': 'file_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'file_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'user-id-index',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            yield {
                's3_client': s3_client,
                'dynamodb': dynamodb,
                'table': table
            }
    
    def test_file_upload_request(self, setup_aws_environment):
        """Test file upload request generation"""
        
        event = {
            'httpMethod': 'POST',
            'path': '/api/files',
            'body': json.dumps({
                'filename': 'test_document.pdf',
                'file_size': 1024000,
                'subject_id': 'physics_101'
            })
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        assert 'file_id' in body
        assert 'upload_url' in body
        assert 'process_url' in body
        assert body['status'] == 'ready_for_upload'
        
        # Verify CORS headers
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    def test_file_upload_validation_errors(self, setup_aws_environment):
        """Test file upload validation errors"""
        
        # Test missing filename
        event = {
            'httpMethod': 'POST',
            'path': '/api/files',
            'body': json.dumps({
                'file_size': 1024000
            })
        }
        
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        
        # Test unsupported file type
        event = {
            'httpMethod': 'POST',
            'path': '/api/files',
            'body': json.dumps({
                'filename': 'malware.exe',
                'file_size': 1024000
            })
        }
        
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        
        # Test file too large
        event = {
            'httpMethod': 'POST',
            'path': '/api/files',
            'body': json.dumps({
                'filename': 'huge_file.pdf',
                'file_size': 20 * 1024 * 1024  # 20MB
            })
        }
        
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
    
    def test_complete_file_processing_workflow(self, setup_aws_environment):
        """Test complete file processing workflow"""
        
        aws_env = setup_aws_environment
        
        # Step 1: Request file upload
        upload_event = {
            'httpMethod': 'POST',
            'path': '/api/files',
            'body': json.dumps({
                'filename': 'test_document.txt',
                'file_size': 1024,
                'subject_id': 'math_101'
            })
        }
        
        upload_response = lambda_handler(upload_event, {})
        assert upload_response['statusCode'] == 200
        
        upload_body = json.loads(upload_response['body'])
        file_id = upload_body['file_id']
        
        # Step 2: Simulate file upload to S3
        test_content = """
        This is a comprehensive test document for RAG processing.
        It contains educational content about mathematics and science.
        
        Key concepts covered:
        - Linear algebra fundamentals
        - Calculus applications
        - Statistical analysis methods
        
        This document will be processed into chunks for vector storage.
        """
        
        aws_env['s3_client'].put_object(
            Bucket='test-lms-documents',
            Key=f'raw-files/user_test-user-123/{file_id}_test_document.txt',
            Body=test_content.encode('utf-8')
        )
        
        # Step 3: Process file for RAG
        process_event = {
            'httpMethod': 'POST',
            'path': '/api/files/process',
            'body': json.dumps({
                'file_id': file_id
            })
        }
        
        process_response = lambda_handler(process_event, {})
        assert process_response['statusCode'] == 200
        
        process_body = json.loads(process_response['body'])
        assert process_body['file_id'] == file_id
        assert process_body['status'] == 'completed'
        assert process_body['chunks_created'] > 0
        assert process_body['vectors_stored'] > 0
        
        # Step 4: Check file status
        status_event = {
            'httpMethod': 'GET',
            'path': '/api/files/status',
            'queryStringParameters': {
                'file_id': file_id,
                'user_id': 'test-user-123'
            }
        }
        
        status_response = lambda_handler(status_event, {})
        assert status_response['statusCode'] == 200
        
        status_body = json.loads(status_response['body'])
        assert status_body['file_id'] == file_id
        assert status_body['processing_status'] == 'completed'
        assert status_body['chunks_created'] > 0
        assert status_body['vectors_stored'] > 0
        
        # Step 5: List user files
        list_event = {
            'httpMethod': 'GET',
            'path': '/api/files',
            'queryStringParameters': {
                'user_id': 'test-user-123'
            }
        }
        
        list_response = lambda_handler(list_event, {})
        assert list_response['statusCode'] == 200
        
        list_body = json.loads(list_response['body'])
        assert list_body['total'] == 1
        assert len(list_body['files']) == 1
        assert list_body['files'][0]['file_id'] == file_id
        assert list_body['files'][0]['processing_status'] == 'completed'
    
    def test_file_processing_errors(self, setup_aws_environment):
        """Test file processing error scenarios"""
        
        # Test processing non-existent file
        process_event = {
            'httpMethod': 'POST',
            'path': '/api/files/process',
            'body': json.dumps({
                'file_id': 'non-existent-file-123'
            })
        }
        
        response = lambda_handler(process_event, {})
        assert response['statusCode'] == 404
        
        # Test missing file_id
        process_event = {
            'httpMethod': 'POST',
            'path': '/api/files/process',
            'body': json.dumps({})
        }
        
        response = lambda_handler(process_event, {})
        assert response['statusCode'] == 400
    
    def test_access_control(self, setup_aws_environment):
        """Test user access control"""
        
        aws_env = setup_aws_environment
        
        # Create a file for user A
        file_metadata = {
            'file_id': 'user-a-file',
            'user_id': 'user-a',
            'filename': 'private_document.txt',
            's3_key': 'raw-files/user_user-a/user-a-file_private_document.txt',
            'status': 'pending',
            'processing_status': 'pending'
        }
        
        aws_env['table'].put_item(Item=file_metadata)
        
        # Try to process file as user B
        process_event = {
            'httpMethod': 'POST',
            'path': '/api/files/process',
            'body': json.dumps({
                'file_id': 'user-a-file'
            })
        }
        
        # This should fail because user_id defaults to 'test-user-123' which doesn't own the file
        response = lambda_handler(process_event, {})
        assert response['statusCode'] == 403
        
        # Try to get status as wrong user
        status_event = {
            'httpMethod': 'GET',
            'path': '/api/files/status',
            'queryStringParameters': {
                'file_id': 'user-a-file',
                'user_id': 'wrong-user'
            }
        }
        
        response = lambda_handler(status_event, {})
        assert response['statusCode'] == 403
    
    def test_method_not_allowed(self, setup_aws_environment):
        """Test unsupported HTTP methods"""
        
        event = {
            'httpMethod': 'DELETE',
            'path': '/api/files',
            'body': json.dumps({})
        }
        
        response = lambda_handler(event, {})
        assert response['statusCode'] == 405
        
        body = json.loads(response['body'])
        assert 'Method not allowed' in body['error']
    
    def test_malformed_requests(self, setup_aws_environment):
        """Test handling of malformed requests"""
        
        # Test invalid JSON
        event = {
            'httpMethod': 'POST',
            'path': '/api/files',
            'body': 'invalid json {'
        }
        
        response = lambda_handler(event, {})
        assert response['statusCode'] == 500
        
        # Test missing body
        event = {
            'httpMethod': 'POST',
            'path': '/api/files',
            'body': None
        }
        
        response = lambda_handler(event, {})
        # Should handle gracefully and return 400 for missing filename
        assert response['statusCode'] == 400
    
    def test_large_file_processing(self, setup_aws_environment):
        """Test processing of larger files with multiple chunks"""
        
        aws_env = setup_aws_environment
        
        # Create a large document
        large_content = """
        Chapter 1: Introduction to Machine Learning
        
        Machine learning is a subset of artificial intelligence that focuses on algorithms
        that can learn and make decisions from data. This field has revolutionized many
        industries and continues to grow rapidly.
        
        """ * 50  # Repeat to create a large document
        
        # Step 1: Request upload
        upload_event = {
            'httpMethod': 'POST',
            'path': '/api/files',
            'body': json.dumps({
                'filename': 'large_textbook.txt',
                'file_size': len(large_content.encode('utf-8')),
                'subject_id': 'cs_101'
            })
        }
        
        upload_response = lambda_handler(upload_event, {})
        assert upload_response['statusCode'] == 200
        
        upload_body = json.loads(upload_response['body'])
        file_id = upload_body['file_id']
        
        # Step 2: Upload content to S3
        aws_env['s3_client'].put_object(
            Bucket='test-lms-documents',
            Key=f'raw-files/user_test-user-123/{file_id}_large_textbook.txt',
            Body=large_content.encode('utf-8')
        )
        
        # Step 3: Process file
        process_event = {
            'httpMethod': 'POST',
            'path': '/api/files/process',
            'body': json.dumps({
                'file_id': file_id
            })
        }
        
        process_response = lambda_handler(process_event, {})
        assert process_response['statusCode'] == 200
        
        process_body = json.loads(process_response['body'])
        assert process_body['status'] == 'completed'
        assert process_body['chunks_created'] > 5  # Should create multiple chunks
        assert process_body['vectors_stored'] > 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])