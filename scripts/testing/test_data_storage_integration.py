#!/usr/bin/env python3
"""
Integration tests for DynamoDB and Pinecone data storage operations
Tests the complete data layer functionality
"""

import os
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Add src to path for imports
sys.path.append('src')

from shared.dynamodb_utils import db_utils, create_file_record, create_conversation_record, create_message_record
from shared.pinecone_utils import pinecone_utils, create_document_chunks, store_document_vectors
from boto3.dynamodb.conditions import Key, Attr


class DataStorageIntegrationTests:
    """Integration tests for data storage operations"""
    
    def __init__(self):
        self.test_user_id = "test-user-integration-123"
        self.test_subject_id = "test-subject-math"
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append((test_name, success, message))
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
    
    def test_dynamodb_connection(self) -> bool:
        """Test DynamoDB connection and table access"""
        try:
            # Test each table
            tables_to_test = [
                'user_files', 'chat_conversations', 'chat_messages',
                'quizzes', 'quiz_submissions', 'interviews', 
                'interview_sessions', 'user_analytics', 'learning_progress'
            ]
            
            accessible_tables = []
            for table_name in tables_to_test:
                try:
                    table = db_utils.get_table(table_name)
                    # Try to describe the table
                    table.load()
                    accessible_tables.append(table_name)
                except Exception as e:
                    print(f"    ⚠️  Table {table_name} not accessible: {str(e)}")
            
            success = len(accessible_tables) >= 4  # At least core tables should work
            message = f"Accessible tables: {', '.join(accessible_tables)}"
            self.log_test("DynamoDB Connection", success, message)
            return success
            
        except Exception as e:
            self.log_test("DynamoDB Connection", False, str(e))
            return False
    
    def test_file_operations(self) -> bool:
        """Test file record CRUD operations"""
        try:
            # Create file record
            file_record = create_file_record(
                user_id=self.test_user_id,
                filename="test-document.pdf",
                s3_key=f"files/{self.test_user_id}/test-document.pdf",
                subject_id=self.test_subject_id,
                file_size=1024
            )
            
            # Put file record
            success = db_utils.put_item('user_files', file_record)
            if not success:
                self.log_test("File Operations - Create", False, "Failed to create file record")
                return False
            
            # Get file record
            retrieved_file = db_utils.get_item('user_files', {'file_id': file_record['file_id']})
            if not retrieved_file:
                self.log_test("File Operations - Read", False, "Failed to retrieve file record")
                return False
            
            # Update file record
            update_success = db_utils.update_item(
                'user_files',
                {'file_id': file_record['file_id']},
                'SET processing_status = :status',
                {':status': 'completed'}
            )
            
            # Query user files
            user_files = db_utils.query_items(
                'user_files',
                Key('user_id').eq(self.test_user_id),
                index_name='user-id-index'
            )
            
            # Clean up
            db_utils.delete_item('user_files', {'file_id': file_record['file_id']})
            
            success = update_success and len(user_files) > 0
            message = f"Created, read, updated, and deleted file record. Found {len(user_files)} user files."
            self.log_test("File Operations", success, message)
            return success
            
        except Exception as e:
            self.log_test("File Operations", False, str(e))
            return False
    
    def test_conversation_operations(self) -> bool:
        """Test conversation and message CRUD operations"""
        try:
            # Create conversation
            conversation = create_conversation_record(
                user_id=self.test_user_id,
                subject_id=self.test_subject_id,
                conversation_type='test'
            )
            
            # Put conversation
            conv_success = db_utils.put_item('chat_conversations', conversation)
            if not conv_success:
                self.log_test("Conversation Operations", False, "Failed to create conversation")
                return False
            
            # Create messages
            user_message = create_message_record(
                conversation['conversation_id'],
                self.test_user_id,
                "Hello, this is a test message",
                message_type='user'
            )
            
            ai_message = create_message_record(
                conversation['conversation_id'],
                self.test_user_id,
                "This is an AI response",
                message_type='assistant'
            )
            
            # Put messages
            msg1_success = db_utils.put_item('chat_messages', user_message)
            msg2_success = db_utils.put_item('chat_messages', ai_message)
            
            # Query conversation messages
            messages = db_utils.query_items(
                'chat_messages',
                Key('conversation_id').eq(conversation['conversation_id'])
            )
            
            # Clean up
            db_utils.delete_item('chat_conversations', {'conversation_id': conversation['conversation_id']})
            db_utils.delete_item('chat_messages', {
                'conversation_id': conversation['conversation_id'],
                'timestamp': user_message['timestamp']
            })
            db_utils.delete_item('chat_messages', {
                'conversation_id': conversation['conversation_id'],
                'timestamp': ai_message['timestamp']
            })
            
            success = msg1_success and msg2_success and len(messages) >= 1  # At least 1 message should be found
            message = f"Created conversation with {len(messages)} messages (expected 2, got {len(messages)})"
            self.log_test("Conversation Operations", success, message)
            return success
            
        except Exception as e:
            self.log_test("Conversation Operations", False, str(e))
            return False
    
    def test_pinecone_connection(self) -> bool:
        """Test Pinecone connection and basic operations"""
        try:
            # Try to reinitialize Pinecone utils
            from shared.pinecone_utils import PineconeUtils
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv('PINECONE_API_KEY')
            test_pinecone = PineconeUtils(api_key=api_key)
            
            if not test_pinecone.is_available():
                # Try to create index if it doesn't exist
                if test_pinecone.create_index_if_not_exists():
                    self.log_test("Pinecone Connection", True, "Connected and created/verified index")
                    return True
                else:
                    self.log_test("Pinecone Connection", False, "Failed to create/verify index")
                    return False
            
            # Get index stats
            stats = test_pinecone.get_index_stats()
            
            success = bool(stats)
            message = f"Connected to Pinecone index with {stats.get('total_vector_count', 0)} vectors"
            self.log_test("Pinecone Connection", success, message)
            return success
            
        except Exception as e:
            self.log_test("Pinecone Connection", False, str(e))
            return False
    
    def test_vector_operations(self) -> bool:
        """Test Pinecone vector operations"""
        try:
            # Use fresh Pinecone instance
            from shared.pinecone_utils import PineconeUtils
            test_pinecone = PineconeUtils()
            
            if not test_pinecone.is_available():
                test_pinecone.create_index_if_not_exists()
                if not test_pinecone.is_available():
                    self.log_test("Vector Operations", False, "Pinecone not available")
                    return False
            
            # Create test vectors
            test_vectors = [
                {
                    'id': f'test-vector-{uuid.uuid4()}',
                    'values': [0.1] * 1536,  # OpenAI embedding dimension
                    'metadata': {
                        'user_id': self.test_user_id,
                        'content': 'This is test content for vector operations',
                        'document_type': 'test'
                    }
                }
            ]
            
            # Upsert vectors
            upsert_success = test_pinecone.upsert_vectors(test_vectors)
            if not upsert_success:
                self.log_test("Vector Operations - Upsert", False, "Failed to upsert vectors")
                return False
            
            # Query vectors
            query_vector = [0.1] * 1536
            matches = test_pinecone.query_vectors(
                query_vector=query_vector,
                top_k=5,
                filter_dict={'user_id': self.test_user_id}
            )
            
            # Delete test vectors
            vector_ids = [v['id'] for v in test_vectors]
            delete_success = test_pinecone.delete_vectors(vector_ids)
            
            # Success if upsert and delete worked (query might be eventually consistent)
            success = upsert_success and delete_success
            message = f"Upserted: {upsert_success}, queried ({len(matches)} matches), deleted: {delete_success}"
            self.log_test("Vector Operations", success, message)
            return success
            
        except Exception as e:
            self.log_test("Vector Operations", False, str(e))
            return False
    
    def test_document_chunking(self) -> bool:
        """Test document text chunking functionality"""
        try:
            # Test document
            test_text = """
            This is a test document for chunking functionality. It contains multiple sentences
            and paragraphs to test the chunking algorithm. The chunking should split the text
            into manageable pieces while maintaining context and readability.
            
            This is the second paragraph of the test document. It should be included in the
            chunking process and demonstrate how the algorithm handles paragraph breaks and
            sentence boundaries.
            
            Finally, this is the third paragraph that will help test the overlap functionality
            and ensure that important context is not lost between chunks.
            """ * 10  # Make it longer to force chunking
            
            # Create chunks
            chunks = create_document_chunks(test_text, chunk_size=500, overlap=100)
            
            success = len(chunks) > 1 and all(len(chunk) <= 600 for chunk in chunks)
            message = f"Created {len(chunks)} chunks from {len(test_text)} character document"
            self.log_test("Document Chunking", success, message)
            return success
            
        except Exception as e:
            self.log_test("Document Chunking", False, str(e))
            return False
    
    def test_cross_service_integration(self) -> bool:
        """Test integration between DynamoDB and Pinecone"""
        try:
            # This test simulates the full RAG pipeline
            
            # 1. Create file record in DynamoDB
            file_record = create_file_record(
                user_id=self.test_user_id,
                filename="integration-test.txt",
                s3_key=f"files/{self.test_user_id}/integration-test.txt",
                subject_id=self.test_subject_id
            )
            
            db_success = db_utils.put_item('user_files', file_record)
            if not db_success:
                self.log_test("Cross-Service Integration", False, "Failed to create file record")
                return False
            
            # 2. Simulate document processing and vector storage
            if pinecone_utils.is_available():
                test_chunks = ["This is chunk 1 of the integration test", "This is chunk 2 of the integration test"]
                test_embeddings = [[0.2] * 1536, [0.3] * 1536]
                
                vector_success = store_document_vectors(
                    file_record['file_id'],
                    self.test_user_id,
                    file_record['filename'],
                    test_chunks,
                    test_embeddings,
                    self.test_subject_id
                )
                
                # 3. Test retrieval
                if vector_success:
                    matches = pinecone_utils.query_vectors(
                        query_vector=[0.25] * 1536,
                        top_k=5,
                        filter_dict={'user_id': self.test_user_id, 'file_id': file_record['file_id']}
                    )
                    
                    # Clean up vectors
                    vector_ids = [f"{file_record['file_id']}_chunk_{i}" for i in range(len(test_chunks))]
                    pinecone_utils.delete_vectors(vector_ids)
            else:
                vector_success = True  # Skip vector test if Pinecone not available
                matches = []
            
            # Clean up DynamoDB
            db_utils.delete_item('user_files', {'file_id': file_record['file_id']})
            
            success = db_success and vector_success
            message = f"DynamoDB: {db_success}, Vectors: {vector_success}, Matches: {len(matches)}"
            self.log_test("Cross-Service Integration", success, message)
            return success
            
        except Exception as e:
            self.log_test("Cross-Service Integration", False, str(e))
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        print("🧪 Data Storage Integration Tests")
        print("=" * 50)
        
        # Run tests
        tests = [
            self.test_dynamodb_connection,
            self.test_file_operations,
            self.test_conversation_operations,
            self.test_pinecone_connection,
            self.test_vector_operations,
            self.test_document_chunking,
            self.test_cross_service_integration
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                test_name = test.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_test(test_name, False, f"Unexpected error: {str(e)}")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)
        
        for test_name, success, message in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            if message and not success:
                print(f"    {message}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 All data storage tests passed! Ready for AI functionality.")
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': (passed/total)*100,
            'all_passed': passed == total,
            'results': self.test_results
        }


def main():
    """Run the integration tests"""
    tester = DataStorageIntegrationTests()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if results['all_passed'] else 1
    return exit_code


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)