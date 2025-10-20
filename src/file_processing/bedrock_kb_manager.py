"""
Bedrock Knowledge Base Manager for Advanced Document Processing
Handles document indexing, retrieval, and user-specific namespaces
"""

import boto3
import json
import logging
import os
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BedrockKnowledgeBaseManager:
    """Manages Bedrock Knowledge Base operations for document processing"""
    
    def __init__(self):
        """Initialize Bedrock Knowledge Base manager"""
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        self.s3_client = boto3.client('s3')
        
        # Configuration
        self.knowledge_base_id = os.getenv('BEDROCK_KNOWLEDGE_BASE_ID')
        self.data_source_id = os.getenv('BEDROCK_DATA_SOURCE_ID')
        self.s3_bucket = os.getenv('DOCUMENTS_BUCKET')
        self.kb_prefix = 'knowledge-base/'
        
        # Embedding model configuration
        self.embedding_model_arn = os.getenv(
            'BEDROCK_EMBEDDING_MODEL_ARN',
            'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1'
        )
        
        logger.info(f"Initialized Bedrock KB Manager with KB ID: {self.knowledge_base_id}")
    
    def is_configured(self) -> bool:
        """Check if Knowledge Base is properly configured"""
        return bool(self.knowledge_base_id and self.s3_bucket)
    
    def store_document_in_kb(self, file_id: str, user_id: str, filename: str, 
                           text_content: str, chunks: List[Dict[str, Any]],
                           comprehend_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Store document in Bedrock Knowledge Base with user-specific namespace"""
        
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Bedrock Knowledge Base not configured',
                'kb_document_id': None
            }
        
        try:
            # Create document metadata
            document_metadata = {
                'file_id': file_id,
                'user_id': user_id,
                'filename': filename,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'total_chunks': len(chunks),
                'document_type': 'user_upload',
                'text_length': len(text_content)
            }
            
            # Add Comprehend analysis if available
            if comprehend_analysis:
                document_metadata.update({
                    'entities_count': len(comprehend_analysis.get('entities', [])),
                    'key_phrases_count': len(comprehend_analysis.get('key_phrases', [])),
                    'language': comprehend_analysis.get('language', 'en'),
                    'sentiment': comprehend_analysis.get('sentiment', {}).get('sentiment') if comprehend_analysis.get('sentiment') else None
                })
            
            # Store document chunks in S3 for Knowledge Base ingestion
            kb_documents_stored = self._store_chunks_for_kb(
                file_id, user_id, filename, chunks, document_metadata, comprehend_analysis
            )
            
            if not kb_documents_stored:
                return {
                    'success': False,
                    'error': 'Failed to store document chunks for Knowledge Base',
                    'kb_document_id': None
                }
            
            # Trigger Knowledge Base ingestion
            ingestion_job_id = self._trigger_kb_ingestion()
            
            return {
                'success': True,
                'kb_document_id': f"user_{user_id}_file_{file_id}",
                'documents_stored': kb_documents_stored,
                'ingestion_job_id': ingestion_job_id,
                'message': 'Document stored in Knowledge Base successfully'
            }
            
        except Exception as e:
            logger.error(f"Error storing document in KB: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'kb_document_id': None
            }
    
    def _store_chunks_for_kb(self, file_id: str, user_id: str, filename: str,
                           chunks: List[Dict[str, Any]], document_metadata: Dict[str, Any],
                           comprehend_analysis: Dict[str, Any] = None) -> int:
        """Store document chunks in S3 format for Knowledge Base ingestion"""
        
        try:
            documents_stored = 0
            
            for chunk in chunks:
                chunk_index = chunk['index']
                chunk_text = chunk['text']
                
                # Create document for Knowledge Base
                kb_document = {
                    'text': chunk_text,
                    'metadata': {
                        'file_id': file_id,
                        'user_id': user_id,
                        'filename': filename,
                        'chunk_index': chunk_index,
                        'chunk_length': chunk['length'],
                        'start_pos': chunk['start_pos'],
                        'end_pos': chunk['end_pos'],
                        'document_type': 'user_upload_chunk',
                        'created_at': datetime.utcnow().isoformat()
                    }
                }
                
                # Add Comprehend insights to metadata
                if comprehend_analysis:
                    # Extract relevant entities and key phrases for this chunk
                    chunk_entities = self._extract_chunk_entities(
                        chunk_text, chunk['start_pos'], chunk['end_pos'], 
                        comprehend_analysis.get('entities', [])
                    )
                    chunk_key_phrases = self._extract_chunk_key_phrases(
                        chunk_text, chunk['start_pos'], chunk['end_pos'],
                        comprehend_analysis.get('key_phrases', [])
                    )
                    
                    kb_document['metadata'].update({
                        'entities': [e['text'] for e in chunk_entities[:5]],  # Top 5 entities
                        'key_phrases': [p['text'] for p in chunk_key_phrases[:5]],  # Top 5 phrases
                        'language': comprehend_analysis.get('language', 'en')
                    })
                
                # Store in S3 with user-specific namespace
                s3_key = f"{self.kb_prefix}user_{user_id}/{file_id}_chunk_{chunk_index}.json"
                
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=s3_key,
                    Body=json.dumps(kb_document, indent=2),
                    ContentType='application/json',
                    Metadata={
                        'user_id': user_id,
                        'file_id': file_id,
                        'chunk_index': str(chunk_index)
                    }
                )
                
                documents_stored += 1
                logger.debug(f"Stored KB document: {s3_key}")
            
            logger.info(f"Stored {documents_stored} KB documents for file {file_id}")
            return documents_stored
            
        except Exception as e:
            logger.error(f"Error storing chunks for KB: {str(e)}")
            return 0
    
    def _extract_chunk_entities(self, chunk_text: str, start_pos: int, end_pos: int,
                              all_entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract entities that fall within this chunk's text range"""
        
        chunk_entities = []
        
        for entity in all_entities:
            entity_start = entity.get('begin_offset', 0)
            entity_end = entity.get('end_offset', 0)
            
            # Check if entity overlaps with chunk
            if (entity_start >= start_pos and entity_start < end_pos) or \
               (entity_end > start_pos and entity_end <= end_pos) or \
               (entity_start < start_pos and entity_end > end_pos):
                
                # Adjust offsets relative to chunk
                relative_start = max(0, entity_start - start_pos)
                relative_end = min(len(chunk_text), entity_end - start_pos)
                
                chunk_entities.append({
                    'text': entity['text'],
                    'type': entity['type'],
                    'score': entity['score'],
                    'begin_offset': relative_start,
                    'end_offset': relative_end
                })
        
        # Sort by score (confidence) descending
        chunk_entities.sort(key=lambda x: x['score'], reverse=True)
        return chunk_entities
    
    def _extract_chunk_key_phrases(self, chunk_text: str, start_pos: int, end_pos: int,
                                 all_key_phrases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract key phrases that fall within this chunk's text range"""
        
        chunk_phrases = []
        
        for phrase in all_key_phrases:
            phrase_start = phrase.get('begin_offset', 0)
            phrase_end = phrase.get('end_offset', 0)
            
            # Check if phrase overlaps with chunk
            if (phrase_start >= start_pos and phrase_start < end_pos) or \
               (phrase_end > start_pos and phrase_end <= end_pos) or \
               (phrase_start < start_pos and phrase_end > end_pos):
                
                # Adjust offsets relative to chunk
                relative_start = max(0, phrase_start - start_pos)
                relative_end = min(len(chunk_text), phrase_end - start_pos)
                
                chunk_phrases.append({
                    'text': phrase['text'],
                    'score': phrase['score'],
                    'begin_offset': relative_start,
                    'end_offset': relative_end
                })
        
        # Sort by score (confidence) descending
        chunk_phrases.sort(key=lambda x: x['score'], reverse=True)
        return chunk_phrases
    
    def _trigger_kb_ingestion(self) -> Optional[str]:
        """Trigger Knowledge Base data source ingestion"""
        
        if not self.data_source_id:
            logger.warning("Data source ID not configured, skipping ingestion")
            return None
        
        try:
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=self.knowledge_base_id,
                dataSourceId=self.data_source_id,
                description=f"Ingestion job triggered at {datetime.utcnow().isoformat()}"
            )
            
            ingestion_job_id = response['ingestionJob']['ingestionJobId']
            logger.info(f"Started KB ingestion job: {ingestion_job_id}")
            return ingestion_job_id
            
        except Exception as e:
            logger.error(f"Error triggering KB ingestion: {str(e)}")
            return None
    
    def query_knowledge_base(self, query: str, user_id: str, max_results: int = 5) -> Dict[str, Any]:
        """Query Knowledge Base with user-specific filtering"""
        
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Bedrock Knowledge Base not configured',
                'results': []
            }
        
        try:
            # Query Knowledge Base with user filtering
            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results,
                        'overrideSearchType': 'HYBRID'  # Use both semantic and keyword search
                    }
                }
            )
            
            # Filter results for user's documents only
            user_results = []
            for result in response.get('retrievalResults', []):
                metadata = result.get('metadata', {})
                
                # Check if this result belongs to the user
                if metadata.get('user_id') == user_id:
                    user_results.append({
                        'text': result.get('content', {}).get('text', ''),
                        'score': result.get('score', 0),
                        'metadata': metadata,
                        'location': result.get('location', {})
                    })
            
            logger.info(f"KB query returned {len(user_results)} user-specific results")
            
            return {
                'success': True,
                'results': user_results,
                'total_results': len(user_results),
                'query': query
            }
            
        except Exception as e:
            logger.error(f"Error querying Knowledge Base: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': []
            }
    
    def get_ingestion_job_status(self, ingestion_job_id: str) -> Dict[str, Any]:
        """Get status of Knowledge Base ingestion job"""
        
        try:
            response = self.bedrock_agent.get_ingestion_job(
                knowledgeBaseId=self.knowledge_base_id,
                dataSourceId=self.data_source_id,
                ingestionJobId=ingestion_job_id
            )
            
            job = response['ingestionJob']
            
            return {
                'job_id': job['ingestionJobId'],
                'status': job['status'],
                'started_at': job.get('startedAt'),
                'updated_at': job.get('updatedAt'),
                'statistics': job.get('statistics', {}),
                'failure_reasons': job.get('failureReasons', [])
            }
            
        except Exception as e:
            logger.error(f"Error getting ingestion job status: {str(e)}")
            return {
                'job_id': ingestion_job_id,
                'status': 'UNKNOWN',
                'error': str(e)
            }
    
    def delete_user_documents(self, user_id: str) -> Dict[str, Any]:
        """Delete all documents for a specific user from Knowledge Base"""
        
        try:
            # List and delete S3 objects for user
            prefix = f"{self.kb_prefix}user_{user_id}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=prefix
            )
            
            objects_deleted = 0
            
            if 'Contents' in response:
                # Delete objects in batches
                objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                
                if objects_to_delete:
                    delete_response = self.s3_client.delete_objects(
                        Bucket=self.s3_bucket,
                        Delete={'Objects': objects_to_delete}
                    )
                    
                    objects_deleted = len(delete_response.get('Deleted', []))
            
            # Trigger re-ingestion to update Knowledge Base
            ingestion_job_id = self._trigger_kb_ingestion()
            
            logger.info(f"Deleted {objects_deleted} KB documents for user {user_id}")
            
            return {
                'success': True,
                'objects_deleted': objects_deleted,
                'ingestion_job_id': ingestion_job_id
            }
            
        except Exception as e:
            logger.error(f"Error deleting user documents: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'objects_deleted': 0
            }
    
    def get_kb_statistics(self) -> Dict[str, Any]:
        """Get Knowledge Base statistics and health"""
        
        try:
            # Get Knowledge Base details
            kb_response = self.bedrock_agent.get_knowledge_base(
                knowledgeBaseId=self.knowledge_base_id
            )
            
            kb_info = kb_response['knowledgeBase']
            
            # Get data source details
            ds_response = self.bedrock_agent.get_data_source(
                knowledgeBaseId=self.knowledge_base_id,
                dataSourceId=self.data_source_id
            ) if self.data_source_id else None
            
            # Count S3 objects
            s3_response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=self.kb_prefix
            )
            
            total_documents = len(s3_response.get('Contents', []))
            
            return {
                'knowledge_base_id': self.knowledge_base_id,
                'kb_name': kb_info.get('name'),
                'kb_status': kb_info.get('status'),
                'created_at': kb_info.get('createdAt'),
                'updated_at': kb_info.get('updatedAt'),
                'data_source_id': self.data_source_id,
                'data_source_status': ds_response['dataSource'].get('status') if ds_response else 'Unknown',
                'total_documents': total_documents,
                's3_bucket': self.s3_bucket,
                'kb_prefix': self.kb_prefix
            }
            
        except Exception as e:
            logger.error(f"Error getting KB statistics: {str(e)}")
            return {
                'knowledge_base_id': self.knowledge_base_id,
                'error': str(e),
                'status': 'ERROR'
            }


# Global instance for easy import
bedrock_kb_manager = BedrockKnowledgeBaseManager()