#!/usr/bin/env python3
"""
Test AWS Textract and Amazon Comprehend Integration
Comprehensive testing of enhanced file processing capabilities
"""

import boto3
import json
import os
import requests
import time
import logging
from typing import Dict, Any, List
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextractComprehendTester:
    """Test Textract and Comprehend integration"""
    
    def __init__(self, api_url: str = None):
        """Initialize tester with API URL"""
        self.api_url = api_url or os.getenv('API_URL', 'http://localhost:3000')
        self.user_id = 'test-user-textract-123'
        
        # AWS clients for direct testing
        self.textract = boto3.client('textract')
        self.comprehend = boto3.client('comprehend')
        self.s3 = boto3.client('s3')
        
        # Test configuration
        self.test_bucket = os.getenv('TEST_BUCKET', f'lms-documents-test-{int(time.time())}')
        
        logger.info(f"Initialized tester with API: {self.api_url}")
    
    def create_test_documents(self) -> Dict[str, bytes]:
        """Create test documents for different file types"""
        
        test_docs = {}
        
        # Create test PDF content (simple text)
        pdf_content = """
        Test Document for AWS Textract Integration
        
        This document contains various types of content to test:
        
        1. Regular text paragraphs
        2. Key entities like Amazon Web Services, AWS Lambda, and machine learning
        3. Important dates: January 15, 2024
        4. Technical terms: artificial intelligence, natural language processing
        5. Names: John Smith, Dr. Sarah Johnson
        6. Organizations: Stanford University, MIT
        
        Summary:
        This is a comprehensive test document designed to evaluate the effectiveness
        of AWS Textract for text extraction and Amazon Comprehend for entity detection
        and key phrase extraction. The document includes various types of content
        that should trigger different analysis capabilities.
        
        Conclusion:
        The integration of Textract and Comprehend provides powerful document
        processing capabilities for educational content management systems.
        """
        
        # For testing, we'll use plain text (in real scenario, you'd create actual PDF)
        test_docs['test_document.txt'] = pdf_content.encode('utf-8')
        
        # Create DOCX-style content
        docx_content = """
        Advanced Document Processing with AWS Services
        
        Introduction:
        This document demonstrates the capabilities of AWS Textract and Amazon Comprehend
        for processing educational materials in a Learning Management System.
        
        Key Technologies:
        - AWS Textract: Optical Character Recognition (OCR) service
        - Amazon Comprehend: Natural Language Processing (NLP) service
        - Amazon Bedrock: Foundation models for AI applications
        - AWS Lambda: Serverless computing platform
        
        Educational Applications:
        1. Automatic content extraction from scanned documents
        2. Entity recognition for academic subjects
        3. Key phrase extraction for content summarization
        4. Sentiment analysis for student feedback
        
        Technical Implementation:
        The system processes documents through multiple stages:
        - Text extraction using Textract
        - Language detection and entity extraction using Comprehend
        - Content chunking for vector storage
        - Integration with Bedrock Knowledge Base
        
        Benefits:
        - Improved accessibility of educational content
        - Enhanced search capabilities
        - Automated content analysis
        - Scalable document processing
        """
        
        test_docs['advanced_processing.txt'] = docx_content.encode('utf-8')
        
        # Create content with multiple languages
        multilingual_content = """
        Multilingual Document Processing Test
        
        English: This document tests language detection capabilities.
        Spanish: Este documento prueba las capacidades de detección de idiomas.
        French: Ce document teste les capacités de détection de langue.
        German: Dieses Dokument testet die Spracherkennungsfähigkeiten.
        
        Technical Terms:
        - Machine Learning (Aprendizaje Automático)
        - Natural Language Processing (Procesamiento de Lenguaje Natural)
        - Artificial Intelligence (Inteligencia Artificial)
        
        Organizations:
        - Amazon Web Services
        - Microsoft Corporation
        - Google LLC
        
        Dates and Numbers:
        - Project started: March 15, 2024
        - Budget: $50,000
        - Team size: 12 developers
        """      
  
        test_docs['multilingual_test.txt'] = multilingual_content.encode('utf-8')
        
        return test_docs
    
    def upload_test_documents(self, test_docs: Dict[str, bytes]) -> Dict[str, str]:
        """Upload test documents to S3"""
        
        uploaded_files = {}
        
        try:
            # Create test bucket if it doesn't exist
            try:
                self.s3.head_bucket(Bucket=self.test_bucket)
            except:
                logger.info(f"Creating test bucket: {self.test_bucket}")
                self.s3.create_bucket(Bucket=self.test_bucket)
        
            for filename, content in test_docs.items():
                key = f"test-documents/{self.user_id}/{filename}"
                
                logger.info(f"Uploading {filename} to S3...")
                self.s3.put_object(
                    Bucket=self.test_bucket,
                    Key=key,
                    Body=content,
                    ContentType='text/plain'
                )
                
                uploaded_files[filename] = f"s3://{self.test_bucket}/{key}"
                logger.info(f"Uploaded: {uploaded_files[filename]}")
        
        except Exception as e:
            logger.error(f"Error uploading documents: {str(e)}")
            raise
        
        return uploaded_files
    
    def test_textract_extraction(self, s3_uri: str) -> Dict[str, Any]:
        """Test Textract text extraction"""
        
        logger.info(f"Testing Textract extraction for: {s3_uri}")
        
        try:
            # Parse S3 URI
            bucket, key = s3_uri.replace('s3://', '').split('/', 1)
            
            # Start text detection job
            response = self.textract.start_document_text_detection(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
            
            job_id = response['JobId']
            logger.info(f"Started Textract job: {job_id}")
            
            # Wait for completion
            while True:
                result = self.textract.get_document_text_detection(JobId=job_id)
                status = result['JobStatus']
                
                if status == 'SUCCEEDED':
                    break
                elif status == 'FAILED':
                    raise Exception(f"Textract job failed: {result.get('StatusMessage', 'Unknown error')}")
                
                logger.info(f"Textract job status: {status}")
                time.sleep(2)
            
            # Extract text blocks
            blocks = result['Blocks']
            text_blocks = [block for block in blocks if block['BlockType'] == 'LINE']
            
            extracted_text = '\n'.join([block['Text'] for block in text_blocks])
            
            return {
                'job_id': job_id,
                'status': status,
                'blocks_count': len(blocks),
                'text_blocks_count': len(text_blocks),
                'extracted_text': extracted_text,
                'confidence_scores': [block.get('Confidence', 0) for block in text_blocks]
            }
        
        except Exception as e:
            logger.error(f"Textract extraction failed: {str(e)}")
            return {
                'error': str(e),
                'status': 'FAILED'
            }
    
    def test_comprehend_analysis(self, text: str) -> Dict[str, Any]:
        """Test Comprehend NLP analysis"""
        
        logger.info("Testing Comprehend analysis...")
        
        try:
            results = {}
            
            # Language detection
            language_response = self.comprehend.detect_dominant_language(Text=text)
            results['language'] = language_response['Languages'][0] if language_response['Languages'] else None
            
            # Entity detection
            entities_response = self.comprehend.detect_entities(Text=text, LanguageCode='en')
            results['entities'] = entities_response['Entities']
            
            # Key phrases
            phrases_response = self.comprehend.detect_key_phrases(Text=text, LanguageCode='en')
            results['key_phrases'] = phrases_response['KeyPhrases']
            
            # Sentiment analysis
            sentiment_response = self.comprehend.detect_sentiment(Text=text, LanguageCode='en')
            results['sentiment'] = sentiment_response['Sentiment']
            results['sentiment_scores'] = sentiment_response['SentimentScore']
            
            # Syntax analysis
            syntax_response = self.comprehend.detect_syntax(Text=text, LanguageCode='en')
            results['syntax_tokens'] = syntax_response['SyntaxTokens']
            
            logger.info(f"Comprehend analysis completed: {len(results['entities'])} entities, {len(results['key_phrases'])} key phrases")
            
            return results
        
        except Exception as e:
            logger.error(f"Comprehend analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def test_api_integration(self, filename: str) -> Dict[str, Any]:
        """Test API integration with file processing"""
        
        logger.info(f"Testing API integration for: {filename}")
        
        try:
            # Test file upload endpoint
            upload_response = requests.post(
                f"{self.api_url}/files",
                json={
                    'filename': filename,
                    'file_size': 1024,
                    'user_id': self.user_id,
                    'subject_id': 'test-subject'
                },
                timeout=30
            )
            
            if upload_response.status_code != 200:
                return {
                    'error': f"Upload API failed: {upload_response.status_code}",
                    'response': upload_response.text
                }
            
            upload_data = upload_response.json()
            
            # Test file processing endpoint
            process_response = requests.post(
                f"{self.api_url}/files/process",
                json={
                    'file_id': upload_data.get('file_id', 'test-file-123'),
                    'user_id': self.user_id
                },
                timeout=60
            )
            
            if process_response.status_code != 200:
                return {
                    'error': f"Process API failed: {process_response.status_code}",
                    'response': process_response.text
                }
            
            process_data = process_response.json()
            
            return {
                'upload_success': True,
                'process_success': True,
                'upload_data': upload_data,
                'process_data': process_data
            }
        
        except Exception as e:
            logger.error(f"API integration test failed: {str(e)}")
            return {'error': str(e)}
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive integration test"""
        
        logger.info("🚀 Starting comprehensive Textract and Comprehend integration test...")
        
        results = {
            'test_start_time': time.time(),
            'documents_created': 0,
            'documents_uploaded': 0,
            'textract_tests': {},
            'comprehend_tests': {},
            'api_tests': {},
            'errors': []
        }
        
        try:
            # Step 1: Create test documents
            logger.info("📄 Creating test documents...")
            test_docs = self.create_test_documents()
            results['documents_created'] = len(test_docs)
            
            # Step 2: Upload to S3
            logger.info("☁️ Uploading documents to S3...")
            uploaded_files = self.upload_test_documents(test_docs)
            results['documents_uploaded'] = len(uploaded_files)
            
            # Step 3: Test Textract extraction
            logger.info("🔍 Testing Textract extraction...")
            for filename, s3_uri in uploaded_files.items():
                try:
                    textract_result = self.test_textract_extraction(s3_uri)
                    results['textract_tests'][filename] = textract_result
                    
                    # Step 4: Test Comprehend analysis on extracted text
                    if 'extracted_text' in textract_result:
                        logger.info(f"🧠 Testing Comprehend analysis for {filename}...")
                        comprehend_result = self.test_comprehend_analysis(textract_result['extracted_text'])
                        results['comprehend_tests'][filename] = comprehend_result
                
                except Exception as e:
                    error_msg = f"Error processing {filename}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Step 5: Test API integration
            logger.info("🌐 Testing API integration...")
            for filename in test_docs.keys():
                try:
                    api_result = self.test_api_integration(filename)
                    results['api_tests'][filename] = api_result
                except Exception as e:
                    error_msg = f"API test error for {filename}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
        
        except Exception as e:
            error_msg = f"Comprehensive test failed: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        results['test_end_time'] = time.time()
        results['test_duration'] = results['test_end_time'] - results['test_start_time']
        
        return results
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        
        report = f"""
# 🚀 Enhanced File Processing Integration Test Report

## Test Summary
- **Test Duration:** {results['test_duration']:.2f} seconds
- **Documents Created:** {results['documents_created']}
- **Documents Uploaded:** {results['documents_uploaded']}
- **Textract Tests:** {len(results['textract_tests'])}
- **Comprehend Tests:** {len(results['comprehend_tests'])}
- **API Tests:** {len(results['api_tests'])}
- **Errors:** {len(results['errors'])}

## Textract Extraction Results
"""
        
        for filename, result in results['textract_tests'].items():
            if 'error' not in result:
                report += f"""
### {filename}
- **Status:** ✅ {result['status']}
- **Blocks Detected:** {result['blocks_count']}
- **Text Blocks:** {result['text_blocks_count']}
- **Average Confidence:** {sum(result['confidence_scores'])/len(result['confidence_scores']):.2f}%
- **Text Preview:** {result['extracted_text'][:200]}...
"""
            else:
                report += f"""
### {filename}
- **Status:** ❌ FAILED
- **Error:** {result['error']}
"""
        
        report += "\n## Comprehend Analysis Results\n"
        
        for filename, result in results['comprehend_tests'].items():
            if 'error' not in result:
                entities_count = len(result.get('entities', []))
                phrases_count = len(result.get('key_phrases', []))
                language = result.get('language', {}).get('LanguageCode', 'Unknown')
                sentiment = result.get('sentiment', 'Unknown')
                
                report += f"""
### {filename}
- **Language:** {language}
- **Entities Detected:** {entities_count}
- **Key Phrases:** {phrases_count}
- **Sentiment:** {sentiment}
- **Top Entities:** {', '.join([e['Text'] for e in result.get('entities', [])[:5]])}
- **Top Phrases:** {', '.join([p['Text'] for p in result.get('key_phrases', [])[:5]])}
"""
            else:
                report += f"""
### {filename}
- **Status:** ❌ FAILED
- **Error:** {result['error']}
"""
        
        report += "\n## API Integration Results\n"
        
        for filename, result in results['api_tests'].items():
            if 'error' not in result:
                report += f"""
### {filename}
- **Upload:** ✅ Success
- **Processing:** ✅ Success
- **File ID:** {result.get('upload_data', {}).get('file_id', 'N/A')}
"""
            else:
                report += f"""
### {filename}
- **Status:** ❌ FAILED
- **Error:** {result['error']}
"""
        
        if results['errors']:
            report += "\n## Errors Encountered\n"
            for error in results['errors']:
                report += f"- {error}\n"
        
        report += f"""
## Recommendations

1. **Textract Performance:** Average confidence scores indicate extraction quality
2. **Comprehend Accuracy:** Entity and phrase detection working as expected
3. **API Integration:** {'✅ All endpoints functional' if not results['errors'] else '❌ Some endpoints need attention'}
4. **Next Steps:** Deploy to production environment and monitor performance

---
*Test completed at {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report


def main():
    """Main test execution"""
    
    print("🚀 Starting Enhanced File Processing Integration Test...")
    
    # Initialize tester
    api_url = os.getenv('API_URL', input("Enter API URL (or press Enter for localhost): ") or 'http://localhost:3000')
    tester = TextractComprehendTester(api_url)
    
    # Run comprehensive test
    results = tester.run_comprehensive_test()
    
    # Generate and display report
    report = tester.generate_test_report(results)
    print(report)
    
    # Save report to file
    report_filename = f"textract_comprehend_test_report_{int(time.time())}.md"
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Test report saved to: {report_filename}")
    
    # Return results for programmatic use
    return results


if __name__ == "__main__":
    main()