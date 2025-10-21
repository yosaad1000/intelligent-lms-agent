"""
File Upload Handler for Document Processing
Handles file uploads, generates presigned URLs, and processes documents with Textract/Comprehend
"""

import json
import boto3
import os
import logging
from typing import Dict, Any, List
from botocore.exceptions import ClientError
import uuid
from datetime import datetime, timedelta
import mimetypes

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class FileUploadHandler:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.textract_client = boto3.client('textract')
        self.comprehend_client = boto3.client('comprehend')
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        
        self.bucket_name = os.environ.get('DOCUMENTS_BUCKET', 'lms-documents-dev')
        self.allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def generate_presigned_upload_url(self, filename: str, content_type: str, user_id: str) -> Dict[str, Any]:
        """Generate presigned URL for file upload"""
        try:
            # Validate file extension
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in self.allowed_extensions:
                return {
                    'success': False,
                    'error': f'File type {file_ext} not allowed. Allowed types: {", ".join(self.allowed_extensions)}'
                }
            
            # Generate unique file key
            file_id = str(uuid.uuid4())
            file_key = f"users/{user_id}/documents/{file_id}/{filename}"
            
            # Generate presigned URL
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ContentType': content_type,
                    'Metadata': {
                        'user_id': user_id,
                        'original_filename': filename,
                        'upload_timestamp': datetime.utcnow().isoformat()
                    }
                },
                ExpiresIn=3600  # 1 hour
            )
            
            return {
                'success': True,
                'upload_url': presigned_url,
                'file_key': file_key,
                'file_id': file_id,
                'expires_in': 3600
            }
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_uploaded_document(self, file_key: str, user_id: str) -> Dict[str, Any]:
        """Process uploaded document with Textract and Comprehend"""
        try:
            # Get file info
            file_info = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            content_type = file_info.get('ContentType', '')
            file_size = file_info.get('ContentLength', 0)
            
            # Extract text based on file type
            if content_type.startswith('image/') or content_type == 'application/pdf':
                extracted_text = self._extract_text_with_textract(file_key)
            else:
                # For text files, read directly
                extracted_text = self._extract_text_directly(file_key)
            
            if not extracted_text:
                return {
                    'success': False,
                    'error': 'No text could be extracted from the document'
                }
            
            # Analyze text with Comprehend
            analysis = self._analyze_text_with_comprehend(extracted_text)
            
            # Generate document summary
            summary = self._generate_document_summary(extracted_text)
            
            # Store processed document metadata
            document_metadata = {
                'file_key': file_key,
                'user_id': user_id,
                'original_filename': file_info.get('Metadata', {}).get('original_filename', 'unknown'),
                'content_type': content_type,
                'file_size': file_size,
                'extracted_text': extracted_text[:5000],  # Store first 5000 chars
                'full_text_length': len(extracted_text),
                'entities': analysis.get('entities', []),
                'key_phrases': analysis.get('key_phrases', []),
                'sentiment': analysis.get('sentiment', {}),
                'language': analysis.get('language', 'en'),
                'summary': summary,
                'processed_at': datetime.utcnow().isoformat(),
                'status': 'processed'
            }
            
            # Store metadata in S3
            metadata_key = file_key.replace(os.path.basename(file_key), 'metadata.json')
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=metadata_key,
                Body=json.dumps(document_metadata),
                ContentType='application/json'
            )
            
            return {
                'success': True,
                'document_id': file_key.split('/')[-2],  # Extract file_id from path
                'metadata': document_metadata,
                'processing_time': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_text_with_textract(self, file_key: str) -> str:
        """Extract text using AWS Textract"""
        try:
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': self.bucket_name,
                        'Name': file_key
                    }
                }
            )
            
            # Extract text from blocks
            text_blocks = []
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_blocks.append(block['Text'])
            
            return '\n'.join(text_blocks)
            
        except ClientError as e:
            logger.error(f"Textract extraction failed: {str(e)}")
            return ""
    
    def _extract_text_directly(self, file_key: str) -> str:
        """Extract text directly from text files"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            content = response['Body'].read()
            
            # Try to decode as UTF-8
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback to latin-1
                return content.decode('latin-1', errors='ignore')
                
        except ClientError as e:
            logger.error(f"Direct text extraction failed: {str(e)}")
            return ""
    
    def _analyze_text_with_comprehend(self, text: str) -> Dict[str, Any]:
        """Analyze text with Amazon Comprehend"""
        try:
            # Limit text length for Comprehend (5000 bytes max)
            text_sample = text[:4000] if len(text) > 4000 else text
            
            analysis = {}
            
            # Detect entities
            try:
                entities_response = self.comprehend_client.detect_entities(
                    Text=text_sample,
                    LanguageCode='en'
                )
                analysis['entities'] = [
                    {
                        'text': entity['Text'],
                        'type': entity['Type'],
                        'confidence': entity['Score']
                    }
                    for entity in entities_response.get('Entities', [])
                ]
            except Exception as e:
                logger.warning(f"Entity detection failed: {str(e)}")
                analysis['entities'] = []
            
            # Detect key phrases
            try:
                phrases_response = self.comprehend_client.detect_key_phrases(
                    Text=text_sample,
                    LanguageCode='en'
                )
                analysis['key_phrases'] = [
                    {
                        'text': phrase['Text'],
                        'confidence': phrase['Score']
                    }
                    for phrase in phrases_response.get('KeyPhrases', [])
                ]
            except Exception as e:
                logger.warning(f"Key phrase detection failed: {str(e)}")
                analysis['key_phrases'] = []
            
            # Detect sentiment
            try:
                sentiment_response = self.comprehend_client.detect_sentiment(
                    Text=text_sample,
                    LanguageCode='en'
                )
                analysis['sentiment'] = {
                    'sentiment': sentiment_response.get('Sentiment'),
                    'confidence': sentiment_response.get('SentimentScore', {})
                }
            except Exception as e:
                logger.warning(f"Sentiment detection failed: {str(e)}")
                analysis['sentiment'] = {}
            
            # Detect language
            try:
                language_response = self.comprehend_client.detect_dominant_language(Text=text_sample)
                languages = language_response.get('Languages', [])
                if languages:
                    analysis['language'] = languages[0]['LanguageCode']
                else:
                    analysis['language'] = 'en'
            except Exception as e:
                logger.warning(f"Language detection failed: {str(e)}")
                analysis['language'] = 'en'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Comprehend analysis failed: {str(e)}")
            return {}
    
    def _generate_document_summary(self, text: str) -> str:
        """Generate document summary using Bedrock"""
        try:
            # Use first 3000 characters for summary
            text_sample = text[:3000] if len(text) > 3000 else text
            
            prompt = f"""
            Please provide a concise summary of the following document content:
            
            {text_sample}
            
            Summary:"""
            
            response = self.bedrock_runtime.invoke_model(
                modelId='amazon.nova-micro-v1:0',
                body=json.dumps({
                    'inputText': prompt,
                    'textGenerationConfig': {
                        'maxTokenCount': 200,
                        'temperature': 0.3,
                        'topP': 0.9
                    }
                })
            )
            
            response_body = json.loads(response['body'].read())
            return response_body.get('results', [{}])[0].get('outputText', '').strip()
            
        except Exception as e:
            logger.warning(f"Summary generation failed: {str(e)}")
            return "Summary generation failed"
    
    def list_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """List documents for a user"""
        try:
            prefix = f"users/{user_id}/documents/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                Delimiter='/'
            )
            
            documents = []
            for prefix_info in response.get('CommonPrefixes', []):
                folder_name = prefix_info['Prefix']
                
                # Try to get metadata
                metadata_key = f"{folder_name}metadata.json"
                try:
                    metadata_obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=metadata_key)
                    metadata = json.loads(metadata_obj['Body'].read())
                    documents.append(metadata)
                except ClientError:
                    # If no metadata, create basic info
                    documents.append({
                        'file_key': folder_name,
                        'user_id': user_id,
                        'status': 'uploaded',
                        'processed_at': None
                    })
            
            return documents
            
        except ClientError as e:
            logger.error(f"Failed to list documents: {str(e)}")
            return []

def lambda_handler(event, context):
    """Lambda handler for file upload operations"""
    try:
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '')
        
        # Handle CORS preflight
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
                    'Access-Control-Max-Age': '86400'
                },
                'body': ''
            }
        
        # Parse request body
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': False, 'error': 'Invalid JSON'})
                }
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        
        # Initialize handler
        handler = FileUploadHandler()
        
        # Route based on path and method
        if path.endswith('/upload') and http_method == 'POST':
            return handle_upload_request(handler, body)
        elif path.endswith('/documents/process') and http_method == 'POST':
            return handle_process_request(handler, body)
        elif path.endswith('/documents') and http_method == 'GET':
            return handle_list_documents(handler, query_params)
        else:
            return {
                'statusCode': 404,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': False, 'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': 'Internal server error'})
        }

def handle_upload_request(handler: FileUploadHandler, body: Dict) -> Dict:
    """Handle file upload URL generation"""
    try:
        filename = body.get('filename')
        content_type = body.get('content_type')
        user_id = body.get('user_id')
        
        if not all([filename, content_type, user_id]):
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': 'filename, content_type, and user_id are required'
                })
            }
        
        result = handler.generate_presigned_upload_url(filename, content_type, user_id)
        
        return {
            'statusCode': 200 if result['success'] else 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def handle_process_request(handler: FileUploadHandler, body: Dict) -> Dict:
    """Handle document processing request"""
    try:
        file_key = body.get('file_key')
        user_id = body.get('user_id')
        
        if not all([file_key, user_id]):
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': 'file_key and user_id are required'
                })
            }
        
        result = handler.process_uploaded_document(file_key, user_id)
        
        return {
            'statusCode': 200 if result['success'] else 400,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def handle_list_documents(handler: FileUploadHandler, query_params: Dict) -> Dict:
    """Handle list documents request"""
    try:
        user_id = query_params.get('user_id')
        
        if not user_id:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': 'user_id is required'
                })
            }
        
        documents = handler.list_user_documents(user_id)
        
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'documents': documents,
                'count': len(documents)
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': str(e)})
        }