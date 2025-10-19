"""
FastFileProcessor - Main File Processing Class

This module implements the core file processing functionality for the LMS system,
including file upload, validation, text extraction, and metadata management.
"""

import os
import uuid
import logging
import mimetypes
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from src.shared.config import config
from src.file_processor.text_extractor import AdvancedTextExtractor
from src.file_processor.knowledge_base_manager import KnowledgeBaseManager

logger = logging.getLogger(__name__)

class FileProcessingError(Exception):
    """Base exception for file processing errors"""
    pass

class UnsupportedFileTypeError(FileProcessingError):
    """Raised when file type is not supported"""
    pass

class FileTooLargeError(FileProcessingError):
    """Raised when file exceeds size limit"""
    pass

class FileValidationError(FileProcessingError):
    """Raised when file validation fails"""
    pass

class ProcessResult:
    """Result object for file processing operations"""
    
    def __init__(self, success: bool, file_id: str = None, message: str = "", 
                 error: str = None, data: Dict[str, Any] = None):
        self.success = success
        self.file_id = file_id
        self.message = message
        self.error = error
        self.data = data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'success': self.success,
            'file_id': self.file_id,
            'message': self.message,
            'error': self.error,
            'data': self.data
        }

class FastFileProcessor:
    """
    Main file processing class for the LMS system.
    
    Handles file upload, validation, text extraction, and metadata management
    with integration to AWS S3, DynamoDB, and Bedrock Knowledge Base.
    """
    
    # Supported file types and their MIME types
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
    SUPPORTED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    }
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = config.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes
    
    def __init__(self, user_id: str = "demo_user"):
        """
        Initialize the FastFileProcessor.
        
        Args:
            user_id: User identifier for file organization
        """
        self.user_id = user_id
        
        try:
            # Initialize AWS clients
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            
            self.dynamodb = boto3.resource(
                'dynamodb',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            
            self.bedrock_agent = boto3.client(
                'bedrock-agent',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            
            # Initialize text extractor and knowledge base manager
            self.text_extractor = AdvancedTextExtractor()
            self.kb_manager = KnowledgeBaseManager(self.user_id)
            
            # Configuration
            self.bucket_name = config.S3_BUCKET_NAME
            self.metadata_table_name = config.FILE_METADATA_TABLE
            self.kb_id = config.KNOWLEDGE_BASE_ID
            
            # Get DynamoDB table
            self.metadata_table = self.dynamodb.Table(self.metadata_table_name)
            
            logger.info(f"FastFileProcessor initialized for user: {self.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize FastFileProcessor: {e}")
            raise FileProcessingError(f"Initialization failed: {e}")
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate file before processing.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Dictionary with validation results
            
        Raises:
            FileValidationError: If validation fails
        """
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                raise FileValidationError(f"File does not exist: {file_path}")
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.MAX_FILE_SIZE:
                raise FileTooLargeError(
                    f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds limit "
                    f"({config.MAX_FILE_SIZE_MB}MB)"
                )
            
            # Check file extension
            file_extension = file_path.suffix.lower()
            if file_extension not in self.SUPPORTED_EXTENSIONS:
                raise UnsupportedFileTypeError(
                    f"File type '{file_extension}' not supported. "
                    f"Supported types: {', '.join(self.SUPPORTED_EXTENSIONS)}"
                )
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if mime_type and mime_type not in self.SUPPORTED_MIME_TYPES:
                logger.warning(f"MIME type '{mime_type}' not in supported list")
            
            # Basic file integrity check
            try:
                with open(file_path, 'rb') as f:
                    # Read first few bytes to ensure file is readable
                    f.read(1024)
            except Exception as e:
                raise FileValidationError(f"File appears to be corrupted: {e}")
            
            validation_result = {
                'valid': True,
                'file_size': file_size,
                'file_extension': file_extension,
                'mime_type': mime_type,
                'file_name': file_path.name
            }
            
            logger.info(f"File validation passed: {file_path.name}")
            return validation_result
            
        except (FileValidationError, UnsupportedFileTypeError, FileTooLargeError):
            raise
        except Exception as e:
            raise FileValidationError(f"Validation error: {e}")
    
    def generate_file_id(self) -> str:
        """Generate unique file ID"""
        return str(uuid.uuid4())
    
    def generate_s3_key(self, file_id: str, original_filename: str, folder: str = "raw") -> str:
        """
        Generate S3 key for file storage.
        
        Args:
            file_id: Unique file identifier
            original_filename: Original filename
            folder: Storage folder (raw, processed, metadata)
            
        Returns:
            S3 key string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in original_filename if c.isalnum() or c in '._-')
        return f"users/{self.user_id}/{folder}/{timestamp}_{file_id}_{safe_filename}"
    
    def create_file_metadata(self, file_id: str, file_path: str, 
                           validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create metadata record for uploaded file.
        
        Args:
            file_id: Unique file identifier
            file_path: Path to the uploaded file
            validation_result: File validation results
            
        Returns:
            File metadata dictionary
        """
        now = datetime.now()
        
        metadata = {
            'file_id': file_id,
            'user_id': self.user_id,
            'original_filename': validation_result['file_name'],
            'file_size': validation_result['file_size'],
            'file_type': validation_result['mime_type'] or 'unknown',
            'file_extension': validation_result['file_extension'],
            'upload_timestamp': now.isoformat(),
            'processing_status': 'uploaded',
            'text_extraction_status': 'pending',
            'kb_indexing_status': 'pending',
            'created_at': now.isoformat(),
            'updated_at': now.isoformat(),
            'error_messages': [],
            'processing_duration': 0,
            'content_preview': '',
            'extracted_concepts': []
        }
        
        return metadata
    
    def save_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Save file metadata to DynamoDB.
        
        Args:
            metadata: File metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.metadata_table.put_item(Item=metadata)
            logger.info(f"Metadata saved for file: {metadata['file_id']}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to save metadata: {e}")
            return False
    
    def update_file_status(self, file_id: str, status_field: str, 
                          status_value: str, additional_data: Dict[str, Any] = None) -> bool:
        """
        Update file processing status in DynamoDB.
        
        Args:
            file_id: File identifier
            status_field: Status field to update
            status_value: New status value
            additional_data: Additional data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_expression = f"SET {status_field} = :status, updated_at = :updated"
            expression_values = {
                ':status': status_value,
                ':updated': datetime.now().isoformat()
            }
            
            # Add additional data to update (avoid duplicate updated_at)
            if additional_data:
                for key, value in additional_data.items():
                    if key != 'updated_at':  # Avoid duplicate path
                        update_expression += f", {key} = :{key}"
                        expression_values[f":{key}"] = value
            
            self.metadata_table.update_item(
                Key={'file_id': file_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            logger.info(f"Status updated for file {file_id}: {status_field} = {status_value}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update file status: {e}")
            return False
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve file metadata from DynamoDB.
        
        Args:
            file_id: File identifier
            
        Returns:
            File metadata dictionary or None if not found
        """
        try:
            response = self.metadata_table.get_item(Key={'file_id': file_id})
            return response.get('Item')
            
        except ClientError as e:
            logger.error(f"Failed to get file metadata: {e}")
            return None
    
    def list_user_files(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List files for the current user.
        
        Args:
            limit: Maximum number of files to return
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            response = self.metadata_table.query(
                IndexName='user-id-index',
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': self.user_id},
                ScanIndexForward=False,  # Sort by timestamp descending
                Limit=limit
            )
            
            return response.get('Items', [])
            
        except ClientError as e:
            logger.error(f"Failed to list user files: {e}")
            return []
    
    def delete_file(self, file_id: str) -> ProcessResult:
        """
        Delete file and its metadata.
        
        Args:
            file_id: File identifier
            
        Returns:
            ProcessResult with operation status
        """
        try:
            # Get file metadata
            metadata = self.get_file_metadata(file_id)
            if not metadata:
                return ProcessResult(
                    success=False,
                    error=f"File not found: {file_id}"
                )
            
            # Delete from S3 if s3_key exists
            if 's3_key' in metadata:
                try:
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=metadata['s3_key']
                    )
                    logger.info(f"Deleted S3 object: {metadata['s3_key']}")
                except ClientError as e:
                    logger.warning(f"Failed to delete S3 object: {e}")
            
            # Delete processed files if they exist
            if 'processed_s3_key' in metadata:
                try:
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=metadata['processed_s3_key']
                    )
                    logger.info(f"Deleted processed S3 object: {metadata['processed_s3_key']}")
                except ClientError as e:
                    logger.warning(f"Failed to delete processed S3 object: {e}")
            
            # Delete metadata from DynamoDB
            self.metadata_table.delete_item(Key={'file_id': file_id})
            
            return ProcessResult(
                success=True,
                file_id=file_id,
                message=f"File '{metadata['original_filename']}' deleted successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return ProcessResult(
                success=False,
                error=f"Delete failed: {e}"
            )
    
    def get_processing_status(self, file_id: str) -> Dict[str, Any]:
        """
        Get detailed processing status for a file.
        
        Args:
            file_id: File identifier
            
        Returns:
            Processing status dictionary
        """
        metadata = self.get_file_metadata(file_id)
        if not metadata:
            return {'error': 'File not found'}
        
        return {
            'file_id': file_id,
            'filename': metadata.get('original_filename', 'Unknown'),
            'processing_status': metadata.get('processing_status', 'unknown'),
            'text_extraction_status': metadata.get('text_extraction_status', 'unknown'),
            'kb_indexing_status': metadata.get('kb_indexing_status', 'unknown'),
            'upload_timestamp': metadata.get('upload_timestamp', ''),
            'processing_duration': metadata.get('processing_duration', 0),
            'error_messages': metadata.get('error_messages', []),
            'content_preview': metadata.get('content_preview', '')
        }
    
    def upload_file_to_s3(self, file_path: str, file_id: str, 
                          validation_result: Dict[str, Any]) -> ProcessResult:
        """
        Upload file to S3 with proper organization and metadata.
        
        Args:
            file_path: Path to the file to upload
            file_id: Unique file identifier
            validation_result: File validation results
            
        Returns:
            ProcessResult with upload status and S3 key
        """
        try:
            # Generate S3 key for raw file
            s3_key = self.generate_s3_key(
                file_id, 
                validation_result['file_name'], 
                "raw"
            )
            
            # Prepare metadata for S3 object
            s3_metadata = {
                'file-id': file_id,
                'user-id': self.user_id,
                'original-filename': validation_result['file_name'],
                'file-size': str(validation_result['file_size']),
                'upload-timestamp': datetime.now().isoformat()
            }
            
            # Upload file to S3
            with open(file_path, 'rb') as file_obj:
                self.s3_client.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        'Metadata': s3_metadata,
                        'ContentType': validation_result.get('mime_type', 'application/octet-stream')
                    }
                )
            
            logger.info(f"File uploaded to S3: {s3_key}")
            
            return ProcessResult(
                success=True,
                file_id=file_id,
                message=f"File uploaded successfully to {s3_key}",
                data={'s3_key': s3_key}
            )
            
        except ClientError as e:
            error_msg = f"S3 upload failed: {e}"
            logger.error(error_msg)
            return ProcessResult(
                success=False,
                file_id=file_id,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Upload error: {e}"
            logger.error(error_msg)
            return ProcessResult(
                success=False,
                file_id=file_id,
                error=error_msg
            )
    
    def download_file_from_s3(self, s3_key: str, local_path: str) -> bool:
        """
        Download file from S3 to local path.
        
        Args:
            s3_key: S3 object key
            local_path: Local file path to save to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"File downloaded from S3: {s3_key} -> {local_path}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False
    
    def get_s3_file_info(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Get S3 object information.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            S3 object metadata or None if not found
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat(),
                'content_type': response.get('ContentType', 'unknown'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"Failed to get S3 object info: {e}")
            return None
    
    def process_file_upload(self, file_path: str) -> ProcessResult:
        """
        Complete file upload process including validation, S3 upload, and metadata storage.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            ProcessResult with complete processing status
        """
        start_time = datetime.now()
        file_id = self.generate_file_id()
        
        try:
            # Step 1: Validate file
            logger.info(f"Starting file upload process for: {file_path}")
            validation_result = self.validate_file(file_path)
            
            # Step 2: Create initial metadata
            metadata = self.create_file_metadata(file_id, file_path, validation_result)
            
            # Step 3: Save initial metadata
            if not self.save_metadata(metadata):
                return ProcessResult(
                    success=False,
                    file_id=file_id,
                    error="Failed to save initial metadata"
                )
            
            # Step 4: Upload to S3
            self.update_file_status(file_id, 'processing_status', 'uploading')
            
            upload_result = self.upload_file_to_s3(file_path, file_id, validation_result)
            if not upload_result.success:
                self.handle_error(file_id, Exception(upload_result.error))
                return upload_result
            
            # Step 5: Update metadata with S3 information
            processing_duration = (datetime.now() - start_time).total_seconds()
            
            self.update_file_status(
                file_id,
                'processing_status',
                'uploaded',
                {
                    's3_key': upload_result.data['s3_key'],
                    'processing_duration': int(processing_duration)
                }
            )
            
            logger.info(f"File upload completed successfully: {file_id}")
            
            return ProcessResult(
                success=True,
                file_id=file_id,
                message=f"File '{validation_result['file_name']}' uploaded successfully",
                data={
                    's3_key': upload_result.data['s3_key'],
                    'processing_duration': processing_duration,
                    'file_size': validation_result['file_size']
                }
            )
            
        except (FileValidationError, UnsupportedFileTypeError, FileTooLargeError) as e:
            self.handle_error(file_id, e)
            return ProcessResult(
                success=False,
                file_id=file_id,
                error=str(e)
            )
        except Exception as e:
            self.handle_error(file_id, e)
            return ProcessResult(
                success=False,
                file_id=file_id,
                error=f"Upload process failed: {e}"
            )
    
    def search_user_files(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search user files by filename or content.
        
        Args:
            search_term: Term to search for
            limit: Maximum number of results
            
        Returns:
            List of matching file metadata
        """
        try:
            # Get all user files
            all_files = self.list_user_files(limit=100)
            
            # Filter by search term (case-insensitive)
            search_term_lower = search_term.lower()
            matching_files = []
            
            for file_info in all_files:
                # Search in filename
                filename = file_info.get('original_filename', '').lower()
                content_preview = file_info.get('content_preview', '').lower()
                concepts = [c.lower() for c in file_info.get('extracted_concepts', [])]
                
                if (search_term_lower in filename or 
                    search_term_lower in content_preview or
                    any(search_term_lower in concept for concept in concepts)):
                    matching_files.append(file_info)
                
                if len(matching_files) >= limit:
                    break
            
            return matching_files
            
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return []
    
    def get_files_by_status(self, status: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get files by processing status.
        
        Args:
            status: Processing status to filter by
            limit: Maximum number of files to return
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            response = self.metadata_table.query(
                IndexName='status-index',
                KeyConditionExpression='processing_status = :status',
                ExpressionAttributeValues={':status': status},
                ScanIndexForward=False,
                Limit=limit
            )
            
            return response.get('Items', [])
            
        except ClientError as e:
            logger.error(f"Failed to get files by status: {e}")
            return []
    
    def get_user_file_statistics(self) -> Dict[str, Any]:
        """
        Get file statistics for the current user.
        
        Returns:
            Dictionary with file statistics
        """
        try:
            files = self.list_user_files(limit=1000)  # Get more files for stats
            
            if not files:
                return {
                    'total_files': 0,
                    'total_size': 0,
                    'file_types': {},
                    'status_counts': {},
                    'recent_uploads': 0
                }
            
            # Calculate statistics
            total_files = len(files)
            total_size = sum(f.get('file_size', 0) for f in files)
            
            # File type distribution
            file_types = {}
            for file_info in files:
                ext = Path(file_info.get('original_filename', '')).suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
            
            # Status distribution
            status_counts = {}
            for file_info in files:
                status = file_info.get('processing_status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Recent uploads (last 24 hours)
            from datetime import datetime, timedelta
            recent_cutoff = (datetime.now() - timedelta(days=1)).isoformat()
            recent_uploads = sum(1 for f in files 
                               if f.get('upload_timestamp', '') > recent_cutoff)
            
            return {
                'total_files': total_files,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_types': file_types,
                'status_counts': status_counts,
                'recent_uploads': recent_uploads,
                'average_file_size': round(total_size / total_files) if total_files > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get file statistics: {e}")
            return {'error': str(e)}
    
    def update_file_content_preview(self, file_id: str, content_preview: str, 
                                  concepts: List[str] = None) -> bool:
        """
        Update file content preview and extracted concepts.
        
        Args:
            file_id: File identifier
            content_preview: Preview of file content
            concepts: List of extracted concepts
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {'content_preview': content_preview[:500]}  # Limit preview size
            
            if concepts:
                update_data['extracted_concepts'] = concepts[:20]  # Limit concepts
            
            return self.update_file_status(
                file_id,
                'text_extraction_status',
                'success',
                update_data
            )
            
        except Exception as e:
            logger.error(f"Failed to update content preview: {e}")
            return False
    
    def get_upload_progress(self, file_id: str) -> Dict[str, Any]:
        """
        Get upload progress for a file.
        
        Args:
            file_id: File identifier
            
        Returns:
            Progress information dictionary
        """
        metadata = self.get_file_metadata(file_id)
        if not metadata:
            return {'error': 'File not found'}
        
        status = metadata.get('processing_status', 'unknown')
        
        progress_map = {
            'uploaded': 100,
            'uploading': 50,
            'processing': 75,
            'completed': 100,
            'failed': 0
        }
        
        return {
            'file_id': file_id,
            'filename': metadata.get('original_filename', 'Unknown'),
            'status': status,
            'progress_percent': progress_map.get(status, 0),
            'upload_timestamp': metadata.get('upload_timestamp', ''),
            'file_size': metadata.get('file_size', 0),
            'error_messages': metadata.get('error_messages', [])
        }
    
    def extract_text_from_file(self, file_path: str, file_id: str) -> ProcessResult:
        """
        Extract text from uploaded file.
        
        Args:
            file_path: Path to the file
            file_id: File identifier
            
        Returns:
            ProcessResult with extraction status and text content
        """
        try:
            logger.info(f"Starting text extraction for file: {file_id}")
            
            # Update status to processing
            self.update_file_status(file_id, 'text_extraction_status', 'processing')
            
            # Extract text using the text extractor
            extraction_result = self.text_extractor.extract_text(file_path)
            
            if extraction_result.success:
                # Clean and process the text
                cleaned_text = self.text_extractor.clean_and_normalize_text(extraction_result.text)
                
                # Extract concepts
                concepts = self.text_extractor.extract_concepts_and_keywords(cleaned_text, max_concepts=15)
                
                # Create content preview (first 500 characters)
                content_preview = cleaned_text[:500] if cleaned_text else ""
                
                # Update metadata with extracted content
                self.update_file_status(
                    file_id,
                    'text_extraction_status',
                    'success',
                    {
                        'content_preview': content_preview,
                        'extracted_concepts': concepts,
                        'extraction_metadata': extraction_result.metadata
                    }
                )
                
                logger.info(f"Text extraction completed for file: {file_id}")
                
                return ProcessResult(
                    success=True,
                    file_id=file_id,
                    message="Text extraction completed successfully",
                    data={
                        'extracted_text': cleaned_text,
                        'content_preview': content_preview,
                        'concepts': concepts,
                        'word_count': extraction_result.word_count,
                        'char_count': extraction_result.char_count,
                        'extraction_method': extraction_result.extraction_method
                    }
                )
            else:
                # Update status to failed
                self.update_file_status(
                    file_id,
                    'text_extraction_status',
                    'failed',
                    {'error_messages': [extraction_result.error]}
                )
                
                return ProcessResult(
                    success=False,
                    file_id=file_id,
                    error=f"Text extraction failed: {extraction_result.error}"
                )
                
        except Exception as e:
            error_msg = f"Text extraction error: {e}"
            logger.error(error_msg)
            
            self.update_file_status(
                file_id,
                'text_extraction_status',
                'failed',
                {'error_messages': [error_msg]}
            )
            
            return ProcessResult(
                success=False,
                file_id=file_id,
                error=error_msg
            )
    
    def save_processed_text(self, file_id: str, text_content: str) -> ProcessResult:
        """
        Save processed text to S3 for Knowledge Base indexing.
        
        Args:
            file_id: File identifier
            text_content: Processed text content
            
        Returns:
            ProcessResult with save status
        """
        try:
            # Generate S3 key for processed text
            processed_s3_key = f"users/{self.user_id}/processed/{file_id}_extracted.txt"
            
            # Save processed text to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=processed_s3_key,
                Body=text_content.encode('utf-8'),
                ContentType='text/plain',
                Metadata={
                    'file-id': file_id,
                    'user-id': self.user_id,
                    'content-type': 'extracted-text',
                    'processing-timestamp': datetime.now().isoformat()
                }
            )
            
            # Update metadata with processed text location
            self.update_file_status(
                file_id,
                'processing_status',
                'text_extracted',
                {'processed_s3_key': processed_s3_key}
            )
            
            logger.info(f"Processed text saved to S3: {processed_s3_key}")
            
            return ProcessResult(
                success=True,
                file_id=file_id,
                message="Processed text saved successfully",
                data={'processed_s3_key': processed_s3_key}
            )
            
        except Exception as e:
            error_msg = f"Failed to save processed text: {e}"
            logger.error(error_msg)
            return ProcessResult(
                success=False,
                file_id=file_id,
                error=error_msg
            )
    
    def process_file_complete_workflow(self, file_path: str) -> ProcessResult:
        """
        Complete file processing workflow including upload, text extraction, and processing.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            ProcessResult with complete processing status
        """
        start_time = datetime.now()
        file_id = self.generate_file_id()
        
        try:
            logger.info(f"Starting complete file processing workflow for: {file_path}")
            
            # Step 1: Upload file (existing functionality)
            upload_result = self.process_file_upload(file_path)
            if not upload_result.success:
                return upload_result
            
            file_id = upload_result.file_id
            
            # Step 2: Extract text from uploaded file
            extraction_result = self.extract_text_from_file(file_path, file_id)
            if not extraction_result.success:
                return extraction_result
            
            # Step 3: Save processed text to S3
            extracted_text = extraction_result.data.get('extracted_text', '')
            if extracted_text:
                save_result = self.save_processed_text(file_id, extracted_text)
                if not save_result.success:
                    logger.warning(f"Failed to save processed text: {save_result.error}")
            
            # Step 4: Index in Knowledge Base
            kb_indexing_result = None
            if extracted_text:
                try:
                    # Get file metadata for KB indexing
                    file_metadata = self.get_file_metadata(file_id)
                    if file_metadata:
                        kb_indexing_result = self.kb_manager.index_document(
                            file_id, 
                            extracted_text, 
                            file_metadata
                        )
                        
                        if kb_indexing_result.success:
                            self.update_file_status(
                                file_id,
                                'kb_indexing_status',
                                'indexed',
                                {
                                    'kb_document_id': kb_indexing_result.document_id,
                                    'kb_chunks': kb_indexing_result.data.get('chunk_count', 0)
                                }
                            )
                            logger.info(f"Document indexed in Knowledge Base: {file_id}")
                        else:
                            self.update_file_status(
                                file_id,
                                'kb_indexing_status',
                                'failed',
                                {'kb_error': kb_indexing_result.error}
                            )
                            logger.warning(f"KB indexing failed: {kb_indexing_result.error}")
                except Exception as e:
                    logger.warning(f"KB indexing error: {e}")
                    self.update_file_status(
                        file_id,
                        'kb_indexing_status',
                        'failed',
                        {'kb_error': str(e)}
                    )
            
            # Step 5: Update final status
            processing_duration = (datetime.now() - start_time).total_seconds()
            
            final_status = 'completed' if (extraction_result.success and 
                                         (not kb_indexing_result or kb_indexing_result.success)) else 'completed_with_warnings'
            
            self.update_file_status(
                file_id,
                'processing_status',
                final_status,
                {
                    'processing_duration': int(processing_duration)
                }
            )
            
            logger.info(f"Complete file processing workflow completed: {file_id}")
            
            return ProcessResult(
                success=True,
                file_id=file_id,
                message="File processing completed successfully",
                data={
                    'upload_data': upload_result.data,
                    'extraction_data': extraction_result.data,
                    'kb_indexing_data': kb_indexing_result.data if kb_indexing_result and kb_indexing_result.success else None,
                    'kb_indexing_error': kb_indexing_result.error if kb_indexing_result and not kb_indexing_result.success else None,
                    'processing_duration': processing_duration
                }
            )
            
        except Exception as e:
            error_msg = f"Complete workflow failed: {e}"
            logger.error(error_msg)
            
            if file_id:
                self.handle_error(file_id, e)
            
            return ProcessResult(
                success=False,
                file_id=file_id,
                error=error_msg
            )
    
    def handle_error(self, file_id: str, error: Exception, 
                    status_field: str = 'processing_status') -> None:
        """
        Handle and log processing errors.
        
        Args:
            file_id: File identifier
            error: Exception that occurred
            status_field: Status field to update
        """
        error_message = f"{type(error).__name__}: {str(error)}"
        
        # Update file status to failed
        self.update_file_status(
            file_id, 
            status_field, 
            'failed',
            {
                'error_messages': [error_message]
            }
        )
        
        logger.error(f"Processing error for file {file_id}: {error_message}")

def main():
    """Test function for FastFileProcessor"""
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing FastFileProcessor Class")
    print("=" * 50)
    
    try:
        # Initialize processor
        processor = FastFileProcessor("test_user")
        print("✅ FastFileProcessor initialized successfully")
        
        # Test file validation (using a dummy file path for demo)
        print("\n📋 Testing file validation...")
        
        # Test listing user files
        print("\n📚 Testing file listing...")
        files = processor.list_user_files()
        print(f"Found {len(files)} files for user")
        
        # Test processing status
        print("\n📊 Testing status retrieval...")
        if files:
            status = processor.get_processing_status(files[0]['file_id'])
            print(f"Status for first file: {status}")
        
        print("\n🎉 FastFileProcessor tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()