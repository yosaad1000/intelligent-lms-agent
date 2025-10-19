"""
Knowledge Base Manager for File Processor Microservice

This module handles integration with Amazon Bedrock Knowledge Base,
including document indexing, synchronization, and management.
"""

import os
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import tempfile

import boto3
from botocore.exceptions import ClientError

from src.shared.config import config

logger = logging.getLogger(__name__)

class KnowledgeBaseError(Exception):
    """Base exception for Knowledge Base operations"""
    pass

class DocumentIndexingError(KnowledgeBaseError):
    """Document indexing specific error"""
    pass

class SyncError(KnowledgeBaseError):
    """Synchronization specific error"""
    pass

class IndexingResult:
    """Result object for document indexing operations"""
    
    def __init__(self, success: bool, document_id: str = None, message: str = "",
                 error: str = None, data: Dict[str, Any] = None):
        self.success = success
        self.document_id = document_id
        self.message = message
        self.error = error
        self.data = data or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'success': self.success,
            'document_id': self.document_id,
            'message': self.message,
            'error': self.error,
            'data': self.data
        }

class KnowledgeBaseManager:
    """
    Manages Amazon Bedrock Knowledge Base operations for document indexing,
    synchronization, and retrieval.
    """
    
    def __init__(self, user_id: str = "demo_user"):
        """
        Initialize the Knowledge Base Manager.
        
        Args:
            user_id: User identifier for document organization
        """
        self.user_id = user_id
        
        try:
            # Initialize AWS clients
            self.bedrock_agent = boto3.client(
                'bedrock-agent',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            
            # Configuration
            self.bucket_name = config.S3_BUCKET_NAME
            self.kb_id = config.KNOWLEDGE_BASE_ID
            
            logger.info(f"KnowledgeBaseManager initialized for user: {self.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize KnowledgeBaseManager: {e}")
            raise KnowledgeBaseError(f"Initialization failed: {e}")
    
    def prepare_document_for_indexing(self, file_id: str, text_content: str, 
                                    metadata: Dict[str, Any]) -> IndexingResult:
        """
        Prepare document for Knowledge Base indexing by creating properly formatted content.
        
        Args:
            file_id: Unique file identifier
            text_content: Processed text content
            metadata: Document metadata
            
        Returns:
            IndexingResult with preparation status
        """
        try:
            # Create document metadata for Knowledge Base
            kb_metadata = {
                'file_id': file_id,
                'user_id': self.user_id,
                'filename': metadata.get('original_filename', 'unknown'),
                'file_type': metadata.get('file_type', 'unknown'),
                'upload_date': metadata.get('upload_timestamp', datetime.now().isoformat()),
                'concepts': metadata.get('extracted_concepts', []),
                'word_count': len(text_content.split()) if text_content else 0,
                'char_count': len(text_content) if text_content else 0
            }
            
            # Create structured document for indexing
            document_content = {
                'title': metadata.get('original_filename', f'Document {file_id}'),
                'content': text_content,
                'metadata': kb_metadata,
                'source': f"user_upload_{self.user_id}",
                'document_id': file_id
            }
            
            # Save structured document to S3 for Knowledge Base ingestion
            kb_s3_key = f"processed/knowledge_base/{self.user_id}/{file_id}.json"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=kb_s3_key,
                Body=json.dumps(document_content, indent=2),
                ContentType='application/json',
                Metadata={
                    'document-id': file_id,
                    'user-id': self.user_id,
                    'content-type': 'knowledge-base-document',
                    'preparation-timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Document prepared for indexing: {kb_s3_key}")
            
            return IndexingResult(
                success=True,
                document_id=file_id,
                message="Document prepared for Knowledge Base indexing",
                data={
                    'kb_s3_key': kb_s3_key,
                    'document_content': document_content,
                    'metadata': kb_metadata
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to prepare document for indexing: {e}"
            logger.error(error_msg)
            return IndexingResult(
                success=False,
                document_id=file_id,
                error=error_msg
            )
    
    def chunk_text_for_embeddings(self, text_content: str, chunk_size: int = 1000,
                                 overlap: int = 100) -> List[Dict[str, Any]]:
        """
        Chunk text content optimally for embedding generation.
        
        Args:
            text_content: Text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks for context preservation
            
        Returns:
            List of text chunks with metadata
        """
        if not text_content:
            return []
        
        try:
            # Split into sentences for better chunking
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text_content)
            
            chunks = []
            current_chunk = ""
            current_size = 0
            
            for sentence in sentences:
                sentence_size = len(sentence)
                
                # If adding this sentence would exceed the limit
                if current_size + sentence_size > chunk_size and current_chunk:
                    # Save current chunk
                    chunk_data = {
                        'text': current_chunk.strip(),
                        'size': current_size,
                        'chunk_index': len(chunks),
                        'word_count': len(current_chunk.split()),
                        'start_position': len(chunks) * (chunk_size - overlap) if chunks else 0
                    }
                    chunks.append(chunk_data)
                    
                    # Start new chunk with overlap
                    if overlap > 0 and current_chunk:
                        overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                        current_chunk = overlap_text + " " + sentence
                        current_size = len(current_chunk)
                    else:
                        current_chunk = sentence
                        current_size = sentence_size
                else:
                    # Add sentence to current chunk
                    if current_chunk:
                        current_chunk += " " + sentence
                        current_size += sentence_size + 1  # +1 for space
                    else:
                        current_chunk = sentence
                        current_size = sentence_size
            
            # Add final chunk if it exists
            if current_chunk.strip():
                chunk_data = {
                    'text': current_chunk.strip(),
                    'size': len(current_chunk),
                    'chunk_index': len(chunks),
                    'word_count': len(current_chunk.split()),
                    'start_position': len(chunks) * (chunk_size - overlap) if chunks else 0
                }
                chunks.append(chunk_data)
            
            logger.info(f"Text chunked into {len(chunks)} chunks for embeddings")
            return chunks
            
        except Exception as e:
            logger.error(f"Text chunking failed: {e}")
            # Return single chunk as fallback
            return [{
                'text': text_content,
                'size': len(text_content),
                'chunk_index': 0,
                'word_count': len(text_content.split()),
                'start_position': 0
            }]
    
    def create_data_source_if_needed(self) -> Optional[str]:
        """
        Create Knowledge Base data source if it doesn't exist.
        
        Returns:
            Data source ID if successful, None otherwise
        """
        try:
            # Check if Knowledge Base exists
            if not self.kb_id:
                logger.warning("No Knowledge Base ID configured")
                return None
            
            # List existing data sources
            try:
                response = self.bedrock_agent.list_data_sources(knowledgeBaseId=self.kb_id)
                data_sources = response.get('dataSourceSummaries', [])
                
                # Look for existing data source
                for ds in data_sources:
                    if ds.get('name') == f'lms-user-documents-{self.user_id}':
                        logger.info(f"Data source already exists: {ds['dataSourceId']}")
                        return ds['dataSourceId']
                        
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.warning(f"Knowledge Base not found: {self.kb_id}")
                    return None
                raise
            
            # Create new data source
            data_source_config = {
                'knowledgeBaseId': self.kb_id,
                'name': f'lms-user-documents-{self.user_id}',
                'description': f'User documents for {self.user_id}',
                'dataSourceConfiguration': {
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f'arn:aws:s3:::{self.bucket_name}',
                        'inclusionPrefixes': [f'processed/knowledge_base/{self.user_id}/']
                    }
                }
            }
            
            response = self.bedrock_agent.create_data_source(**data_source_config)
            data_source_id = response['dataSource']['dataSourceId']
            
            logger.info(f"Created data source: {data_source_id}")
            return data_source_id
            
        except Exception as e:
            logger.error(f"Failed to create data source: {e}")
            return None
    
    def trigger_knowledge_base_sync(self, data_source_id: str = None) -> IndexingResult:
        """
        Trigger Knowledge Base synchronization to index new documents.
        
        Args:
            data_source_id: Data source ID to sync (optional)
            
        Returns:
            IndexingResult with sync status
        """
        try:
            if not self.kb_id:
                return IndexingResult(
                    success=False,
                    error="No Knowledge Base ID configured"
                )
            
            # Get or create data source
            if not data_source_id:
                data_source_id = self.create_data_source_if_needed()
                
            if not data_source_id:
                return IndexingResult(
                    success=False,
                    error="Failed to get or create data source"
                )
            
            # Start ingestion job
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=self.kb_id,
                dataSourceId=data_source_id,
                description=f"Sync user documents for {self.user_id}"
            )
            
            ingestion_job_id = response['ingestionJob']['ingestionJobId']
            
            logger.info(f"Started Knowledge Base sync: {ingestion_job_id}")
            
            return IndexingResult(
                success=True,
                message="Knowledge Base sync started successfully",
                data={
                    'ingestion_job_id': ingestion_job_id,
                    'data_source_id': data_source_id,
                    'kb_id': self.kb_id
                }
            )
            
        except ClientError as e:
            error_msg = f"Knowledge Base sync failed: {e}"
            logger.error(error_msg)
            return IndexingResult(
                success=False,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Sync trigger failed: {e}"
            logger.error(error_msg)
            return IndexingResult(
                success=False,
                error=error_msg
            )
    
    def check_sync_status(self, ingestion_job_id: str) -> Dict[str, Any]:
        """
        Check the status of a Knowledge Base synchronization job.
        
        Args:
            ingestion_job_id: Ingestion job ID to check
            
        Returns:
            Dictionary with sync status information
        """
        try:
            if not self.kb_id:
                return {'error': 'No Knowledge Base ID configured'}
            
            # Get data source ID (simplified - in production, store this)
            data_source_id = self.create_data_source_if_needed()
            if not data_source_id:
                return {'error': 'Failed to get data source ID'}
            
            response = self.bedrock_agent.get_ingestion_job(
                knowledgeBaseId=self.kb_id,
                dataSourceId=data_source_id,
                ingestionJobId=ingestion_job_id
            )
            
            job_info = response['ingestionJob']
            
            return {
                'job_id': ingestion_job_id,
                'status': job_info.get('status', 'UNKNOWN'),
                'created_at': job_info.get('createdAt', '').isoformat() if job_info.get('createdAt') else '',
                'updated_at': job_info.get('updatedAt', '').isoformat() if job_info.get('updatedAt') else '',
                'description': job_info.get('description', ''),
                'failure_reasons': job_info.get('failureReasons', [])
            }
            
        except ClientError as e:
            logger.error(f"Failed to check sync status: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Sync status check failed: {e}")
            return {'error': str(e)}
    
    def index_document(self, file_id: str, text_content: str, 
                      metadata: Dict[str, Any]) -> IndexingResult:
        """
        Index a document in the Knowledge Base.
        
        Args:
            file_id: Unique file identifier
            text_content: Processed text content
            metadata: Document metadata
            
        Returns:
            IndexingResult with indexing status
        """
        try:
            logger.info(f"Starting document indexing for file: {file_id}")
            
            # Step 1: Prepare document for indexing
            prep_result = self.prepare_document_for_indexing(file_id, text_content, metadata)
            if not prep_result.success:
                return prep_result
            
            # Step 2: Create text chunks for optimal embedding
            chunks = self.chunk_text_for_embeddings(text_content)
            
            # Step 3: Save chunks as separate documents for better retrieval
            chunk_s3_keys = []
            for i, chunk in enumerate(chunks):
                chunk_document = {
                    'title': f"{metadata.get('original_filename', 'Document')} - Part {i+1}",
                    'content': chunk['text'],
                    'metadata': {
                        **prep_result.data['metadata'],
                        'chunk_index': chunk['chunk_index'],
                        'chunk_size': chunk['size'],
                        'word_count': chunk['word_count'],
                        'parent_document_id': file_id
                    },
                    'source': f"user_upload_{self.user_id}_chunk_{i}",
                    'document_id': f"{file_id}_chunk_{i}"
                }
                
                chunk_s3_key = f"processed/knowledge_base/{self.user_id}/{file_id}_chunk_{i}.json"
                
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=chunk_s3_key,
                    Body=json.dumps(chunk_document, indent=2),
                    ContentType='application/json',
                    Metadata={
                        'document-id': f"{file_id}_chunk_{i}",
                        'parent-document-id': file_id,
                        'user-id': self.user_id,
                        'chunk-index': str(i),
                        'content-type': 'knowledge-base-chunk'
                    }
                )
                
                chunk_s3_keys.append(chunk_s3_key)
            
            logger.info(f"Created {len(chunks)} chunks for document: {file_id}")
            
            # Step 4: Trigger Knowledge Base sync
            sync_result = self.trigger_knowledge_base_sync()
            
            return IndexingResult(
                success=True,
                document_id=file_id,
                message=f"Document indexed successfully with {len(chunks)} chunks",
                data={
                    'main_document': prep_result.data['kb_s3_key'],
                    'chunks': chunk_s3_keys,
                    'chunk_count': len(chunks),
                    'sync_job': sync_result.data if sync_result.success else None,
                    'sync_error': sync_result.error if not sync_result.success else None
                }
            )
            
        except Exception as e:
            error_msg = f"Document indexing failed: {e}"
            logger.error(error_msg)
            return IndexingResult(
                success=False,
                document_id=file_id,
                error=error_msg
            )
    
    def batch_index_documents(self, documents: List[Dict[str, Any]]) -> List[IndexingResult]:
        """
        Index multiple documents in batch.
        
        Args:
            documents: List of document dictionaries with file_id, text_content, metadata
            
        Returns:
            List of IndexingResult objects
        """
        results = []
        
        for doc in documents:
            file_id = doc.get('file_id')
            text_content = doc.get('text_content', '')
            metadata = doc.get('metadata', {})
            
            if not file_id:
                results.append(IndexingResult(
                    success=False,
                    error="Missing file_id in document"
                ))
                continue
            
            result = self.index_document(file_id, text_content, metadata)
            results.append(result)
            
            # Small delay between documents to avoid rate limiting
            time.sleep(0.1)
        
        successful = sum(1 for r in results if r.success)
        logger.info(f"Batch indexing completed: {successful}/{len(documents)} successful")
        
        return results
    
    def search_documents(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search documents in the Knowledge Base.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            if not self.kb_id:
                return {'error': 'No Knowledge Base ID configured'}
            
            # Use Bedrock Knowledge Base retrieve API
            response = self.bedrock_agent.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            results = []
            for item in response.get('retrievalResults', []):
                result = {
                    'content': item.get('content', {}).get('text', ''),
                    'score': item.get('score', 0.0),
                    'location': item.get('location', {}),
                    'metadata': item.get('metadata', {})
                }
                results.append(result)
            
            return {
                'query': query,
                'results': results,
                'total_results': len(results)
            }
            
        except ClientError as e:
            logger.error(f"Knowledge Base search failed: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {'error': str(e)}

def main():
    """Test function for KnowledgeBaseManager"""
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing KnowledgeBaseManager")
    print("=" * 50)
    
    try:
        kb_manager = KnowledgeBaseManager("test_user")
        print("✅ KnowledgeBaseManager initialized")
        
        # Test document preparation
        test_metadata = {
            'original_filename': 'test_document.txt',
            'file_type': 'text/plain',
            'upload_timestamp': datetime.now().isoformat(),
            'extracted_concepts': ['test', 'document', 'knowledge']
        }
        
        test_content = "This is a test document for Knowledge Base indexing. It contains multiple sentences to test the chunking functionality."
        
        prep_result = kb_manager.prepare_document_for_indexing(
            'test-file-123', 
            test_content, 
            test_metadata
        )
        
        if prep_result.success:
            print("✅ Document preparation successful")
            print(f"   S3 Key: {prep_result.data.get('kb_s3_key', 'N/A')}")
        else:
            print(f"❌ Document preparation failed: {prep_result.error}")
        
        # Test text chunking
        chunks = kb_manager.chunk_text_for_embeddings(test_content, chunk_size=50)
        print(f"✅ Text chunking: {len(chunks)} chunks created")
        
        print("\n🎉 KnowledgeBaseManager test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()