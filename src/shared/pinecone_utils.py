"""
Pinecone utility functions for LMS system
Provides vector database operations for RAG functionality
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

try:
    from pinecone import Pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    try:
        # Fallback for older pinecone-client package
        import pinecone
        PINECONE_AVAILABLE = True
    except ImportError:
        PINECONE_AVAILABLE = False
        print("Warning: Pinecone not available. Install with: pip install pinecone")


class PineconeUtils:
    """Utility class for Pinecone vector database operations"""
    
    def __init__(self, api_key: Optional[str] = None, index_name: str = "lms-vectors"):
        self.api_key = api_key or os.getenv('PINECONE_API_KEY')
        self.index_name = index_name
        self.pc = None
        self.index = None
        
        if PINECONE_AVAILABLE and self.api_key:
            try:
                self.pc = Pinecone(api_key=self.api_key)
                if self.pc.has_index(self.index_name):
                    self.index = self.pc.Index(self.index_name)
                else:
                    print(f"Warning: Pinecone index '{self.index_name}' not found")
            except Exception as e:
                print(f"Error initializing Pinecone: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Pinecone is available and configured"""
        return PINECONE_AVAILABLE and self.index is not None
    
    def create_index_if_not_exists(self, dimension: int = 1536, metric: str = "cosine") -> bool:
        """Create Pinecone index if it doesn't exist"""
        if not PINECONE_AVAILABLE or not self.pc:
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
                print(f"Created Pinecone index: {self.index_name}")
                
            self.index = self.pc.Index(self.index_name)
            return True
        except Exception as e:
            print(f"Error creating Pinecone index: {str(e)}")
            return False
    
    def upsert_vectors(self, vectors: List[Dict[str, Any]]) -> bool:
        """Upsert vectors to Pinecone index"""
        if not self.is_available():
            print("Pinecone not available for upsert operation")
            return False
        
        try:
            # Format vectors for Pinecone
            formatted_vectors = []
            for vector in vectors:
                formatted_vectors.append({
                    'id': vector['id'],
                    'values': vector['values'],
                    'metadata': vector.get('metadata', {})
                })
            
            self.index.upsert(vectors=formatted_vectors)
            return True
        except Exception as e:
            print(f"Error upserting vectors to Pinecone: {str(e)}")
            return False
    
    def query_vectors(self, query_vector: List[float], top_k: int = 5, 
                     filter_dict: Optional[Dict] = None, 
                     include_metadata: bool = True) -> List[Dict[str, Any]]:
        """Query vectors from Pinecone index"""
        if not self.is_available():
            print("Pinecone not available for query operation")
            return []
        
        try:
            query_params = {
                'vector': query_vector,
                'top_k': top_k,
                'include_metadata': include_metadata
            }
            
            if filter_dict:
                query_params['filter'] = filter_dict
            
            response = self.index.query(**query_params)
            return response.get('matches', [])
        except Exception as e:
            print(f"Error querying Pinecone: {str(e)}")
            return []
    
    def delete_vectors(self, vector_ids: List[str]) -> bool:
        """Delete vectors from Pinecone index"""
        if not self.is_available():
            print("Pinecone not available for delete operation")
            return False
        
        try:
            self.index.delete(ids=vector_ids)
            return True
        except Exception as e:
            print(f"Error deleting vectors from Pinecone: {str(e)}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        if not self.is_available():
            return {}
        
        try:
            stats = self.index.describe_index_stats()
            return stats
        except Exception as e:
            print(f"Error getting Pinecone stats: {str(e)}")
            return {}


# Document processing utilities for RAG

def create_document_chunks(text: str, chunk_size: int = 1000, 
                          overlap: int = 200) -> List[str]:
    """Split document text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings near the chunk boundary
            for i in range(end, max(start + chunk_size - 100, start), -1):
                if text[i] in '.!?':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def create_vector_metadata(file_id: str, user_id: str, filename: str, 
                          chunk_index: int, total_chunks: int, 
                          subject_id: Optional[str] = None) -> Dict[str, Any]:
    """Create metadata for vector storage"""
    return {
        'file_id': file_id,
        'user_id': user_id,
        'filename': filename,
        'chunk_index': chunk_index,
        'total_chunks': total_chunks,
        'subject_id': subject_id,
        'created_at': datetime.utcnow().isoformat(),
        'document_type': 'file_chunk'
    }


def create_conversation_vector_metadata(conversation_id: str, message_id: str, 
                                      user_id: str, message_type: str,
                                      subject_id: Optional[str] = None) -> Dict[str, Any]:
    """Create metadata for conversation vectors"""
    return {
        'conversation_id': conversation_id,
        'message_id': message_id,
        'user_id': user_id,
        'message_type': message_type,
        'subject_id': subject_id,
        'created_at': datetime.utcnow().isoformat(),
        'document_type': 'conversation'
    }


def format_rag_context(matches: List[Dict[str, Any]], max_context_length: int = 4000) -> Tuple[str, List[str]]:
    """Format Pinecone matches into RAG context and citations"""
    context_parts = []
    citations = []
    current_length = 0
    
    for match in matches:
        metadata = match.get('metadata', {})
        score = match.get('score', 0)
        
        # Only include high-confidence matches
        if score < 0.7:
            continue
        
        # Extract content (this would be the original text chunk)
        content = metadata.get('content', '')
        if not content:
            continue
        
        # Check if adding this content would exceed limit
        if current_length + len(content) > max_context_length:
            break
        
        context_parts.append(content)
        current_length += len(content)
        
        # Create citation
        filename = metadata.get('filename', 'Unknown')
        chunk_index = metadata.get('chunk_index', 0)
        citation = f"{filename} (chunk {chunk_index + 1})"
        if citation not in citations:
            citations.append(citation)
    
    context = "\n\n".join(context_parts)
    return context, citations


# Global instance for easy import
pinecone_utils = PineconeUtils()


# Helper functions for common RAG operations

def store_document_vectors(file_id: str, user_id: str, filename: str, 
                          text_chunks: List[str], embeddings: List[List[float]],
                          subject_id: Optional[str] = None) -> bool:
    """Store document vectors in Pinecone"""
    if not pinecone_utils.is_available():
        return False
    
    vectors = []
    for i, (chunk, embedding) in enumerate(zip(text_chunks, embeddings)):
        vector_id = f"{file_id}_chunk_{i}"
        metadata = create_vector_metadata(
            file_id, user_id, filename, i, len(text_chunks), subject_id
        )
        metadata['content'] = chunk  # Store the actual text for retrieval
        
        vectors.append({
            'id': vector_id,
            'values': embedding,
            'metadata': metadata
        })
    
    return pinecone_utils.upsert_vectors(vectors)


def search_relevant_documents(query_embedding: List[float], user_id: str,
                            subject_id: Optional[str] = None, 
                            top_k: int = 5) -> Tuple[str, List[str]]:
    """Search for relevant documents and return formatted context"""
    if not pinecone_utils.is_available():
        return "", []
    
    # Build filter for user's documents
    filter_dict = {'user_id': user_id}
    if subject_id:
        filter_dict['subject_id'] = subject_id
    
    matches = pinecone_utils.query_vectors(
        query_vector=query_embedding,
        top_k=top_k,
        filter_dict=filter_dict
    )
    
    return format_rag_context(matches)