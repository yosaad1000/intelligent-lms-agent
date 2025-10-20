"""
RAG File Processing Lambda Function
Handles file uploads, text extraction, chunking, embedding generation, and vector storage
"""

import json
import boto3
import os
import uuid
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

# Text extraction libraries
try:
    import PyPDF2
    from docx import Document
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: PDF/DOCX processing not available. Install with: pip install PyPDF2 python-docx")

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle file upload and RAG processing requests
    """
    
    try:
        # Parse request body
        body_str = event.get('body', '{}')
        if body_str is None:
            body_str = '{}'
        body = json.loads(body_str)
        
        # Handle different operations
        http_method = event['httpMethod']
        path = event.get('path', '')
        
        if http_method == 'POST':
            # For POST, get user_id from body
            user_id = body.get('user_id', 'test-user-123')
            
            if '/process' in path:
                # Process uploaded file for RAG
                return handle_file_processing(body, user_id)
            else:
                # Generate presigned URL for upload
                return handle_file_upload(body, user_id)
                
        elif http_method == 'GET':
            # For GET, get user_id from query parameters
            query_params = event.get('queryStringParameters') or {}
            user_id = query_params.get('user_id', 'test-user-123')
            
            if '/status' in path:
                # Get processing status
                file_id = query_params.get('file_id')
                return handle_get_status(file_id, user_id)
            else:
                # Get user files
                return handle_get_files(user_id)
        else:
            return {
                'statusCode': 405,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        logger.error(f"Error in file handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }


def handle_file_upload(body: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Handle file upload request - generate presigned URL"""
    
    try:
        filename = body.get('filename')
        file_size = body.get('file_size', 0)
        subject_id = body.get('subject_id')
        
        if not filename:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Filename is required'})
            }
        
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.txt']
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in allowed_extensions:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': f'File type {file_ext} not supported. Allowed: {", ".join(allowed_extensions)}'
                })
            }
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': f'File size {file_size} exceeds limit of {max_size} bytes'
                })
            }
        
        # Generate file ID and S3 key
        file_id = str(uuid.uuid4())
        s3_key = f"raw-files/user_{user_id}/{file_id}_{filename}"
        
        # Generate presigned URL for upload
        s3_client = boto3.client('s3')
        bucket_name = os.getenv('DOCUMENTS_BUCKET', f'lms-documents-{os.getenv("AWS_ACCOUNT_ID", "default")}-{os.getenv("AWS_REGION", "us-east-1")}')
        
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': s3_key,
                'ContentType': 'application/octet-stream'
            },
            ExpiresIn=3600  # 1 hour
        )
        
        # Store file metadata in DynamoDB
        dynamodb = boto3.resource('dynamodb')
        files_table = dynamodb.Table('lms-user-files')
        
        file_metadata = {
            'file_id': file_id,
            'user_id': user_id,
            'filename': filename,
            's3_key': s3_key,
            'subject_id': subject_id,
            'file_size': file_size,
            'status': 'pending_upload',
            'processing_status': 'pending',
            'text_extraction_status': 'pending',
            'vector_storage_status': 'pending',
            'upload_timestamp': datetime.utcnow().isoformat(),
            'ttl': int((datetime.utcnow() + timedelta(days=365)).timestamp())
        }
        
        files_table.put_item(Item=file_metadata)
        
        logger.info(f"Generated upload URL for file {file_id}: {filename}")
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'file_id': file_id,
                'upload_url': presigned_url,
                'status': 'ready_for_upload',
                'process_url': f'/api/files/process'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in file upload: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }


def handle_file_processing(body: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Handle file processing for RAG after upload"""
    
    try:
        file_id = body.get('file_id')
        if not file_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'file_id is required'})
            }
        
        # Get file metadata
        dynamodb = boto3.resource('dynamodb')
        files_table = dynamodb.Table('lms-user-files')
        
        response = files_table.get_item(Key={'file_id': file_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'File not found'})
            }
        
        file_metadata = response['Item']
        
        # Verify user owns the file
        if file_metadata['user_id'] != user_id:
            return {
                'statusCode': 403,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Access denied'})
            }
        
        # Update status to processing
        update_file_status(files_table, file_id, 'processing_status', 'processing')
        
        # Process the file for RAG
        processing_result = process_file_for_rag(file_metadata)
        
        if processing_result['success']:
            # Update status to completed
            update_file_status(files_table, file_id, 'processing_status', 'completed', {
                'text_extraction_status': 'completed',
                'vector_storage_status': 'completed',
                'chunks_created': processing_result['chunks_created'],
                'vectors_stored': processing_result['vectors_stored'],
                'content_preview': processing_result['content_preview'][:500]
            })
            
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'file_id': file_id,
                    'status': 'completed',
                    'chunks_created': processing_result['chunks_created'],
                    'vectors_stored': processing_result['vectors_stored'],
                    'message': 'File processed successfully for RAG'
                })
            }
        else:
            # Update status to failed
            update_file_status(files_table, file_id, 'processing_status', 'failed', {
                'error_message': processing_result['error']
            })
            
            return {
                'statusCode': 500,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'file_id': file_id,
                    'status': 'failed',
                    'error': processing_result['error']
                })
            }
        
    except Exception as e:
        logger.error(f"Error in file processing: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }


def handle_get_files(user_id: str) -> Dict[str, Any]:
    """Get user's files"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        files_table = dynamodb.Table('lms-user-files')
        
        # Query user's files
        response = files_table.query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id},
            ScanIndexForward=False  # Most recent first
        )
        
        files = response.get('Items', [])
        
        # Format response
        formatted_files = []
        for file_item in files:
            formatted_files.append({
                'file_id': file_item['file_id'],
                'filename': file_item['filename'],
                'file_size': int(file_item.get('file_size', 0)),  # Convert Decimal to int
                'status': file_item.get('status', 'unknown'),
                'processing_status': file_item.get('processing_status', 'pending'),
                'text_extraction_status': file_item.get('text_extraction_status', 'pending'),
                'vector_storage_status': file_item.get('vector_storage_status', 'pending'),
                'upload_timestamp': file_item.get('upload_timestamp'),
                'subject_id': file_item.get('subject_id'),
                'chunks_created': file_item.get('chunks_created', 0),
                'vectors_stored': file_item.get('vectors_stored', 0),
                'content_preview': file_item.get('content_preview', '')[:200]
            })
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'files': formatted_files,
                'total': len(formatted_files)
            })
        }
        
    except Exception as e:
        logger.error(f"Error getting files: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }


def handle_get_status(file_id: str, user_id: str) -> Dict[str, Any]:
    """Get file processing status"""
    
    try:
        if not file_id:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'file_id is required'})
            }
        
        dynamodb = boto3.resource('dynamodb')
        files_table = dynamodb.Table('lms-user-files')
        
        response = files_table.get_item(Key={'file_id': file_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'File not found'})
            }
        
        file_metadata = response['Item']
        
        # Verify user owns the file
        if file_metadata['user_id'] != user_id:
            return {
                'statusCode': 403,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Access denied'})
            }
        
        status_info = {
            'file_id': file_id,
            'filename': file_metadata['filename'],
            'processing_status': file_metadata.get('processing_status', 'pending'),
            'text_extraction_status': file_metadata.get('text_extraction_status', 'pending'),
            'vector_storage_status': file_metadata.get('vector_storage_status', 'pending'),
            'chunks_created': file_metadata.get('chunks_created', 0),
            'vectors_stored': file_metadata.get('vectors_stored', 0),
            'upload_timestamp': file_metadata.get('upload_timestamp'),
            'error_message': file_metadata.get('error_message', '')
        }
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(status_info)
        }
        
    except Exception as e:
        logger.error(f"Error getting file status: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)})
        }


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }

# RAG Processing Functions

def process_file_for_rag(file_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Process file for RAG with enhanced Textract, Comprehend, and Bedrock KB integration"""
    
    try:
        file_id = file_metadata['file_id']
        user_id = file_metadata['user_id']
        filename = file_metadata['filename']
        s3_key = file_metadata['s3_key']
        
        logger.info(f"Starting enhanced RAG processing for file {file_id}: {filename}")
        
        # Step 1: Download and extract text from S3 with Textract and Comprehend
        text_content, extraction_metadata = extract_text_from_s3_file(s3_key, filename)
        if not text_content:
            return {
                'success': False,
                'error': 'Failed to extract text from file'
            }
        
        # Step 2: Chunk the text
        chunks = create_text_chunks(text_content)
        if not chunks:
            return {
                'success': False,
                'error': 'Failed to create text chunks'
            }
        
        # Step 3: Store processed chunks in S3
        chunks_s3_key = f"processed-chunks/user_{user_id}/{file_id}_chunks.json"
        store_chunks_in_s3(chunks_s3_key, chunks, file_metadata, extraction_metadata)
        
        # Step 4: Generate embeddings and store in Pinecone
        vectors_stored = store_vectors_in_pinecone(file_id, user_id, filename, chunks)
        
        # Step 5: Store in Bedrock Knowledge Base with user-specific namespace
        kb_result = store_in_bedrock_knowledge_base(
            file_id, user_id, filename, text_content, chunks, 
            extraction_metadata.get('comprehend_analysis', {}) if extraction_metadata else {}
        )
        
        logger.info(f"Enhanced RAG processing completed for file {file_id}: {len(chunks)} chunks, {vectors_stored} vectors, KB stored: {kb_result['success']}")
        
        processing_result = {
            'success': True,
            'chunks_created': len(chunks),
            'vectors_stored': vectors_stored,
            'content_preview': text_content[:500],
            'processed_s3_key': chunks_s3_key,
            'extraction_method': extraction_metadata.get('extraction_method', 'unknown') if extraction_metadata else 'unknown',
            'bedrock_kb_stored': kb_result['success'],
            'kb_document_id': kb_result.get('kb_document_id')
        }
        
        # Add Textract and Comprehend insights
        if extraction_metadata:
            comprehend_analysis = extraction_metadata.get('comprehend_analysis', {})
            processing_result.update({
                'textract_blocks_detected': extraction_metadata.get('blocks_detected', 0),
                'textract_lines_detected': extraction_metadata.get('lines_detected', 0),
                'textract_words_detected': extraction_metadata.get('words_detected', 0),
                'comprehend_entities_count': len(comprehend_analysis.get('entities', [])),
                'comprehend_key_phrases_count': len(comprehend_analysis.get('key_phrases', [])),
                'comprehend_language': comprehend_analysis.get('language', 'en'),
                'comprehend_sentiment': comprehend_analysis.get('sentiment', {}).get('sentiment') if comprehend_analysis.get('sentiment') else None
            })
        
        # Add KB ingestion job ID if available
        if kb_result.get('ingestion_job_id'):
            processing_result['kb_ingestion_job_id'] = kb_result['ingestion_job_id']
        
        return processing_result
        
    except Exception as e:
        logger.error(f"Error in enhanced RAG processing: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def extract_text_from_s3_file(s3_key: str, filename: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Extract text content from file in S3 with enhanced Textract and Comprehend analysis"""
    
    try:
        from .text_extractor import text_extractor
        
        s3_client = boto3.client('s3')
        bucket_name = os.getenv('DOCUMENTS_BUCKET', f'lms-documents-{os.getenv("AWS_ACCOUNT_ID", "default")}-{os.getenv("AWS_REGION", "us-east-1")}')
        
        # Download file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        file_content = response['Body'].read()
        
        # Extract text using enhanced text extractor (with Textract and Comprehend)
        extraction_result = text_extractor.extract_text(file_content, filename)
        
        if extraction_result['success']:
            # Clean and validate the extracted text
            cleaned_text = text_extractor.clean_extracted_text(extraction_result['text'])
            
            # Validate text quality
            validation = text_extractor.validate_extracted_text(cleaned_text)
            
            # Get Comprehend analysis from extraction result
            comprehend_analysis = extraction_result.get('comprehend_analysis', {})
            
            # Add extraction metadata
            extraction_metadata = {
                'extraction_method': extraction_result.get('extraction_method', 'unknown'),
                'document_type': extraction_result.get('document_type', 'unknown'),
                'blocks_detected': extraction_result.get('blocks_detected', 0),
                'lines_detected': extraction_result.get('lines_detected', 0),
                'words_detected': extraction_result.get('words_detected', 0),
                'comprehend_analysis': comprehend_analysis,
                'validation': validation
            }
            
            if validation['is_valid']:
                logger.info(f"Successfully extracted text from {filename} using {extraction_result.get('extraction_method', 'unknown')}: {validation['statistics']}")
                logger.info(f"Comprehend analysis: {len(comprehend_analysis.get('entities', []))} entities, {len(comprehend_analysis.get('key_phrases', []))} key phrases")
                return cleaned_text, extraction_metadata
            else:
                logger.warning(f"Text extraction quality issues for {filename}: {validation['warnings']}")
                return cleaned_text, extraction_metadata  # Return anyway, but log warnings
        else:
            logger.error(f"Text extraction failed for {filename}: {extraction_result['error']}")
            return None, None
            
    except Exception as e:
        logger.error(f"Error extracting text from S3 file {s3_key}: {str(e)}")
        return None, None


def create_text_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks for RAG"""
    
    # Return empty list for empty text
    if not text or not text.strip():
        return []
    
    if len(text) <= chunk_size:
        return [{
            'index': 0,
            'text': text,
            'start_pos': 0,
            'end_pos': len(text),
            'length': len(text)
        }]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings near the chunk boundary
            for i in range(end, max(start + chunk_size - 100, start), -1):
                if text[i] in '.!?\n':
                    end = i + 1
                    break
        
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({
                'index': len(chunks),
                'text': chunk_text,
                'start_pos': start,
                'end_pos': end,
                'length': len(chunk_text)
            })
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def store_chunks_in_s3(s3_key: str, chunks: List[Dict[str, Any]], file_metadata: Dict[str, Any], 
                      extraction_metadata: Dict[str, Any] = None) -> bool:
    """Store processed chunks in S3 with enhanced metadata"""
    
    try:
        s3_client = boto3.client('s3')
        bucket_name = os.getenv('DOCUMENTS_BUCKET', f'lms-documents-{os.getenv("AWS_ACCOUNT_ID", "default")}-{os.getenv("AWS_REGION", "us-east-1")}')
        
        chunks_data = {
            'file_id': file_metadata['file_id'],
            'filename': file_metadata['filename'],
            'user_id': file_metadata['user_id'],
            'processed_at': datetime.utcnow().isoformat(),
            'total_chunks': len(chunks),
            'chunks': chunks
        }
        
        # Add extraction metadata if available
        if extraction_metadata:
            chunks_data['extraction_metadata'] = extraction_metadata
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(chunks_data, indent=2),
            ContentType='application/json',
            Metadata={
                'user_id': file_metadata['user_id'],
                'file_id': file_metadata['file_id'],
                'total_chunks': str(len(chunks)),
                'extraction_method': extraction_metadata.get('extraction_method', 'unknown') if extraction_metadata else 'unknown'
            }
        )
        
        logger.info(f"Stored {len(chunks)} chunks in S3: {s3_key}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing chunks in S3: {str(e)}")
        return False


def store_in_bedrock_knowledge_base(file_id: str, user_id: str, filename: str, 
                                  text_content: str, chunks: List[Dict[str, Any]],
                                  comprehend_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
    """Store document in Bedrock Knowledge Base with user-specific namespace"""
    
    try:
        from .bedrock_kb_manager import bedrock_kb_manager
        
        # Store document in Bedrock Knowledge Base
        kb_result = bedrock_kb_manager.store_document_in_kb(
            file_id=file_id,
            user_id=user_id,
            filename=filename,
            text_content=text_content,
            chunks=chunks,
            comprehend_analysis=comprehend_analysis
        )
        
        if kb_result['success']:
            logger.info(f"Successfully stored document in Bedrock KB: {kb_result['kb_document_id']}")
        else:
            logger.warning(f"Failed to store document in Bedrock KB: {kb_result['error']}")
        
        return kb_result
        
    except Exception as e:
        logger.error(f"Error storing document in Bedrock KB: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'kb_document_id': None
        }


def store_vectors_in_pinecone(file_id: str, user_id: str, filename: str, chunks: List[Dict[str, Any]]) -> int:
    """Generate embeddings and store vectors in Pinecone"""
    
    try:
        from .vector_storage import vector_storage
        
        # Use mock embeddings in Lambda environment (for now)
        use_mock = os.getenv('USE_MOCK_EMBEDDINGS', 'true').lower() == 'true'
        
        vectors_stored = vector_storage.store_document_vectors(
            file_id=file_id,
            user_id=user_id,
            filename=filename,
            text_chunks=chunks,
            subject_id=None,  # Will be added later when subject context is available
            use_mock_embeddings=use_mock
        )
        
        logger.info(f"Stored {vectors_stored} vectors for file {file_id}")
        return vectors_stored
        
    except Exception as e:
        logger.error(f"Error storing vectors in Pinecone: {str(e)}")
        return 0


def update_file_status(files_table, file_id: str, status_field: str, status_value: str, additional_data: Dict[str, Any] = None) -> bool:
    """Update file processing status in DynamoDB"""
    
    try:
        update_expression = f"SET {status_field} = :status, updated_at = :updated"
        expression_values = {
            ':status': status_value,
            ':updated': datetime.utcnow().isoformat()
        }
        
        # Add additional data to update
        if additional_data:
            for key, value in additional_data.items():
                if key != 'updated_at':  # Avoid duplicate
                    update_expression += f", {key} = :{key}"
                    expression_values[f":{key}"] = value
        
        files_table.update_item(
            Key={'file_id': file_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        logger.info(f"Updated file {file_id}: {status_field} = {status_value}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating file status: {str(e)}")
        return False


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }