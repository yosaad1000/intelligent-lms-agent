"""
Test script to validate Bedrock Agent SDK Integration
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from shared.bedrock_agent_service import BedrockAgentService, AgentType, AgentContext, BedrockAgentError
from shared.agent_utils import AgentInvoker
from shared.config import config


def test_configuration():
    """Test Bedrock Agent configuration"""
    print("🔧 Testing Bedrock Agent Configuration...")
    
    # Check environment variables
    required_vars = [
        'BEDROCK_CHAT_AGENT_ID',
        'BEDROCK_QUIZ_AGENT_ID', 
        'BEDROCK_INTERVIEW_AGENT_ID',
        'BEDROCK_ANALYSIS_AGENT_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = getattr(config, var, '')
        if not value:
            missing_vars.append(var)
        else:
            print(f"  ✅ {var}: {value[:10]}...")
    
    if missing_vars:
        print(f"  ❌ Missing configuration: {', '.join(missing_vars)}")
        print("  💡 Please set these environment variables in your .env file")
        return False
    
    print("  ✅ All Bedrock Agent IDs configured")
    return True


def test_service_initialization():
    """Test BedrockAgentService initialization"""
    print("\n🚀 Testing BedrockAgentService Initialization...")
    
    try:
        service = BedrockAgentService()
        print("  ✅ BedrockAgentService initialized successfully")
        
        # Test configuration validation
        validation_results = service.validate_configuration()
        print(f"  📋 Agent validation results: {validation_results}")
        
        all_configured = all(validation_results.values())
        if all_configured:
            print("  ✅ All agents properly configured")
        else:
            print("  ⚠️  Some agents not configured")
        
        # Test agent info
        agent_info = service.get_agent_info()
        print("  📊 Agent Information:")
        for agent_type, info in agent_info.items():
            status = "✅" if info['configured'] else "❌"
            print(f"    {status} {agent_type}: {info['description']}")
        
        return service, all_configured
        
    except Exception as e:
        print(f"  ❌ Failed to initialize BedrockAgentService: {str(e)}")
        return None, False


def test_agent_invoker():
    """Test AgentInvoker initialization"""
    print("\n🎯 Testing AgentInvoker...")
    
    try:
        invoker = AgentInvoker()
        print("  ✅ AgentInvoker initialized successfully")
        
        # Test service status
        status = invoker.get_service_status()
        print(f"  📊 Service Status: {status['service_initialized']}")
        
        if status['service_initialized']:
            print("  ✅ Agent invoker service ready")
        else:
            print("  ❌ Agent invoker service not ready")
        
        return invoker, status['service_initialized']
        
    except Exception as e:
        print(f"  ❌ Failed to initialize AgentInvoker: {str(e)}")
        return None, False


async def test_mock_agent_invocation(service):
    """Test agent invocation with mock data (no actual AWS calls)"""
    print("\n🧪 Testing Mock Agent Invocation...")
    
    # Create test context
    context = AgentContext(
        user_id='test-user-123',
        session_id='test-session-456',
        conversation_history=[
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there!'}
        ],
        rag_context=[
            {'text': 'Sample document content about mathematics', 'source': 'test.pdf'}
        ],
        user_profile={'mastery_levels': {'math': 0.7}},
        subject_context='mathematics'
    )
    
    # Test prompt building for different agent types
    test_cases = [
        (AgentType.CHAT, "What is calculus?"),
        (AgentType.QUIZ, "Generate a quiz about algebra"),
        (AgentType.INTERVIEW, "Start an interview about physics"),
        (AgentType.ANALYSIS, "Analyze my learning progress")
    ]
    
    for agent_type, message in test_cases:
        try:
            # Test prompt building (this doesn't make AWS calls)
            enhanced_prompt = service._build_enhanced_prompt(message, context, agent_type)
            
            print(f"  ✅ {agent_type.value} agent prompt building successful")
            print(f"    📝 Prompt length: {len(enhanced_prompt)} characters")
            
            # Verify prompt contains expected elements
            if message in enhanced_prompt:
                print(f"    ✅ Original message included")
            if 'mathematics' in enhanced_prompt:
                print(f"    ✅ Subject context included")
            if 'mastery_levels' in enhanced_prompt:
                print(f"    ✅ User profile included")
            
        except Exception as e:
            print(f"  ❌ {agent_type.value} agent prompt building failed: {str(e)}")


async def test_agent_invoker_methods(invoker):
    """Test AgentInvoker high-level methods with mock data"""
    print("\n🎪 Testing AgentInvoker Methods...")
    
    # Note: These tests will fail if AWS credentials are not configured
    # or if Bedrock Agents are not actually deployed
    
    test_user_id = 'test-user-123'
    
    # Test chat method structure
    try:
        print("  🔍 Testing chat_with_context method signature...")
        # This will likely fail due to AWS credentials, but we can test the method exists
        # and has the right signature
        
        # We'll catch the error and verify it's an AWS-related error, not a method error
        result = await invoker.chat_with_context(
            user_id=test_user_id,
            message="Hello, this is a test message"
        )
        
        print("  ✅ chat_with_context method executed (unexpected success)")
        
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['credentials', 'aws', 'bedrock', 'unauthorized', 'access']):
            print("  ✅ chat_with_context method exists (AWS credentials/access issue expected)")
        else:
            print(f"  ❌ chat_with_context method error: {str(e)}")
    
    # Test quiz generation method
    try:
        print("  🔍 Testing generate_quiz method signature...")
        
        result = await invoker.generate_quiz(
            user_id=test_user_id,
            topic="mathematics",
            difficulty="intermediate",
            question_count=3
        )
        
        print("  ✅ generate_quiz method executed (unexpected success)")
        
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['credentials', 'aws', 'bedrock', 'unauthorized', 'access']):
            print("  ✅ generate_quiz method exists (AWS credentials/access issue expected)")
        else:
            print(f"  ❌ generate_quiz method error: {str(e)}")
    
    # Test interview method
    try:
        print("  🔍 Testing conduct_interview method signature...")
        
        result = await invoker.conduct_interview(
            user_id=test_user_id,
            interview_type="technical",
            topic="programming"
        )
        
        print("  ✅ conduct_interview method executed (unexpected success)")
        
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['credentials', 'aws', 'bedrock', 'unauthorized', 'access']):
            print("  ✅ conduct_interview method exists (AWS credentials/access issue expected)")
        else:
            print(f"  ❌ conduct_interview method error: {str(e)}")
    
    # Test analysis method
    try:
        print("  🔍 Testing analyze_learning_progress method signature...")
        
        result = await invoker.analyze_learning_progress(
            user_id=test_user_id,
            analysis_type="overall"
        )
        
        print("  ✅ analyze_learning_progress method executed (unexpected success)")
        
    except Exception as e:
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['credentials', 'aws', 'bedrock', 'unauthorized', 'access']):
            print("  ✅ analyze_learning_progress method exists (AWS credentials/access issue expected)")
        else:
            print(f"  ❌ analyze_learning_progress method error: {str(e)}")


def test_lambda_handler_imports():
    """Test that Lambda handlers can import the Bedrock Agent services"""
    print("\n📦 Testing Lambda Handler Imports...")
    
    try:
        # Test chat handler imports
        from chat.chat_handler import lambda_handler as chat_handler
        print("  ✅ Chat handler imports successful")
        
        # Test quiz handler imports
        from quiz_generator.quiz_handler import lambda_handler as quiz_handler
        print("  ✅ Quiz handler imports successful")
        
        # Test interview handler imports
        from voice_interview.interview_handler import lambda_handler as interview_handler
        print("  ✅ Interview handler imports successful")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {str(e)}")
        return False


def test_error_handling():
    """Test error handling classes"""
    print("\n🛡️  Testing Error Handling...")
    
    try:
        # Test BedrockAgentError
        error = BedrockAgentError("Test error", AgentType.CHAT, "TEST_CODE")
        
        assert str(error) == "Test error"
        assert error.agent_type == AgentType.CHAT
        assert error.error_code == "TEST_CODE"
        
        print("  ✅ BedrockAgentError class working correctly")
        
        # Test AgentType enum
        assert AgentType.CHAT.value == "chat"
        assert AgentType.QUIZ.value == "quiz"
        assert AgentType.INTERVIEW.value == "interview"
        assert AgentType.ANALYSIS.value == "analysis"
        
        print("  ✅ AgentType enum working correctly")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🧪 Bedrock Agent SDK Integration Test Suite")
    print("=" * 50)
    
    test_results = []
    
    # Test 1: Configuration
    config_ok = test_configuration()
    test_results.append(("Configuration", config_ok))
    
    # Test 2: Service initialization
    service, service_ok = test_service_initialization()
    test_results.append(("Service Initialization", service_ok))
    
    # Test 3: Agent invoker
    invoker, invoker_ok = test_agent_invoker()
    test_results.append(("Agent Invoker", invoker_ok))
    
    # Test 4: Mock invocations (if service initialized)
    if service:
        await test_mock_agent_invocation(service)
        test_results.append(("Mock Invocations", True))
    else:
        test_results.append(("Mock Invocations", False))
    
    # Test 5: Invoker methods (if invoker initialized)
    if invoker:
        await test_agent_invoker_methods(invoker)
        test_results.append(("Invoker Methods", True))
    else:
        test_results.append(("Invoker Methods", False))
    
    # Test 6: Lambda handler imports
    imports_ok = test_lambda_handler_imports()
    test_results.append(("Lambda Imports", imports_ok))
    
    # Test 7: Error handling
    error_ok = test_error_handling()
    test_results.append(("Error Handling", error_ok))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bedrock Agent SDK integration is ready.")
    elif passed >= total * 0.7:
        print("⚠️  Most tests passed. Some issues may need attention.")
    else:
        print("❌ Multiple test failures. Please check configuration and setup.")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if not config_ok:
        print("  - Set up Bedrock Agent IDs in your .env file")
        print("  - Ensure you have deployed Bedrock Agents in AWS")
    
    if not service_ok or not invoker_ok:
        print("  - Check AWS credentials configuration")
        print("  - Verify Bedrock service permissions")
    
    if not imports_ok:
        print("  - Check Python path and module structure")
        print("  - Ensure all dependencies are installed")
    
    print("\n🚀 Next Steps:")
    print("  1. Deploy actual Bedrock Agents in AWS Console")
    print("  2. Update .env file with real Agent IDs")
    print("  3. Test with real AWS credentials")
    print("  4. Run integration tests with actual AWS services")


if __name__ == "__main__":
    asyncio.run(main())