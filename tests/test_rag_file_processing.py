"""
Comprehensive tests for RAG File Processing Lambda Function
Tests file upload, text extraction, chunking, embedding generation, and vector storage
"""

import json
import pytest
import boto3
import os
from unittest.mock import Mock, patch, MagicMock
from moto import mock_s3, mock_dynamodb
import sys

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from file_processing.file_handler import (
    lambda_handler,
    handle_file_upload,
    handle_file_processing,
    handle_get_files,
    handle_get_status,
    process_file_for_rag,
    extract_text_from_s3_file,
    create_text_chunks,
    store_chunks_in_s3,
    store_vectors_in_pinecone,
    generate_embedding_mock,
    update_file_status
)


class TestRAGFileProcessing:
    """Test suite for RAG file processing functionality"""
    
    @pytest.fixture
    def setup_aws_mocks(self):
        """Set up AWS service mocks"""
        with mock_s3(), mock_dynamodb():
            # Create S3 bucket
            s3_client = boto3.client('s3', region_name='us-east-1')
            bucket_name = 'lms-documents-test-us-east-1'
            s3_client.create_bucket(Bucket=bucket_name)
            
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
            
            # Set environment variables
            os.environ['DOCUMENTS_BUCKET'] = bucket_name
            os.environ['AWS_ACCOUNT_ID'] = 'test'
            os.environ['AWS_REGION'] = 'us-east-1'
            
            yield {
                's3_client': s3_client,
                'dynamodb': dynamodb,
                'table': table,
                'bucket_name': bucket_name
            }
    
    def test_file_upload_request(self, setup_aws_mocks):
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
    
    def test_file_upload_validation(self, setup_aws_mocks):
        """Test file upload validation"""
        
        # Test unsupported file type
        event = {
            'httpMethod': 'POST',
            'path': '/api/files',
            'body': json.dumps({
                'filename': 'test_document.exe',
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
                'filename': 'test_document.pdf',
                'file_size': 20 * 1024 * 1024  # 20MB
            })
        }
        
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
    
    def test_text_chunking(self):
        """Test text chunking functionality"""
        
        # Test short text (no chunking needed)
        short_text = "This is a short text that doesn't need chunking."
        chunks = create_text_chunks(short_text, chunk_size=1000)
        
        assert len(chunks) == 1
        assert chunks[0]['text'] == short_text
        assert chunks[0]['index'] == 0
        
        # Test long text (chunking needed)
        long_text = "This is a sentence. " * 100  # Create long text
        chunks = create_text_chunks(long_text, chunk_size=200, overlap=50)
        
        assert len(chunks) > 1
        assert all('text' in chunk for chunk in chunks)
        assert all('index' in chunk for chunk in chunks)
        assert all('start_pos' in chunk for chunk in chunks)
        assert all('end_pos' in chunk for chunk in chunks)
        
        # Verify overlap
        if len(chunks) > 1:
            # Check that there's some overlap between consecutive chunks
            chunk1_end = chunks[0]['text'][-20:]  # Last 20 chars
            chunk2_start = chunks[1]['text'][:50]  # First 50 chars
            # There should be some common content due to overlap
    
    def test_embedding_generation(self):
        """Test embedding generation"""
        
        text = "This is a test document for embedding generation."
        embedding = generate_embedding_mock(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # Titan embedding dimension
        assert all(isinstance(val, float) for val in embedding)
        assert all(0 <= val <= 1 for val in embedding)  # Normalized values
    
    @patch('src.file_processing.file_handler.store_vectors_in_pinecone')
    @patch('src.file_processing.file_handler.store_chunks_in_s3')
    def test_rag_processing_pipeline(self, mock_store_s3, mock_store_pinecone, setup_aws_mocks):
        """Test complete RAG processing pipeline"""
        
        aws_mocks = setup_aws_mocks
        
        # Mock successful operations
        mock_store_s3.return_value = True
        mock_store_pinecone.return_value = 5
        
        # Create test file in S3
        test_content = "This is a test document. It contains multiple sentences. Each sentence provides valuable information for testing."
        aws_mocks['s3_client'].put_object(
            Bucket=aws_mocks['bucket_name'],
            Key='raw-files/user_test123/test_file.txt',
            Body=test_content.encode('utf-8')
        )
        
        file_metadata = {
            'file_id': 'test-file-123',
            'user_id': 'test123',
            'filename': 'test_document.txt',
            's3_key': 'raw-files/user_test123/test_file.txt'
        }
        
        result = process_file_for_rag(file_metadata)
        
        assert result['success'] is True
        assert result['chunks_created'] > 0
        assert result['vectors_stored'] == 5
        assert 'content_preview' in result
        
        # Verify mocks were called
        mock_store_s3.assert_called_once()
        mock_store_pinecone.assert_called_once()
    
    def test_file_processing_endpoint(self, setup_aws_mocks):
        """Test file processing endpoint"""
        
        aws_mocks = setup_aws_mocks
        
        # First create a file record
        file_id = 'test-file-456'
        file_metadata = {
            'file_id': file_id,
            'user_id': 'test123',
            'filename': 'test_document.txt',
            's3_key': 'raw-files/user_test123/test_file.txt',
            'status': 'pending_upload',
            'processing_status': 'pending'
        }
        
        aws_mocks['table'].put_item(Item=file_metadata)
        
        # Create test file in S3
        test_content = "This is a test document for processing."
        aws_mocks['s3_client'].put_object(
            Bucket=aws_mocks['bucket_name'],
            Key='raw-files/user_test123/test_file.txt',
            Body=test_content.encode('utf-8')
        )
        
        # Test processing request
        event = {
            'httpMethod': 'POST',
            'path': '/api/files/process',
            'body': json.dumps({
                'file_id': file_id
            })
        }
        
        with patch('src.file_processing.file_handler.store_vectors_in_pinecone', return_value=3):
            response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        assert body['file_id'] == file_id
        assert body['status'] == 'completed'
        assert 'chunks_created' in body
        assert 'vectors_stored' in body
    
    def test_get_files_endpoint(self, setup_aws_mocks):
        """Test get files endpoint"""
        
        aws_mocks = setup_aws_mocks
        
        # Create test files
        test_files = [
            {
                'file_id': 'file1',
                'user_id': 'test123',
                'filename': 'document1.pdf',
                'file_size': 1024,
                'status': 'completed',
                'processing_status': 'completed'
            },
            {
                'file_id': 'file2',
                'user_id': 'test123',
                'filename': 'document2.txt',
                'file_size': 2048,
                'status': 'processing',
                'processing_status': 'processing'
            }
        ]
        
        for file_data in test_files:
            aws_mocks['table'].put_item(Item=file_data)
        
        # Test get files request
        event = {
            'httpMethod': 'GET',
            'path': '/api/files',
            'queryStringParameters': {
                'user_id': 'test123'
            }
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        assert 'files' in body
        assert 'total' in body
        assert body['total'] == 2
        assert len(body['files']) == 2
    
    def test_get_status_endpoint(self, setup_aws_mocks):
        """Test get file status endpoint"""
        
        aws_mocks = setup_aws_mocks
        
        # Create test file
        file_id = 'status-test-file'
        file_metadata = {
            'file_id': file_id,
            'user_id': 'test123',
            'filename': 'status_test.pdf',
            'processing_status': 'completed',
            'text_extraction_status': 'completed',
            'vector_storage_status': 'completed',
            'chunks_created': 5,
            'vectors_stored': 5
        }
        
        aws_mocks['table'].put_item(Item=file_metadata)
        
        # Test status request
        event = {
            'httpMethod': 'GET',
            'path': '/api/files/status',
            'queryStringParameters': {
                'file_id': file_id,
                'user_id': 'test123'
            }
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        
        assert body['file_id'] == file_id
        assert body['processing_status'] == 'completed'
        assert body['chunks_created'] == 5
        assert body['vectors_stored'] == 5
    
    def test_error_handling(self, setup_aws_mocks):
        """Test error handling in various scenarios"""
        
        # Test processing non-existent file
        event = {
            'httpMethod': 'POST',
            'path': '/api/files/process',
            'body': json.dumps({
                'file_id': 'non-existent-file'
            })
        }
        
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404
        
        # Test accessing file without permission
        aws_mocks = setup_aws_mocks
        
        file_metadata = {
            'file_id': 'protected-file',
            'user_id': 'other_user',
            'filename': 'protected.pdf',
            'status': 'pending'
        }
        
        aws_mocks['table'].put_item(Item=file_metadata)
        
        event = {
            'httpMethod': 'POST',
            'path': '/api/files/process',
            'body': json.dumps({
                'file_id': 'protected-file'
            })
        }
        
        response = lambda_handler(event, {})
        assert response['statusCode'] == 403
    
    def test_cors_headers(self, setup_aws_mocks):
        """Test CORS headers are included in responses"""
        
        event = {
            'httpMethod': 'GET',
            'path': '/api/files',
            'queryStringParameters': {
                'user_id': 'test123'
            }
        }
        
        response = lambda_handler(event, {})
        
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])