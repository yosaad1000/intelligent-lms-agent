#!/usr/bin/env python3
"""
Test LangGraph Lambda Deployment
Simple test to verify the Lambda function can be deployed and invoked
"""

import json
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_lambda_handler_import():
    """Test that the Lambda handler can be imported"""
    
    print("🧪 Testing LangGraph Lambda Handler Import...")
    
    try:
        # Import the handler
        from chat.langgraph_chat_handler import lambda_handler
        
        print("✅ Lambda handler imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to import Lambda handler: {str(e)}")
        return False

def test_lambda_handler_execution():
    """Test Lambda handler execution with mock event"""
    
    print("\n🧪 Testing LangGraph Lambda Handler Execution...")
    
    try:
        from chat.langgraph_chat_handler import lambda_handler
        
        # Create mock event
        mock_event = {
            "httpMethod": "POST",
            "path": "/api/chat/langgraph",
            "body": json.dumps({
                "user_id": "test-user-123",
                "message": "Hello, test the LangGraph workflow!"
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        # Mock context
        class MockContext:
            def __init__(self):
                self.function_name = "test-langgraph-function"
                self.memory_limit_in_mb = 1024
                self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
                self.aws_request_id = "test-request-id"
        
        mock_context = MockContext()
        
        # Execute handler
        response = lambda_handler(mock_event, mock_context)
        
        # Check response structure
        assert "statusCode" in response, "Missing statusCode in response"
        assert "headers" in response, "Missing headers in response"
        assert "body" in response, "Missing body in response"
        
        # Parse response body
        body = json.loads(response["body"])
        
        print(f"✅ Lambda handler executed successfully")
        print(f"   Status Code: {response['statusCode']}")
        print(f"   Response Keys: {list(body.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Lambda handler execution failed: {str(e)}")
        return False

def test_workflow_info_endpoint():
    """Test workflow info endpoint"""
    
    print("\n🧪 Testing Workflow Info Endpoint...")
    
    try:
        from chat.langgraph_chat_handler import lambda_handler
        
        # Create mock event for workflow info
        mock_event = {
            "httpMethod": "GET",
            "path": "/api/chat/workflow",
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        class MockContext:
            pass
        
        # Execute handler
        response = lambda_handler(mock_event, MockContext())
        
        # Check response
        assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
        
        body = json.loads(response["body"])
        assert "workflow_info" in body, "Missing workflow_info in response"
        
        print(f"✅ Workflow info endpoint working")
        print(f"   Workflow Type: {body['workflow_info'].get('workflow_type', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow info endpoint failed: {str(e)}")
        return False

def test_service_dependencies():
    """Test that all required services can be imported"""
    
    print("\n🧪 Testing Service Dependencies...")
    
    dependencies = [
        ("LangGraph Agent Service", "shared.langgraph_agent_service", "LangGraphAgentService"),
        ("Bedrock Agent Service", "shared.bedrock_agent_service", "BedrockAgentService"),
        ("LangChain Memory", "shared.langchain_memory", "memory_manager"),
        ("Agent Utils", "shared.agent_utils", "agent_invoker"),
        ("Config", "shared.config", "config")
    ]
    
    results = []
    
    for name, module_path, class_name in dependencies:
        try:
            module = __import__(module_path, fromlist=[class_name])
            getattr(module, class_name)
            print(f"   ✅ {name}")
            results.append(True)
        except Exception as e:
            print(f"   ❌ {name}: {str(e)}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Dependencies Success Rate: {success_rate:.1f}%")
    
    return all(results)

def main():
    """Run all deployment tests"""
    
    print("🚀 LangGraph Lambda Deployment Test Suite")
    print("=" * 50)
    
    tests = [
        ("Lambda Handler Import", test_lambda_handler_import),
        ("Service Dependencies", test_service_dependencies),
        ("Lambda Handler Execution", test_lambda_handler_execution),
        ("Workflow Info Endpoint", test_workflow_info_endpoint)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Deployment Test Results")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nSummary:")
    print(f"  Total Tests: {total}")
    print(f"  Passed: {passed} ✅")
    print(f"  Failed: {total - passed} ❌")
    print(f"  Success Rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 All deployment tests passed! Ready for Lambda deployment.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review issues before deployment.")
        
        print("\nFailed Tests:")
        for test_name, result in results:
            if not result:
                print(f"  • {test_name}")
        
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)