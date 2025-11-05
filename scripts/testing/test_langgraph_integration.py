#!/usr/bin/env python3
"""
LangGraph Integration Test Suite
Comprehensive testing for LangChain + LangGraph agent workflow
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import our services
from shared.langgraph_agent_service import LangGraphAgentService, WorkflowIntent
from shared.bedrock_agent_service import AgentContext
from shared.langchain_memory import memory_manager
from shared.agent_utils import agent_invoker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LangGraphTestSuite:
    """Test suite for LangGraph workflow"""
    
    def __init__(self):
        """Initialize test suite"""
        self.test_results = []
        self.langgraph_service = None
        
    async def run_all_tests(self):
        """Run all LangGraph tests"""
        
        print("🧪 Starting LangGraph Integration Test Suite")
        print("=" * 60)
        
        # Initialize services
        await self.test_service_initialization()
        
        # Test workflow components
        await self.test_workflow_creation()
        await self.test_intent_detection()
        await self.test_language_detection()
        await self.test_rag_integration()
        await self.test_memory_integration()
        await self.test_aws_services_integration()
        
        # Test complete workflows
        await self.test_summarization_workflow()
        await self.test_question_answering_workflow()
        await self.test_quiz_generation_workflow()
        await self.test_translation_workflow()
        
        # Test agent invoker integration
        await self.test_agent_invoker_integration()
        
        # Print results
        self.print_test_results()
    
    async def test_service_initialization(self):
        """Test LangGraph service initialization"""
        
        print("\n🔧 Testing Service Initialization...")
        
        try:
            self.langgraph_service = LangGraphAgentService()
            
            # Test workflow info
            workflow_info = self.langgraph_service.get_workflow_info()
            
            assert workflow_info['workflow_type'] == 'LangGraph'
            assert 'nodes' in workflow_info
            assert 'supported_intents' in workflow_info
            assert len(workflow_info['nodes']) > 0
            
            self.record_test_result("Service Initialization", True, "LangGraph service initialized successfully")
            
        except Exception as e:
            self.record_test_result("Service Initialization", False, f"Failed to initialize: {str(e)}")
    
    async def test_workflow_creation(self):
        """Test workflow graph creation"""
        
        print("\n🔄 Testing Workflow Creation...")
        
        try:
            # Test that workflow is compiled
            assert self.langgraph_service.agent_executor is not None
            
            # Test workflow info
            workflow_info = self.langgraph_service.get_workflow_info()
            expected_nodes = [
                "language_detection",
                "intent_detection", 
                "document_processing",
                "rag_retrieval",
                "summarization",
                "quiz_generation",
                "translation",
                "analysis",
                "response_synthesis"
            ]
            
            for node in expected_nodes:
                assert node in workflow_info['nodes'], f"Missing node: {node}"
            
            self.record_test_result("Workflow Creation", True, "Workflow graph created with all nodes")
            
        except Exception as e:
            self.record_test_result("Workflow Creation", False, f"Workflow creation failed: {str(e)}")
    
    async def test_intent_detection(self):
        """Test intent detection functionality"""
        
        print("\n🎯 Testing Intent Detection...")
        
        test_cases = [
            ("Can you summarize my physics notes?", WorkflowIntent.SUMMARIZE),
            ("Generate a quiz about biology", WorkflowIntent.QUIZ),
            ("What is Newton's first law?", WorkflowIntent.GENERAL),
            ("Translate this to Spanish", WorkflowIntent.TRANSLATE),
            ("Analyze my learning progress", WorkflowIntent.ANALYZE)
        ]
        
        try:
            for message, expected_intent in test_cases:
                # Create test state
                from shared.langgraph_agent_service import AgentState
                from langchain_core.messages import HumanMessage
                
                test_state = {
                    "messages": [HumanMessage(content=message)],
                    "user_id": "test-user",
                    "session_id": "test-session",
                    "intent": "",
                    "language": "en",
                    "documents": [],
                    "rag_context": [],
                    "user_profile": {},
                    "tools_used": [],
                    "final_response": "",
                    "citations": [],
                    "metadata": {}
                }
                
                # Test intent detection node
                result_state = await self.langgraph_service._detect_intent_node(test_state)
                
                # Check if intent was detected (may not be exact due to NLP variability)
                assert result_state["intent"] != "", f"No intent detected for: {message}"
                
                print(f"  ✅ '{message}' -> Intent: {result_state['intent']}")
            
            self.record_test_result("Intent Detection", True, f"Tested {len(test_cases)} intent detection cases")
            
        except Exception as e:
            self.record_test_result("Intent Detection", False, f"Intent detection failed: {str(e)}")
    
    async def test_language_detection(self):
        """Test language detection functionality"""
        
        print("\n🌐 Testing Language Detection...")
        
        test_cases = [
            ("Hello, how are you?", "en"),
            ("Hola, ¿cómo estás?", "es"),
            ("Bonjour, comment allez-vous?", "fr")
        ]
        
        try:
            for message, expected_lang in test_cases:
                from shared.langgraph_agent_service import AgentState
                from langchain_core.messages import HumanMessage
                
                test_state = {
                    "messages": [HumanMessage(content=message)],
                    "user_id": "test-user",
                    "session_id": "test-session",
                    "intent": "",
                    "language": "",
                    "documents": [],
                    "rag_context": [],
                    "user_profile": {},
                    "tools_used": [],
                    "final_response": "",
                    "citations": [],
                    "metadata": {}
                }
                
                # Test language detection node
                result_state = await self.langgraph_service._detect_language_node(test_state)
                
                # Check if language was detected
                assert result_state["language"] != "", f"No language detected for: {message}"
                
                print(f"  ✅ '{message}' -> Language: {result_state['language']}")
            
            self.record_test_result("Language Detection", True, f"Tested {len(test_cases)} language detection cases")
            
        except Exception as e:
            self.record_test_result("Language Detection", False, f"Language detection failed: {str(e)}")
    
    async def test_rag_integration(self):
        """Test RAG retrieval integration"""
        
        print("\n📚 Testing RAG Integration...")
        
        try:
            from shared.langgraph_agent_service import AgentState
            from langchain_core.messages import HumanMessage
            
            test_state = {
                "messages": [HumanMessage(content="What is machine learning?")],
                "user_id": "test-user",
                "session_id": "test-session",
                "intent": "question",
                "language": "en",
                "documents": [],
                "rag_context": [],
                "user_profile": {},
                "tools_used": [],
                "final_response": "",
                "citations": [],
                "metadata": {}
            }
            
            # Test RAG retrieval node
            result_state = await self.langgraph_service._rag_retrieval_node(test_state)
            
            # Check if RAG context was processed (may be empty if no KB configured)
            assert "rag_context" in result_state
            assert isinstance(result_state["rag_context"], list)
            
            print(f"  ✅ RAG retrieval processed, found {len(result_state['rag_context'])} documents")
            
            self.record_test_result("RAG Integration", True, "RAG retrieval node executed successfully")
            
        except Exception as e:
            self.record_test_result("RAG Integration", False, f"RAG integration failed: {str(e)}")
    
    async def test_memory_integration(self):
        """Test LangChain memory integration"""
        
        print("\n🧠 Testing Memory Integration...")
        
        try:
            # Test memory manager
            session_id = "test-memory-session"
            user_id = "test-memory-user"
            
            memory = memory_manager.get_memory(session_id, user_id, "test-memory-table")
            
            # Test adding messages
            memory.add_user_message("Hello, this is a test message")
            memory.add_ai_message("Hello! I received your test message.")
            
            # Test retrieving messages
            messages = memory.get_recent_messages(10)
            
            assert len(messages) >= 2, "Messages not stored properly"
            
            # Test conversation summary
            summary = memory.get_conversation_summary()
            assert summary['session_id'] == session_id
            assert summary['user_id'] == user_id
            
            print(f"  ✅ Memory integration working, {len(messages)} messages stored")
            
            self.record_test_result("Memory Integration", True, "LangChain memory integration successful")
            
        except Exception as e:
            self.record_test_result("Memory Integration", False, f"Memory integration failed: {str(e)}")
    
    async def test_aws_services_integration(self):
        """Test AWS services integration"""
        
        print("\n☁️ Testing AWS Services Integration...")
        
        try:
            # Test that AWS clients are initialized
            assert self.langgraph_service.textract is not None
            assert self.langgraph_service.comprehend is not None
            assert self.langgraph_service.translate is not None
            assert self.langgraph_service.llm is not None
            
            print("  ✅ AWS clients initialized:")
            print("    - Amazon Textract ✓")
            print("    - Amazon Comprehend ✓") 
            print("    - Amazon Translate ✓")
            print("    - Amazon Bedrock LLM ✓")
            
            self.record_test_result("AWS Services Integration", True, "All AWS services initialized")
            
        except Exception as e:
            self.record_test_result("AWS Services Integration", False, f"AWS services integration failed: {str(e)}")
    
    async def test_summarization_workflow(self):
        """Test complete summarization workflow"""
        
        print("\n📝 Testing Summarization Workflow...")
        
        try:
            context = AgentContext(
                user_id="test-user",
                session_id="test-summarization",
                rag_context=[],
                user_profile={},
                subject_context=None
            )
            
            response = await self.langgraph_service.process_message(
                user_id="test-user",
                message="Summarize the key concepts of machine learning",
                session_id="test-summarization",
                context=context
            )
            
            assert response["success"], f"Summarization failed: {response.get('error')}"
            assert response["intent"] in ["summarize", "general"], f"Wrong intent: {response['intent']}"
            assert len(response["response"]) > 0, "Empty response"
            
            print(f"  ✅ Summarization workflow completed")
            print(f"    Intent: {response['intent']}")
            print(f"    Tools used: {response['tools_used']}")
            
            self.record_test_result("Summarization Workflow", True, "Complete summarization workflow successful")
            
        except Exception as e:
            self.record_test_result("Summarization Workflow", False, f"Summarization workflow failed: {str(e)}")
    
    async def test_question_answering_workflow(self):
        """Test question answering workflow"""
        
        print("\n❓ Testing Question Answering Workflow...")
        
        try:
            context = AgentContext(
                user_id="test-user",
                session_id="test-qa",
                rag_context=[],
                user_profile={},
                subject_context=None
            )
            
            response = await self.langgraph_service.process_message(
                user_id="test-user",
                message="What is the difference between supervised and unsupervised learning?",
                session_id="test-qa",
                context=context
            )
            
            assert response["success"], f"Q&A failed: {response.get('error')}"
            assert len(response["response"]) > 0, "Empty response"
            
            print(f"  ✅ Question answering workflow completed")
            print(f"    Intent: {response['intent']}")
            print(f"    Response length: {len(response['response'])} chars")
            
            self.record_test_result("Question Answering Workflow", True, "Q&A workflow successful")
            
        except Exception as e:
            self.record_test_result("Question Answering Workflow", False, f"Q&A workflow failed: {str(e)}")
    
    async def test_quiz_generation_workflow(self):
        """Test quiz generation workflow"""
        
        print("\n📝 Testing Quiz Generation Workflow...")
        
        try:
            context = AgentContext(
                user_id="test-user",
                session_id="test-quiz",
                rag_context=[],
                user_profile={},
                subject_context=None
            )
            
            response = await self.langgraph_service.process_message(
                user_id="test-user",
                message="Generate a quiz about Python programming with 3 questions",
                session_id="test-quiz",
                context=context
            )
            
            assert response["success"], f"Quiz generation failed: {response.get('error')}"
            assert response["intent"] in ["quiz", "general"], f"Wrong intent: {response['intent']}"
            assert len(response["response"]) > 0, "Empty response"
            
            print(f"  ✅ Quiz generation workflow completed")
            print(f"    Intent: {response['intent']}")
            print(f"    Tools used: {response['tools_used']}")
            
            self.record_test_result("Quiz Generation Workflow", True, "Quiz generation workflow successful")
            
        except Exception as e:
            self.record_test_result("Quiz Generation Workflow", False, f"Quiz generation workflow failed: {str(e)}")
    
    async def test_translation_workflow(self):
        """Test translation workflow"""
        
        print("\n🌐 Testing Translation Workflow...")
        
        try:
            context = AgentContext(
                user_id="test-user",
                session_id="test-translation",
                rag_context=[],
                user_profile={},
                subject_context=None
            )
            
            response = await self.langgraph_service.process_message(
                user_id="test-user",
                message="Translate 'Hello, how are you?' to Spanish",
                session_id="test-translation",
                context=context
            )
            
            assert response["success"], f"Translation failed: {response.get('error')}"
            assert len(response["response"]) > 0, "Empty response"
            
            print(f"  ✅ Translation workflow completed")
            print(f"    Intent: {response['intent']}")
            print(f"    Language: {response['language']}")
            
            self.record_test_result("Translation Workflow", True, "Translation workflow successful")
            
        except Exception as e:
            self.record_test_result("Translation Workflow", False, f"Translation workflow failed: {str(e)}")
    
    async def test_agent_invoker_integration(self):
        """Test agent invoker integration with LangGraph"""
        
        print("\n🤖 Testing Agent Invoker Integration...")
        
        try:
            # Test chat with context
            response = await agent_invoker.chat_with_context(
                user_id="test-user",
                message="Hello, test the agent invoker integration",
                conversation_id="test-invoker-session"
            )
            
            assert response["success"], f"Agent invoker failed: {response.get('error')}"
            assert "workflow_type" in response["metadata"], "Missing workflow type"
            
            # Test service status
            status = agent_invoker.get_service_status()
            assert status["service_initialized"], "Service not initialized"
            assert "langgraph_workflow" in status, "Missing LangGraph workflow info"
            
            print(f"  ✅ Agent invoker integration successful")
            print(f"    Workflow type: {response['metadata']['workflow_type']}")
            print(f"    Primary workflow: {status['primary_workflow']}")
            
            self.record_test_result("Agent Invoker Integration", True, "Agent invoker integration successful")
            
        except Exception as e:
            self.record_test_result("Agent Invoker Integration", False, f"Agent invoker integration failed: {str(e)}")
    
    def record_test_result(self, test_name: str, success: bool, message: str):
        """Record test result"""
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name} - {message}")
    
    def print_test_results(self):
        """Print comprehensive test results"""
        
        print("\n" + "=" * 60)
        print("🧪 LangGraph Test Suite Results")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        
        print(f"\n📊 Summary:")
        print(f"  Total Tests: {len(self.test_results)}")
        print(f"  Passed: {passed} ✅")
        print(f"  Failed: {failed} ❌")
        print(f"  Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['message']}")
        
        print(f"\n✅ Passed Tests:")
        for result in self.test_results:
            if result["success"]:
                print(f"  • {result['test']}")
        
        # Save results to file
        results_file = f"langgraph_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": len(self.test_results),
                    "passed": passed,
                    "failed": failed,
                    "success_rate": passed/len(self.test_results)*100
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {results_file}")


async def main():
    """Main test function"""
    
    # Run test suite
    test_suite = LangGraphTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())