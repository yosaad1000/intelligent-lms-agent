#!/usr/bin/env python3
"""
Test LangGraph AI Agent Chat Implementation
Comprehensive testing for intelligent document summarization
"""

import json
import requests
import time
import os
from datetime import datetime
from typing import Dict, Any, List

# Test configuration
API_BASE_URL = "https://your-api-id.execute-api.us-east-1.amazonaws.com/dev"
TEST_USER_ID = "test-user-langgraph-123"
TEST_SUBJECT_ID = "physics-101"

class LangGraphChatTester:
    """Test suite for LangGraph AI Agent Chat"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"[{timestamp}] {status} {test_name}"
        if details:
            message += f" - {details}"
        print(message)
        
        self.test_results.append({
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': timestamp
        })
    
    def test_intent_detection(self) -> bool:
        """Test intent detection with different message types"""
        
        print("\n🧠 Testing Intent Detection...")
        
        test_cases = [
            {
                'message': 'Can you summarize my physics notes?',
                'expected_intent': 'summarize',
                'description': 'Summarization intent'
            },
            {
                'message': 'What is Newton\'s first law?',
                'expected_intent': 'question',
                'description': 'Question intent'
            },
            {
                'message': 'Translate this to Spanish',
                'expected_intent': 'translate',
                'description': 'Translation intent'
            },
            {
                'message': 'Hello, how are you?',
                'expected_intent': 'general',
                'description': 'General conversation'
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            try:
                response = self.send_chat_message(test_case['message'])
                
                if response and response.get('success'):
                    detected_intent = response.get('intent_detected', '')
                    expected_intent = test_case['expected_intent']
                    
                    if detected_intent == expected_intent:
                        self.log_test(
                            f"Intent Detection - {test_case['description']}", 
                            True, 
                            f"Detected: {detected_intent}"
                        )
                    else:
                        self.log_test(
                            f"Intent Detection - {test_case['description']}", 
                            False, 
                            f"Expected: {expected_intent}, Got: {detected_intent}"
                        )
                        all_passed = False
                else:
                    self.log_test(
                        f"Intent Detection - {test_case['description']}", 
                        False, 
                        "No response or failed request"
                    )
                    all_passed = False
                    
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                self.log_test(
                    f"Intent Detection - {test_case['description']}", 
                    False, 
                    f"Error: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    def test_document_summarization(self) -> bool:
        """Test document summarization with different summary types"""
        
        print("\n📄 Testing Document Summarization...")
        
        summary_tests = [
            {
                'message': 'Give me a brief summary of my notes',
                'summary_type': 'brief',
                'description': 'Brief summary request'
            },
            {
                'message': 'Provide a detailed summary of the uploaded documents',
                'summary_type': 'detailed',
                'description': 'Detailed summary request'
            },
            {
                'message': 'I need a comprehensive overview of all my materials',
                'summary_type': 'comprehensive',
                'description': 'Comprehensive summary request'
            },
            {
                'message': 'Summarize my physics notes',
                'summary_type': 'standard',
                'description': 'Standard summary request'
            }
        ]
        
        all_passed = True
        
        for test in summary_tests:
            try:
                response = self.send_chat_message(test['message'], TEST_SUBJECT_ID)
                
                if response and response.get('success'):
                    intent = response.get('intent_detected', '')
                    summary_type = response.get('summary_type', '')
                    tools_used = response.get('tools_used', [])
                    response_text = response.get('response', '')
                    
                    # Check if summarization was detected
                    if intent == 'summarize':
                        self.log_test(
                            f"Summarization - {test['description']} (Intent)", 
                            True, 
                            f"Intent: {intent}, Type: {summary_type}"
                        )
                        
                        # Check if appropriate tools were used
                        expected_tools = ['intent_detection', 'document_processing', 'summarization']
                        tools_found = any(tool in tools_used for tool in expected_tools)
                        
                        self.log_test(
                            f"Summarization - {test['description']} (Tools)", 
                            tools_found, 
                            f"Tools used: {tools_used}"
                        )
                        
                        # Check response quality
                        has_content = len(response_text) > 50
                        self.log_test(
                            f"Summarization - {test['description']} (Content)", 
                            has_content, 
                            f"Response length: {len(response_text)} chars"
                        )
                        
                        if not (tools_found and has_content):
                            all_passed = False
                    else:
                        self.log_test(
                            f"Summarization - {test['description']}", 
                            False, 
                            f"Expected summarize intent, got: {intent}"
                        )
                        all_passed = False
                else:
                    self.log_test(
                        f"Summarization - {test['description']}", 
                        False, 
                        "No response or failed request"
                    )
                    all_passed = False
                    
                time.sleep(2)  # Longer delay for processing
                
            except Exception as e:
                self.log_test(
                    f"Summarization - {test['description']}", 
                    False, 
                    f"Error: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    def test_rag_retrieval(self) -> bool:
        """Test RAG retrieval and question answering"""
        
        print("\n🔍 Testing RAG Retrieval and Question Answering...")
        
        question_tests = [
            {
                'message': 'What are the main concepts in my physics notes?',
                'description': 'Concept extraction question'
            },
            {
                'message': 'Explain the key points from my uploaded documents',
                'description': 'Key points question'
            },
            {
                'message': 'How does this relate to what I studied before?',
                'description': 'Contextual question'
            },
            {
                'message': 'Can you find information about Newton\'s laws in my files?',
                'description': 'Specific topic search'
            }
        ]
        
        all_passed = True
        
        for test in question_tests:
            try:
                response = self.send_chat_message(test['message'], TEST_SUBJECT_ID)
                
                if response and response.get('success'):
                    intent = response.get('intent_detected', '')
                    tools_used = response.get('tools_used', [])
                    rag_docs_used = response.get('rag_documents_used', 0)
                    citations = response.get('citations', [])
                    
                    # Check if question answering was triggered
                    if intent in ['question', 'general']:
                        self.log_test(
                            f"RAG - {test['description']} (Intent)", 
                            True, 
                            f"Intent: {intent}"
                        )
                        
                        # Check if RAG retrieval was used
                        rag_used = 'rag_retrieval' in tools_used
                        self.log_test(
                            f"RAG - {test['description']} (Retrieval)", 
                            rag_used, 
                            f"RAG docs: {rag_docs_used}, Citations: {len(citations)}"
                        )
                        
                        # Check if question answering was used
                        qa_used = 'question_answering' in tools_used
                        self.log_test(
                            f"RAG - {test['description']} (QA)", 
                            qa_used, 
                            f"Tools: {tools_used}"
                        )
                        
                        if not (rag_used and qa_used):
                            all_passed = False
                    else:
                        self.log_test(
                            f"RAG - {test['description']}", 
                            False, 
                            f"Unexpected intent: {intent}"
                        )
                        all_passed = False
                else:
                    self.log_test(
                        f"RAG - {test['description']}", 
                        False, 
                        "No response or failed request"
                    )
                    all_passed = False
                    
                time.sleep(2)
                
            except Exception as e:
                self.log_test(
                    f"RAG - {test['description']}", 
                    False, 
                    f"Error: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    def test_language_detection(self) -> bool:
        """Test language detection and translation"""
        
        print("\n🌍 Testing Language Detection and Translation...")
        
        language_tests = [
            {
                'message': 'Hello, how are you today?',
                'expected_language': 'en',
                'description': 'English detection'
            },
            {
                'message': 'Hola, ¿cómo estás?',
                'expected_language': 'es',
                'description': 'Spanish detection'
            },
            {
                'message': 'Translate this to Spanish please',
                'expected_language': 'en',
                'description': 'Translation request'
            }
        ]
        
        all_passed = True
        
        for test in language_tests:
            try:
                response = self.send_chat_message(test['message'])
                
                if response and response.get('success'):
                    detected_language = response.get('language_detected', '')
                    expected_language = test['expected_language']
                    
                    if detected_language == expected_language:
                        self.log_test(
                            f"Language - {test['description']}", 
                            True, 
                            f"Detected: {detected_language}"
                        )
                    else:
                        self.log_test(
                            f"Language - {test['description']}", 
                            False, 
                            f"Expected: {expected_language}, Got: {detected_language}"
                        )
                        all_passed = False
                else:
                    self.log_test(
                        f"Language - {test['description']}", 
                        False, 
                        "No response or failed request"
                    )
                    all_passed = False
                    
                time.sleep(1)
                
            except Exception as e:
                self.log_test(
                    f"Language - {test['description']}", 
                    False, 
                    f"Error: {str(e)}"
                )
                all_passed = False
        
        return all_passed
    
    def test_workflow_orchestration(self) -> bool:
        """Test LangGraph workflow orchestration"""
        
        print("\n⚙️ Testing Workflow Orchestration...")
        
        try:
            # Test complex workflow with multiple steps
            response = self.send_chat_message(
                "Can you analyze my documents and give me a detailed summary with key insights?",
                TEST_SUBJECT_ID
            )
            
            if response and response.get('success'):
                # Check workflow metadata
                langgraph_used = response.get('langgraph_workflow', False)
                workflow_version = response.get('workflow_version', '')
                tools_used = response.get('tools_used', [])
                processing_metadata = response.get('processing_metadata', {})
                
                self.log_test(
                    "Workflow - LangGraph Usage", 
                    langgraph_used, 
                    f"Version: {workflow_version}"
                )
                
                # Check if multiple tools were orchestrated
                expected_tools = ['language_detection', 'intent_detection', 'document_processing', 'summarization', 'response_synthesis']
                tools_found = sum(1 for tool in expected_tools if tool in tools_used)
                
                self.log_test(
                    "Workflow - Tool Orchestration", 
                    tools_found >= 3, 
                    f"Tools used: {tools_found}/5 - {tools_used}"
                )
                
                # Check processing metadata
                has_metadata = bool(processing_metadata)
                self.log_test(
                    "Workflow - Processing Metadata", 
                    has_metadata, 
                    f"Metadata keys: {list(processing_metadata.keys())}"
                )
                
                return langgraph_used and tools_found >= 3 and has_metadata
            else:
                self.log_test(
                    "Workflow - Orchestration", 
                    False, 
                    "No response or failed request"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Workflow - Orchestration", 
                False, 
                f"Error: {str(e)}"
            )
            return False
    
    def test_conversation_history(self) -> bool:
        """Test conversation history functionality"""
        
        print("\n💬 Testing Conversation History...")
        
        try:
            # Get conversation history
            response = requests.get(
                f"{self.api_url}/chat/history",
                params={'user_id': TEST_USER_ID, 'limit': 10},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                conversations = data.get('conversations', [])
                
                self.log_test(
                    "History - Retrieval", 
                    True, 
                    f"Found {len(conversations)} conversations"
                )
                
                # Check if any conversations have LangGraph metadata
                langgraph_conversations = [
                    conv for conv in conversations 
                    if conv.get('workflow_version')
                ]
                
                self.log_test(
                    "History - LangGraph Metadata", 
                    len(langgraph_conversations) > 0, 
                    f"LangGraph conversations: {len(langgraph_conversations)}"
                )
                
                return True
            else:
                self.log_test(
                    "History - Retrieval", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "History - Retrieval", 
                False, 
                f"Error: {str(e)}"
            )
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling and fallback mechanisms"""
        
        print("\n🛡️ Testing Error Handling...")
        
        error_tests = [
            {
                'message': '',  # Empty message
                'description': 'Empty message handling'
            },
            {
                'message': 'x' * 10000,  # Very long message
                'description': 'Long message handling'
            }
        ]
        
        all_passed = True
        
        for test in error_tests:
            try:
                response = self.send_chat_message(test['message'])
                
                # Should either succeed with fallback or return proper error
                if response:
                    if response.get('success') or 'error' in response:
                        self.log_test(
                            f"Error Handling - {test['description']}", 
                            True, 
                            f"Handled gracefully"
                        )
                    else:
                        self.log_test(
                            f"Error Handling - {test['description']}", 
                            False, 
                            "Unexpected response format"
                        )
                        all_passed = False
                else:
                    self.log_test(
                        f"Error Handling - {test['description']}", 
                        False, 
                        "No response"
                    )
                    all_passed = False
                    
                time.sleep(1)
                
            except Exception as e:
                # Exceptions are expected for some error cases
                self.log_test(
                    f"Error Handling - {test['description']}", 
                    True, 
                    f"Exception handled: {type(e).__name__}"
                )
        
        return all_passed
    
    def send_chat_message(self, message: str, subject_id: str = None) -> Dict[str, Any]:
        """Send chat message to API"""
        
        payload = {
            'user_id': TEST_USER_ID,
            'message': message
        }
        
        if subject_id:
            payload['subject_id'] = subject_id
        
        try:
            response = self.session.post(
                f"{self.api_url}/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        
        print("🚀 Starting LangGraph AI Agent Chat Tests")
        print(f"📡 API URL: {self.api_url}")
        print(f"👤 Test User: {TEST_USER_ID}")
        print("=" * 60)
        
        # Run test suites
        test_suites = [
            ('Intent Detection', self.test_intent_detection),
            ('Document Summarization', self.test_document_summarization),
            ('RAG Retrieval', self.test_rag_retrieval),
            ('Language Detection', self.test_language_detection),
            ('Workflow Orchestration', self.test_workflow_orchestration),
            ('Conversation History', self.test_conversation_history),
            ('Error Handling', self.test_error_handling)
        ]
        
        suite_results = {}
        
        for suite_name, test_function in test_suites:
            try:
                result = test_function()
                suite_results[suite_name] = result
                print(f"\n{suite_name}: {'✅ PASSED' if result else '❌ FAILED'}")
            except Exception as e:
                suite_results[suite_name] = False
                print(f"\n{suite_name}: ❌ FAILED - {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Suite summary
        print(f"\nTest Suites:")
        for suite_name, result in suite_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {suite_name}: {status}")
        
        # Failed tests detail
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'suite_results': suite_results,
            'test_details': self.test_results
        }

def main():
    """Main test function"""
    
    # Get API URL from environment or use default
    api_url = os.getenv('LANGGRAPH_API_URL', API_BASE_URL)
    
    if 'your-api-id' in api_url:
        print("❌ Please update API_BASE_URL with your actual API Gateway URL")
        print("You can find it in the deployment output or AWS Console")
        return
    
    # Run tests
    tester = LangGraphChatTester(api_url)
    results = tester.run_all_tests()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"langgraph_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    if results['success_rate'] >= 80:
        print("\n🎉 LangGraph AI Agent Chat tests completed successfully!")
        exit(0)
    else:
        print("\n⚠️ Some tests failed. Please check the results and fix issues.")
        exit(1)

if __name__ == "__main__":
    main()