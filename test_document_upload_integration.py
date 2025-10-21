"""
Test Document Upload Integration with Real AWS Services
Tests the complete document upload and processing workflow
"""

import json
import requests
import time
import os
from typing import Dict, Any

class DocumentUploadTester:
    def __init__(self):
        self.api_base_url = "https://7k21xsoz93.execute-api.us-east-1.amazonaws.com/dev"
        self.test_user_id = "test-user-document-integration"
        
    def test_complete_document_workflow(self):
        """Test the complete document upload and processing workflow"""
        print("🚀 Starting Document Upload Integration Test")
        
        # Step 1: Test presigned URL generation
        print("\n📝 Step 1: Testing presigned URL generation...")
        presigned_result = self.test_presigned_url_generation()
        if not presigned_result['success']:
            print(f"❌ Presigned URL generation failed: {presigned_result['error']}")
            return False
        
        print(f"✅ Presigned URL generated successfully")
        
        # Step 2: Test file upload to S3
        print("\n📤 Step 2: Testing file upload to S3...")
        upload_result = self.test_file_upload_to_s3(presigned_result)
        if not upload_result['success']:
            print(f"❌ File upload failed: {upload_result['error']}")
            return False
        
        print(f"✅ File uploaded to S3 successfully")
        
        # Step 3: Test document processing
        print("\n🔄 Step 3: Testing document processing...")
        processing_result = self.test_document_processing(presigned_result['file_key'])
        if not processing_result['success']:
            print(f"❌ Document processing failed: {processing_result['error']}")
            return False
        
        print(f"✅ Document processed successfully")
        print(f"   - Extracted text length: {len(processing_result.get('metadata', {}).get('extracted_text', ''))}")
        print(f"   - Entities found: {len(processing_result.get('metadata', {}).get('entities', []))}")
        print(f"   - Key phrases: {len(processing_result.get('metadata', {}).get('key_phrases', []))}")
        
        # Step 4: Test document listing
        print("\n📋 Step 4: Testing document listing...")
        list_result = self.test_document_listing()
        if not list_result['success']:
            print(f"❌ Document listing failed: {list_result['error']}")
            return False
        
        print(f"✅ Document listing successful")
        print(f"   - Documents found: {len(list_result.get('documents', []))}")
        
        # Step 5: Test Bedrock Agent integration
        print("\n🤖 Step 5: Testing Bedrock Agent integration...")
        agent_result = self.test_bedrock_agent_integration()
        if not agent_result['success']:
            print(f"❌ Bedrock Agent integration failed: {agent_result['error']}")
            return False
        
        print(f"✅ Bedrock Agent integration successful")
        print(f"   - Response length: {len(agent_result.get('response', ''))}")
        
        print("\n🎉 All tests passed! Document processing integration is working correctly.")
        return True
    
    def test_presigned_url_generation(self) -> Dict[str, Any]:
        """Test presigned URL generation"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/v1/upload/presigned",
                json={
                    "file_name": "test-document.pdf",
                    "content_type": "application/pdf",
                    "user_id": self.test_user_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {
                        'success': True,
                        'upload_url': data['upload_url'],
                        'file_key': data['file_key'],
                        'file_id': data.get('file_id')
                    }
                else:
                    return {'success': False, 'error': data.get('error', 'Unknown error')}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_file_upload_to_s3(self, presigned_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test file upload to S3 using presigned URL"""
        try:
            # Create a test PDF content
            test_content = b"""
            %PDF-1.4
            1 0 obj
            <<
            /Type /Catalog
            /Pages 2 0 R
            >>
            endobj
            
            2 0 obj
            <<
            /Type /Pages
            /Kids [3 0 R]
            /Count 1
            >>
            endobj
            
            3 0 obj
            <<
            /Type /Page
            /Parent 2 0 R
            /MediaBox [0 0 612 792]
            /Contents 4 0 R
            >>
            endobj
            
            4 0 obj
            <<
            /Length 44
            >>
            stream
            BT
            /F1 12 Tf
            100 700 Td
            (This is a test document for AI processing) Tj
            ET
            endstream
            endobj
            
            xref
            0 5
            0000000000 65535 f 
            0000000009 00000 n 
            0000000074 00000 n 
            0000000120 00000 n 
            0000000179 00000 n 
            trailer
            <<
            /Size 5
            /Root 1 0 R
            >>
            startxref
            274
            %%EOF
            """
            
            # Upload to S3
            response = requests.put(
                presigned_data['upload_url'],
                data=test_content,
                headers={'Content-Type': 'application/pdf'},
                timeout=60
            )
            
            if response.status_code in [200, 204]:
                return {'success': True}
            else:
                return {'success': False, 'error': f"S3 upload failed: HTTP {response.status_code}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_document_processing(self, file_key: str) -> Dict[str, Any]:
        """Test document processing with Textract and Comprehend"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/v1/documents/process",
                json={
                    "file_key": file_key,
                    "user_id": self.test_user_id
                },
                timeout=120  # Processing can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {
                        'success': True,
                        'document_id': data.get('document_id'),
                        'metadata': data.get('metadata', {})
                    }
                else:
                    return {'success': False, 'error': data.get('error', 'Processing failed')}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_document_listing(self) -> Dict[str, Any]:
        """Test document listing"""
        try:
            response = requests.get(
                f"{self.api_base_url}/api/v1/documents",
                params={"user_id": self.test_user_id},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {
                        'success': True,
                        'documents': data.get('documents', []),
                        'count': data.get('count', 0)
                    }
                else:
                    return {'success': False, 'error': data.get('error', 'Listing failed')}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_bedrock_agent_integration(self) -> Dict[str, Any]:
        """Test Bedrock Agent integration with document context"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/v1/chat",
                json={
                    "message": "Summarize my uploaded test document",
                    "user_id": self.test_user_id,
                    "session_id": f"test-session-{int(time.time())}",
                    "context": {
                        "action": "document_summary",
                        "user_documents": True
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {
                        'success': True,
                        'response': data.get('response', ''),
                        'citations': data.get('citations', []),
                        'tools_used': data.get('tools_used', [])
                    }
                else:
                    return {'success': False, 'error': data.get('error', 'Agent failed')}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_quiz_generation(self) -> Dict[str, Any]:
        """Test quiz generation from document"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/v1/chat",
                json={
                    "message": "Generate a 3-question quiz from my uploaded document",
                    "user_id": self.test_user_id,
                    "session_id": f"quiz-session-{int(time.time())}",
                    "context": {
                        "action": "generate_quiz",
                        "question_count": 3
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {
                        'success': True,
                        'quiz': data.get('response', ''),
                        'citations': data.get('citations', [])
                    }
                else:
                    return {'success': False, 'error': data.get('error', 'Quiz generation failed')}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

def main():
    """Run the document upload integration test"""
    tester = DocumentUploadTester()
    
    print("=" * 60)
    print("🧪 DOCUMENT PROCESSING INTEGRATION TEST")
    print("=" * 60)
    
    success = tester.test_complete_document_workflow()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Document upload and processing integration is working correctly")
        print("✅ AWS Textract text extraction is functional")
        print("✅ Amazon Comprehend analysis is working")
        print("✅ Bedrock Agent integration is successful")
        print("=" * 60)
        
        # Optional: Test quiz generation
        print("\n🎯 Testing quiz generation...")
        quiz_result = tester.test_quiz_generation()
        if quiz_result['success']:
            print("✅ Quiz generation successful!")
            print(f"   Quiz preview: {quiz_result['quiz'][:200]}...")
        else:
            print(f"⚠️  Quiz generation failed: {quiz_result['error']}")
        
    else:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED!")
        print("Please check the error messages above and verify:")
        print("- AWS credentials are configured correctly")
        print("- API Gateway endpoints are deployed")
        print("- Lambda functions have proper permissions")
        print("- S3 bucket exists and is accessible")
        print("=" * 60)

if __name__ == "__main__":
    main()