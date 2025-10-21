"""
Test Document Processing Integration
Tests the complete document upload, processing, and retrieval workflow
"""

import pytest
import json
import boto3
import os
from moto import mock_s3, mock_textract, mock_comprehend
from unittest.mock import patch, MagicMock
import tempfile
from io import BytesIO

# Import the file upload handler
import sys
sys.path.append('src')
from file_processing.file_upload_handler import FileUploadHandler, lambda_handler

class TestDocumentProcessingIntegration:
    
    @mock_s3
    @mock_textract
    @mock_comprehend
    def setup_method(self):
        """Set up test environment"""
        # Create mock S3 bucket
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.bucket_name = 'test-lms-documents'
        self.s3_client.create_bucket(Bucket=self.bucket_name)
        
        # Set environment variables
        os.environ['DOCUMENTS_BUCKET'] = self.bucket_name
        
        # Initialize handler
        self.handler = FileUploadHandler()
        self.handler.bucket_name = self.bucket_name
    
    def test_generate_presigned_upload_url(self):
        """Test presigned URL generation"""
        result = self.handler.generate_presigned_upload_url(
            filename='test_document.pdf',
            content_type='application/pdf',
            user_id='test_user_123'
        )
        
        assert result['success'] is True
        assert 'upload_url' in result
        assert 'file_key' in result
        assert 'file_id' in result
        assert result['expires_in'] == 3600
        assert 'users/test_user_123/documents/' in result['file_key']
    
    def test_invalid_file_extension(self):
        """Test rejection of invalid file extensions"""
        result = self.handler.generate_presigned_upload_url(
            filename='test_document.exe',
            content_type='application/octet-stream',
            user_id='test_user_123'
        )
        
        assert result['success'] is False
        assert 'not allowed' in result['error']
    
    @mock_s3
    @mock_textract
    def test_textract_processing(self):
        """Test document processing with Textract"""
        # Upload a test file to S3
        file_key = 'users/test_user_123/documents/test_id/test.pdf'
        test_content = b'Test PDF content'
        
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=test_content,
            ContentType='application/pdf',
            Metadata={
                'user_id': 'test_user_123',
                'original_filename': 'test.pdf'
            }
        )
        
        # Mock Textract response
        with patch.object(self.handler.textract_client, 'detect_document_text') as mock_textract:
            mock_textract.return_value = {
                'Blocks': [
                    {
                        'BlockType': 'LINE',
                        'Text': 'This is a test document'
                    },
                    {
                        'BlockType': 'LINE', 
                        'Text': 'With multiple lines of text'
                    }
                ]
            }
            
            # Mock Comprehend responses
            with patch.object(self.handler.comprehend_client, 'detect_entities') as mock_entities, \
                 patch.object(self.handler.comprehend_client, 'detect_key_phrases') as mock_phrases, \
                 patch.object(self.handler.comprehend_client, 'detect_sentiment') as mock_sentiment, \
                 patch.object(self.handler.comprehend_client, 'detect_dominant_language') as mock_language:
                
                mock_entities.return_value = {
                    'Entities': [
                        {'Text': 'test document', 'Type': 'OTHER', 'Score': 0.95}
                    ]
                }
                mock_phrases.return_value = {
                    'KeyPhrases': [
                        {'Text': 'test document', 'Score': 0.90}
                    ]
                }
                mock_sentiment.return_value = {
                    'Sentiment': 'NEUTRAL',
                    'SentimentScore': {'Neutral': 0.85}
                }
                mock_language.return_value = {
                    'Languages': [{'LanguageCode': 'en', 'Score': 0.99}]
                }
                
                # Mock Bedrock summary generation
                with patch.object(self.handler.bedrock_runtime, 'invoke_model') as mock_bedrock:
                    mock_bedrock.return_value = {
                        'body': MagicMock(read=lambda: json.dumps({
                            'results': [{'outputText': 'This is a test document summary.'}]
                        }).encode())
                    }
                    
                    # Process the document
                    result = self.handler.process_uploaded_document(file_key, 'test_user_123')
                    
                    assert result['success'] is True
                    assert 'document_id' in result
                    assert 'metadata' in result
                    
                    metadata = result['metadata']
                    assert metadata['user_id'] == 'test_user_123'
                    assert metadata['status'] == 'processed'
                    assert 'This is a test document' in metadata['extracted_text']
                    assert len(metadata['entities']) > 0
                    assert len(metadata['key_phrases']) > 0
                    assert metadata['sentiment']['sentiment'] == 'NEUTRAL'
                    assert metadata['language'] == 'en'
                    assert metadata['summary'] == 'This is a test document summary.'
    
    @mock_s3
    def test_text_file_processing(self):
        """Test processing of plain text files"""
        # Upload a text file
        file_key = 'users/test_user_123/documents/test_id/test.txt'
        test_content = 'This is a plain text document with important information.'
        
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain',
            Metadata={
                'user_id': 'test_user_123',
                'original_filename': 'test.txt'
            }
        )
        
        # Mock Comprehend responses
        with patch.object(self.handler.comprehend_client, 'detect_entities') as mock_entities, \
             patch.object(self.handler.comprehend_client, 'detect_key_phrases') as mock_phrases, \
             patch.object(self.handler.comprehend_client, 'detect_sentiment') as mock_sentiment, \
             patch.object(self.handler.comprehend_client, 'detect_dominant_language') as mock_language:
            
            mock_entities.return_value = {'Entities': []}
            mock_phrases.return_value = {'KeyPhrases': []}
            mock_sentiment.return_value = {'Sentiment': 'NEUTRAL', 'SentimentScore': {}}
            mock_language.return_value = {'Languages': [{'LanguageCode': 'en'}]}
            
            # Mock Bedrock summary
            with patch.object(self.handler.bedrock_runtime, 'invoke_model') as mock_bedrock:
                mock_bedrock.return_value = {
                    'body': MagicMock(read=lambda: json.dumps({
                        'results': [{'outputText': 'Text file summary.'}]
                    }).encode())
                }
                
                result = self.handler.process_uploaded_document(file_key, 'test_user_123')
                
                assert result['success'] is True
                metadata = result['metadata']
                assert test_content in metadata['extracted_text']
                assert metadata['content_type'] == 'text/plain'
    
    @mock_s3
    def test_list_user_documents(self):
        """Test listing user documents"""
        # Create test documents
        user_id = 'test_user_123'
        
        # Document 1
        doc1_key = f'users/{user_id}/documents/doc1/'
        metadata1 = {
            'file_key': doc1_key,
            'user_id': user_id,
            'original_filename': 'document1.pdf',
            'status': 'processed'
        }
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=f'{doc1_key}metadata.json',
            Body=json.dumps(metadata1),
            ContentType='application/json'
        )
        
        # Document 2
        doc2_key = f'users/{user_id}/documents/doc2/'
        metadata2 = {
            'file_key': doc2_key,
            'user_id': user_id,
            'original_filename': 'document2.docx',
            'status': 'processed'
        }
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=f'{doc2_key}metadata.json',
            Body=json.dumps(metadata2),
            ContentType='application/json'
        )
        
        # List documents
        documents = self.handler.list_user_documents(user_id)
        
        assert len(documents) == 2
        filenames = [doc['original_filename'] for doc in documents]
        assert 'document1.pdf' in filenames
        assert 'document2.docx' in filenames
    
    def test_lambda_handler_upload_endpoint(self):
        """Test Lambda handler for upload endpoint"""
        event = {
            'httpMethod': 'POST',
            'path': '/api/v1/upload',
            'body': json.dumps({
                'filename': 'test.pdf',
                'content_type': 'application/pdf',
                'user_id': 'test_user_123'
            })
        }
        
        with patch('file_processing.file_upload_handler.FileUploadHandler') as mock_handler_class:
            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler
            mock_handler.generate_presigned_upload_url.return_value = {
                'success': True,
                'upload_url': 'https://test-url.com',
                'file_key': 'test-key',
                'file_id': 'test-id'
            }
            
            response = lambda_handler(event, {})
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            assert 'upload_url' in body
    
    def test_lambda_handler_process_endpoint(self):
        """Test Lambda handler for process endpoint"""
        event = {
            'httpMethod': 'POST',
            'path': '/api/v1/documents/process',
            'body': json.dumps({
                'file_key': 'users/test_user/documents/test_id/test.pdf',
                'user_id': 'test_user_123'
            })
        }
        
        with patch('file_processing.file_upload_handler.FileUploadHandler') as mock_handler_class:
            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler
            mock_handler.process_uploaded_document.return_value = {
                'success': True,
                'document_id': 'test_id',
                'metadata': {'status': 'processed'}
            }
            
            response = lambda_handler(event, {})
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            assert 'document_id' in body
    
    def test_lambda_handler_list_documents(self):
        """Test Lambda handler for list documents endpoint"""
        event = {
            'httpMethod': 'GET',
            'path': '/api/v1/documents',
            'queryStringParameters': {
                'user_id': 'test_user_123'
            }
        }
        
        with patch('file_processing.file_upload_handler.FileUploadHandler') as mock_handler_class:
            mock_handler = MagicMock()
            mock_handler_class.return_value = mock_handler
            mock_handler.list_user_documents.return_value = [
                {'original_filename': 'test1.pdf', 'status': 'processed'},
                {'original_filename': 'test2.docx', 'status': 'processed'}
            ]
            
            response = lambda_handler(event, {})
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
            assert len(body['documents']) == 2
    
    def test_lambda_handler_cors(self):
        """Test CORS preflight handling"""
        event = {
            'httpMethod': 'OPTIONS',
            'path': '/api/v1/upload'
        }
        
        response = lambda_handler(event, {})
        
        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
        assert 'Access-Control-Allow-Headers' in response['headers']
    
    def test_error_handling(self):
        """Test error handling in document processing"""
        # Test with non-existent file
        result = self.handler.process_uploaded_document(
            'non-existent-key',
            'test_user_123'
        )
        
        assert result['success'] is False
        assert 'error' in result

if __name__ == '__main__':
    pytest.main([__file__, '-v'])