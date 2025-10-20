"""
Vector storage utilities for RAG functionality
Handles Pinecone integration and embedding generation
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import boto3

# Pinecone integration
try:
    from pinecone import Pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    print("Warning: Pinecone not available. Install with: pip install pinecone")

logger = logging.getLogger(__name__)


class VectorStorage:
    """Handles vector storage operations for RAG"""
    
    def __init__(self, api_key: Optional[str] = None, index_name: str = "lms-vectors"):
        self.api_key = api_key or os.getenv('PINECONE_API_KEY')
        self.index_name = index_name
        self.pc = None
        self.index = None
        
        # Initialize Bedrock for embeddings
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        self.embedding_model = os.getenv('BEDROCK_EMBEDDING_MODEL_ID', 'amazon.titan-embed-text-v1')
        
        if PINECONE_AVAILABLE and self.api_key:
            try:
                self.pc = Pinecone(api_key=self.api_key)
                if self.pc.has_index(self.index_name):
                    self.index = self.pc.Index(self.index_name)
                    logger.info(f"Connected to Pinecone index: {self.index_name}")
                else:
                    logger.warning(f"Pinecone index '{self.index_name}' not found")
            except Exception as e:
                logger.error(f"Error initializing Pinecone: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if vector storage is available and configured"""
        return PINECONE_AVAILABLE and self.index is not None
    
    def create_index_if_not_exists(self, dimension: int = 1536, metric: str = "cosine") -> bool:
        """Create Pinecone index if it doesn't exist"""
        
        if not PINECONE_AVAILABLE or not self.pc:
            logger.error("Pinecone not available for index creation")
            return False
        
        try:
            if not self.pc.has_index(self.index_name):
                self.pc.create_index(
                    name=self.index_name,
                    dimension=dimension,
                    metric=metric,
                    spec={
                        "serverless": {
                            "cloud": "aws",
                            "region": "us-east-1"
                        }
                    }
                )
                logger.info(f"Created Pinecone index: {self.index_name}")
                
            self.index = self.pc.Index(self.index_name)
            return True
            
        except Exception as e:
            logger.error(f"Error creating Pinecone index: {str(e)}")
            return False
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Bedrock Titan"""
        
        try:
            # Truncate text if too long (Titan has input limits)
            max_input_length = 8000  # Conservative limit for Titan
            if len(text) > max_input_length:
                text = text[:max_input_length]
                logger.warning(f"Text truncated to {max_input_length} characters for embedding")
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.embedding_model,
                body=json.dumps({
                    'inputText': text
                })
            )
            
            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding')
            
            if embedding and len(embedding) == 1536:  # Titan embedding dimension
                return embedding
            else:
                logger.error(f"Invalid embedding response: {len(embedding) if embedding else 0} dimensions")
                return None
                
        except Exception as e:
            logger.error(f"Error generating Bedrock embedding: {str(e)}")
            return None
    
    def generate_embedding_mock(self, text: str) -> List[float]:
        """Generate mock embedding for testing (deterministic)"""
        
        import hashlib
        import struct
        
        # Create deterministic "embedding" from text hash
        text_hash = hashlib.md5(text.encode()).digest()
        embedding = []
        
        # Generate 1536 values (Titan embedding dimension)
        for i in range(1536):
            # Use hash bytes cyclically to create pseudo-random floats
            byte_index = (i * 4) % len(text_hash)
            
            # Create 4-byte sequence for float conversion
            byte_sequence = b''
            for j in range(4):
                byte_sequence += bytes([text_hash[(byte_index + j) % len(text_hash)]])
            
            # Convert to float and normalize
            value = struct.unpack('I', byte_sequence)[0] / (2**32)  # Normalize to 0-1
            embedding.append(value)
        
        return embedding
    
    def store_document_vectors(self, file_id: str, user_id: str, filename: str, 
                             text_chunks: List[Dict[str, Any]], 
                             subject_id: Optional[str] = None,
                             use_mock_embeddings: bool = False) -> int:
        """Store document vectors in Pinecone"""
        
        if not self.is_available() and not use_mock_embeddings:
            logger.warning("Pinecone not available, using mock storage")
            use_mock_embeddings = True
        
        vectors_stored = 0
        
        try:
            vectors_to_upsert = []
            
            for chunk in text_chunks:
                chunk_text = chunk['text']
                chunk_index = chunk['index']
                
                # Generate embedding
                if use_mock_embeddings:
                    embedding = self.generate_embedding_mock(chunk_text)
                else:
                    embedding = self.generate_embedding(chunk_text)
                
                if not embedding:
                    logger.error(f"Failed to generate embedding for chunk {chunk_index}")
                    continue
                
                # Create vector ID
                vector_id = f"user_{user_id}_file_{file_id}_chunk_{chunk_index}"
                
                # Create metadata
                metadata = {
                    'user_id': user_id,
                    'file_id': file_id,
                    'filename': filename,
                    'chunk_index': chunk_index,
                    'text': chunk_text[:1000],  # Limit metadata size
                    'chunk_length': chunk['length'],
                    'start_pos': chunk['start_pos'],
                    'end_pos': chunk['end_pos'],
                    'created_at': datetime.utcnow().isoformat(),
                    'document_type': 'file_chunk'
                }
                
                if subject_id:
                    metadata['subject_id'] = subject_id
                
                vectors_to_upsert.append({
                    'id': vector_id,
                    'values': embedding,
                    'metadata': metadata
                })
                
                vectors_stored += 1
            
            # Upsert vectors to Pinecone (if available)
            if self.is_available() and not use_mock_embeddings:
                # Batch upsert in chunks of 100 (Pinecone limit)
                batch_size = 100
                for i in range(0, len(vectors_to_upsert), batch_size):
                    batch = vectors_to_upsert[i:i + batch_size]
                    self.index.upsert(vectors=batch)
                    logger.debug(f"Upserted batch {i//batch_size + 1}: {len(batch)} vectors")
                
                logger.info(f"Stored {vectors_stored} vectors in Pinecone for file {file_id}")
            else:
                logger.info(f"Mock stored {vectors_stored} vectors for file {file_id}")
            
            return vectors_stored
            
        except Exception as e:
            logger.error(f"Error storing vectors in Pinecone: {str(e)}")
            return 0
    
    def query_similar_vectors(self, query_text: str, user_id: str, 
                            top_k: int = 5, subject_id: Optional[str] = None,
                            use_mock: bool = False) -> List[Dict[str, Any]]:
        """Query similar vectors from Pinecone"""
        
        if not self.is_available() and not use_mock:
            logger.warning("Pinecone not available for querying")
            return []
        
        try:
            # Generate query embedding
            if use_mock:
                query_embedding = self.generate_embedding_mock(query_text)
            else:
                query_embedding = self.generate_embedding(query_text)
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Build filter for user's documents
            filter_dict = {'user_id': user_id}
            if subject_id:
                filter_dict['subject_id'] = subject_id
            
            if use_mock:
                # Return mock results for testing
                return self._generate_mock_query_results(query_text, user_id, top_k)
            
            # Query Pinecone
            query_response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=True
            )
            
            matches = query_response.get('matches', [])
            
            # Format results
            results = []
            for match in matches:
                results.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match['metadata'],
                    'text': match['metadata'].get('text', '')
                })
            
            logger.info(f"Found {len(results)} similar vectors for query")
            return results
            
        except Exception as e:
            logger.error(f"Error querying Pinecone: {str(e)}")
            return []
    
    def _generate_mock_query_results(self, query_text: str, user_id: str, top_k: int) -> List[Dict[str, Any]]:
        """Generate mock query results for testing"""
        
        mock_results = []
        
        for i in range(min(top_k, 3)):  # Return up to 3 mock results
            mock_results.append({
                'id': f'user_{user_id}_file_mock_{i}_chunk_0',
                'score': 0.9 - (i * 0.1),  # Decreasing relevance scores
                'metadata': {
                    'user_id': user_id,
                    'file_id': f'mock_file_{i}',
                    'filename': f'mock_document_{i}.pdf',
                    'chunk_index': 0,
                    'text': f'Mock relevant content for query: {query_text[:50]}...',
                    'created_at': datetime.utcnow().isoformat(),
                    'document_type': 'file_chunk'
                },
                'text': f'This is mock content that would be relevant to: {query_text[:100]}...'
            })
        
        return mock_results
    
    def delete_file_vectors(self, file_id: str, user_id: str) -> bool:
        """Delete all vectors for a specific file"""
        
        if not self.is_available():
            logger.warning("Pinecone not available for deletion")
            return True  # Return True for mock deletion
        
        try:
            # Query to find all vectors for this file
            filter_dict = {
                'user_id': user_id,
                'file_id': file_id
            }
            
            # Get all vector IDs for this file
            query_response = self.index.query(
                vector=[0.0] * 1536,  # Dummy vector for metadata-only query
                top_k=10000,  # Large number to get all chunks
                filter=filter_dict,
                include_metadata=False  # We only need IDs
            )
            
            vector_ids = [match['id'] for match in query_response.get('matches', [])]
            
            if vector_ids:
                # Delete vectors in batches
                batch_size = 1000  # Pinecone deletion limit
                for i in range(0, len(vector_ids), batch_size):
                    batch_ids = vector_ids[i:i + batch_size]
                    self.index.delete(ids=batch_ids)
                
                logger.info(f"Deleted {len(vector_ids)} vectors for file {file_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vectors for file {file_id}: {str(e)}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        
        if not self.is_available():
            return {
                'status': 'unavailable',
                'total_vectors': 0,
                'dimension': 1536
            }
        
        try:
            stats = self.index.describe_index_stats()
            return {
                'status': 'available',
                'total_vectors': stats.get('total_vector_count', 0),
                'dimension': stats.get('dimension', 1536),
                'index_fullness': stats.get('index_fullness', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error getting Pinecone stats: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }


# Helper functions for RAG context formatting

def format_rag_context(query_results: List[Dict[str, Any]], 
                      max_context_length: int = 4000) -> Tuple[str, List[str]]:
    """Format query results into RAG context and citations"""
    
    context_parts = []
    citations = []
    current_length = 0
    
    for result in query_results:
        metadata = result.get('metadata', {})
        score = result.get('score', 0)
        text = result.get('text', '')
        
        # Only include high-confidence matches
        if score < 0.7:
            continue
        
        # Check if adding this content would exceed limit
        if current_length + len(text) > max_context_length:
            break
        
        context_parts.append(text)
        current_length += len(text)
        
        # Create citation
        filename = metadata.get('filename', 'Unknown')
        chunk_index = metadata.get('chunk_index', 0)
        citation = f"{filename} (chunk {chunk_index + 1})"
        if citation not in citations:
            citations.append(citation)
    
    context = "\n\n".join(context_parts)
    return context, citations


def create_vector_metadata(file_id: str, user_id: str, filename: str, 
                          chunk_index: int, chunk_data: Dict[str, Any],
                          subject_id: Optional[str] = None) -> Dict[str, Any]:
    """Create standardized metadata for vector storage"""
    
    metadata = {
        'user_id': user_id,
        'file_id': file_id,
        'filename': filename,
        'chunk_index': chunk_index,
        'text': chunk_data['text'][:1000],  # Limit size
        'chunk_length': chunk_data['length'],
        'start_pos': chunk_data['start_pos'],
        'end_pos': chunk_data['end_pos'],
        'created_at': datetime.utcnow().isoformat(),
        'document_type': 'file_chunk'
    }
    
    if subject_id:
        metadata['subject_id'] = subject_id
    
    return metadata


# Global instance for easy import
vector_storage = VectorStorage()