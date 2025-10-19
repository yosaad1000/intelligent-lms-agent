"""
Simple tests for RAG File Processing functionality
Tests core components without complex AWS mocking
"""

import json
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from file_processing.file_handler import (
    create_text_chunks,
    update_file_status,
    get_cors_headers
)

from file_processing.text_extractor import TextExtractor
from file_processing.vector_storage import VectorStorage


class TestRAGComponents:
    """Test individual RAG components"""
    
    def test_text_chunking(self):
        """Test text chunking functionality"""
        
        # Test short text (no chunking needed)
        short_text = "This is a short text that doesn't need chunking."
        chunks = create_text_chunks(short_text, chunk_size=1000)
        
        assert len(chunks) == 1
        assert chunks[0]['text'] == short_text
        assert chunks[0]['index'] == 0
        assert chunks[0]['start_pos'] == 0
        assert chunks[0]['end_pos'] == len(short_text)
        
        # Test long text (chunking needed)
        long_text = "This is a sentence. " * 100  # Create long text
        chunks = create_text_chunks(long_text, chunk_size=200, overlap=50)
        
        assert len(chunks) > 1
        assert all('text' in chunk for chunk in chunks)
        assert all('index' in chunk for chunk in chunks)
        assert all('start_pos' in chunk for chunk in chunks)
        assert all('end_pos' in chunk for chunk in chunks)
        assert all('length' in chunk for chunk in chunks)
        
        # Verify chunk indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk['index'] == i
    
    def test_text_extractor_txt(self):
        """Test text extraction from TXT files"""
        
        extractor = TextExtractor()
        
        # Test UTF-8 text
        test_text = "This is a test document.\nWith multiple lines.\nAnd special characters: áéíóú"
        file_content = test_text.encode('utf-8')
        
        result = extractor.extract_text(file_content, 'test.txt')
        
        assert result['success'] is True
        assert result['text'] == test_text
        assert 'metadata' in result
        assert result['metadata']['file_extension'] == '.txt'
    
    def test_text_extractor_unsupported(self):
        """Test text extraction with unsupported file type"""
        
        extractor = TextExtractor()
        
        result = extractor.extract_text(b'test content', 'test.exe')
        
        assert result['success'] is False
        assert 'Unsupported file type' in result['error']
        assert result['text'] == ''
    
    def test_text_validation(self):
        """Test text validation functionality"""
        
        extractor = TextExtractor()
        
        # Test valid text
        valid_text = "This is a valid document with sufficient content for processing."
        validation = extractor.validate_extracted_text(valid_text, min_length=10)
        
        assert validation['is_valid'] is True
        assert 'statistics' in validation
        assert validation['statistics']['character_count'] == len(valid_text)
        assert validation['statistics']['word_count'] > 0
        
        # Test invalid text (too short)
        short_text = "Short"
        validation = extractor.validate_extracted_text(short_text, min_length=50)
        
        assert validation['is_valid'] is False
        assert len(validation['warnings']) > 0
    
    def test_text_cleaning(self):
        """Test text cleaning functionality"""
        
        extractor = TextExtractor()
        
        # Test text with excessive whitespace
        messy_text = "This  is   a    messy\n\n\n\ntext   with\t\ttabs\nand   spaces."
        cleaned = extractor.clean_extracted_text(messy_text)
        
        assert "   " not in cleaned  # No triple spaces
        assert "\n\n\n" not in cleaned  # No triple newlines
        assert cleaned.strip() == cleaned  # No leading/trailing whitespace
    
    def test_vector_storage_mock_embedding(self):
        """Test mock embedding generation"""
        
        storage = VectorStorage()
        
        text = "This is a test document for embedding generation."
        embedding = storage.generate_embedding_mock(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # Titan embedding dimension
        assert all(isinstance(val, float) for val in embedding)
        assert all(0 <= val <= 1 for val in embedding)  # Normalized values
        
        # Test deterministic behavior
        embedding2 = storage.generate_embedding_mock(text)
        assert embedding == embedding2  # Should be identical for same text
    
    def test_vector_storage_mock_query(self):
        """Test mock vector querying"""
        
        storage = VectorStorage()
        
        query_text = "test query"
        user_id = "test_user_123"
        
        results = storage.query_similar_vectors(
            query_text=query_text,
            user_id=user_id,
            top_k=3,
            use_mock=True
        )
        
        assert isinstance(results, list)
        assert len(results) <= 3
        
        for result in results:
            assert 'id' in result
            assert 'score' in result
            assert 'metadata' in result
            assert 'text' in result
            assert result['metadata']['user_id'] == user_id
    
    def test_cors_headers(self):
        """Test CORS headers generation"""
        
        headers = get_cors_headers()
        
        required_headers = [
            'Content-Type',
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]
        
        for header in required_headers:
            assert header in headers
        
        assert headers['Access-Control-Allow-Origin'] == '*'
        assert 'GET' in headers['Access-Control-Allow-Methods']
        assert 'POST' in headers['Access-Control-Allow-Methods']
    
    @patch('boto3.resource')
    def test_update_file_status(self, mock_dynamodb):
        """Test file status update functionality"""
        
        # Mock DynamoDB table
        mock_table = Mock()
        mock_dynamodb.return_value.Table.return_value = mock_table
        
        # Test successful update
        mock_table.update_item.return_value = {}
        
        result = update_file_status(
            mock_table,
            'test_file_123',
            'processing_status',
            'completed',
            {'chunks_created': 5}
        )
        
        assert result is True
        mock_table.update_item.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_table.update_item.call_args
        assert call_args[1]['Key']['file_id'] == 'test_file_123'
        assert ':status' in call_args[1]['ExpressionAttributeValues']
        assert call_args[1]['ExpressionAttributeValues'][':status'] == 'completed'
    
    def test_supported_file_types(self):
        """Test supported file type checking"""
        
        extractor = TextExtractor()
        
        # Test supported types
        assert extractor.is_supported_file('document.pdf') is True
        assert extractor.is_supported_file('document.docx') is True
        assert extractor.is_supported_file('document.txt') is True
        
        # Test unsupported types
        assert extractor.is_supported_file('document.exe') is False
        assert extractor.is_supported_file('document.jpg') is False
        assert extractor.is_supported_file('document.mp4') is False
        
        # Test case insensitive
        assert extractor.is_supported_file('DOCUMENT.PDF') is True
        assert extractor.is_supported_file('Document.TXT') is True


class TestRAGIntegration:
    """Test RAG component integration"""
    
    def test_end_to_end_text_processing(self):
        """Test complete text processing pipeline"""
        
        # Create test document
        test_content = """
        This is a comprehensive test document for RAG processing.
        
        It contains multiple paragraphs with different types of content.
        Some paragraphs are longer than others to test the chunking functionality.
        
        The document includes various topics:
        - Machine learning concepts
        - Natural language processing
        - Information retrieval systems
        
        This content should be properly extracted, chunked, and prepared for vector storage.
        Each chunk should maintain semantic coherence while respecting size limits.
        """
        
        # Step 1: Extract text
        extractor = TextExtractor()
        extraction_result = extractor.extract_text(test_content.encode('utf-8'), 'test.txt')
        
        assert extraction_result['success'] is True
        extracted_text = extraction_result['text']
        
        # Step 2: Clean text
        cleaned_text = extractor.clean_extracted_text(extracted_text)
        assert len(cleaned_text) > 0
        
        # Step 3: Validate text
        validation = extractor.validate_extracted_text(cleaned_text)
        assert validation['is_valid'] is True
        
        # Step 4: Create chunks
        chunks = create_text_chunks(cleaned_text, chunk_size=200, overlap=50)
        assert len(chunks) > 1
        
        # Step 5: Generate embeddings (mock)
        storage = VectorStorage()
        embeddings = []
        for chunk in chunks:
            embedding = storage.generate_embedding_mock(chunk['text'])
            embeddings.append(embedding)
        
        assert len(embeddings) == len(chunks)
        assert all(len(emb) == 1536 for emb in embeddings)
        
        # Step 6: Test vector storage (mock)
        vectors_stored = storage.store_document_vectors(
            file_id='test_file_123',
            user_id='test_user_456',
            filename='test.txt',
            text_chunks=chunks,
            use_mock_embeddings=True
        )
        
        assert vectors_stored == len(chunks)
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        
        extractor = TextExtractor()
        storage = VectorStorage()
        
        # Test empty content
        result = extractor.extract_text(b'', 'empty.txt')
        assert result['success'] is True
        assert result['text'] == ''
        
        # Test invalid file type
        result = extractor.extract_text(b'content', 'invalid.xyz')
        assert result['success'] is False
        
        # Test empty chunks
        chunks = create_text_chunks('', chunk_size=100)
        assert len(chunks) == 0
        
        # Test vector storage with empty chunks
        vectors_stored = storage.store_document_vectors(
            file_id='empty_file',
            user_id='test_user',
            filename='empty.txt',
            text_chunks=[],
            use_mock_embeddings=True
        )
        assert vectors_stored == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])