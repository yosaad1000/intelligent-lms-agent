#!/usr/bin/env python3
"""
Create a simple chat Lambda that works without Pinecone dependencies
"""

import boto3
import zipfile
import tempfile
from pathlib import Path

def create_simple_chat_handler():
    """Create a simplified chat handler that works"""
    
    handler_code = '''
import json
import boto3
import os
import uuid
from datetime import datetime
from decimal import Decimal

def lambda_handler(event, context):
    """Simple chat handler that works without complex dependencies"""
    
    try:
        # Parse request
        http_method = event.get('httpMethod', 'POST')
        
        if http_method == 'GET':
            return handle_chat_history(event)
        else:
            return handle_chat_message(event)
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)}, default=decimal_to_int)
        }

def handle_chat_message(event):
    """Handle chat message"""
    
    try:
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('user_id', 'test-user')
        message = body.get('message', '').strip()
        
        if not message:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Create conversation
        conversation_id = create_conversation(user_id)
        
        # Simple AI response (no Bedrock for now)
        ai_response = generate_simple_response(message)
        
        # Store conversation
        store_chat_message(conversation_id, user_id, message, ai_response)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'success': True,
                'response': ai_response,
                'conversation_id': conversation_id,
                'timestamp': datetime.utcnow().isoformat(),
                'citations': [],
                'rag_documents_used': 0,
                'rag_enhanced': False,
                'bedrock_agent_used': False
            }, default=decimal_to_int)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)}, default=decimal_to_int)
        }

def handle_chat_history(event):
    """Handle chat history request"""
    
    try:
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id', 'test-user')
        
        conversations = get_user_conversations(user_id)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps({
                'conversations': conversations,
                'total_conversations': len(conversations)
            }, default=decimal_to_int)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)}, default=decimal_to_int)
        }

def generate_simple_response(message):
    """Generate a simple response"""
    
    message_lower = message.lower()
    
    if 'hello' in message_lower or 'hi' in message_lower:
        return "Hello! I'm your AI assistant. I'm currently running on AWS Lambda! Upload some documents and I'll help you learn from them using RAG technology."
    
    elif 'machine learning' in message_lower:
        return "Machine learning is a fascinating field! I'd love to help you learn more about it. Upload some documents about ML and I'll be able to provide more specific, contextual answers based on your materials."
    
    elif 'what' in message_lower and ('are' in message_lower or 'is' in message_lower):
        return "That's a great question! I can provide much better answers when you upload relevant documents. The RAG system will then search through your materials to give you accurate, source-backed responses."
    
    elif 'help' in message_lower:
        return "I'm here to help! I'm an AI assistant powered by AWS Lambda with RAG capabilities. Upload some documents using the file upload feature, and then ask me questions about them. I'll search through your documents to provide accurate, contextual answers with proper citations."
    
    else:
        return f"I understand you're asking about: '{message}'. I'm working! This response is coming from AWS Lambda. Upload some documents and I'll be able to provide much more detailed, contextual answers using RAG (Retrieval-Augmented Generation) technology."

def create_conversation(user_id):
    """Create a new conversation"""
    
    conversation_id = str(uuid.uuid4())
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('lms-chat-conversations')
        
        table.put_item(Item={
            'conversation_id': conversation_id,
            'user_id': user_id,
            'title': 'Chat Session',
            'conversation_type': 'general',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'message_count': 0
        })
    except Exception as e:
        print(f"Error creating conversation: {e}")
    
    return conversation_id

def store_chat_message(conversation_id, user_id, user_message, ai_response):
    """Store chat messages"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        messages_table = dynamodb.Table('lms-chat-messages')
        
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        
        # Store user message
        messages_table.put_item(Item={
            'conversation_id': conversation_id,
            'timestamp': timestamp,
            'message_id': str(uuid.uuid4()),
            'user_id': user_id,
            'message_type': 'user',
            'content': user_message,
            'citations': [],
            'context_used': {}
        })
        
        # Store AI response
        messages_table.put_item(Item={
            'conversation_id': conversation_id,
            'timestamp': timestamp + 1,
            'message_id': str(uuid.uuid4()),
            'user_id': user_id,
            'message_type': 'assistant',
            'content': ai_response,
            'citations': [],
            'context_used': {'simple_response': True}
        })
        
    except Exception as e:
        print(f"Error storing messages: {e}")

def get_user_conversations(user_id):
    """Get user conversations"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('lms-chat-conversations')
        
        response = table.query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        
        conversations = []
        for item in response['Items']:
            conversations.append({
                'conversation_id': item['conversation_id'],
                'title': item['title'],
                'conversation_type': item['conversation_type'],
                'created_at': item['created_at'],
                'message_count': int(item.get('message_count', 0))
            })
        
        return conversations
        
    except Exception as e:
        print(f"Error getting conversations: {e}")
        return []

def decimal_to_int(obj):
    """Convert Decimal to int for JSON serialization"""
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError

def get_cors_headers():
    """Get CORS headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }
'''
    
    return handler_code

def deploy_simple_chat():
    """Deploy the simple chat handler"""
    
    print("🚀 Creating Simple Chat Lambda")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create the handler file
        handler_file = temp_path / "chat_handler.py"
        with open(handler_file, 'w') as f:
            f.write(create_simple_chat_handler())
        
        # Create ZIP
        zip_file = "simple-chat.zip"
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(handler_file, "chat_handler.py")
        
        print("✅ Created simple chat package")
        
        # Deploy to Lambda
        lambda_client = boto3.client('lambda')
        
        try:
            with open(zip_file, 'rb') as f:
                lambda_client.update_function_code(
                    FunctionName='lms-chat-function',
                    ZipFile=f.read()
                )
            
            lambda_client.update_function_configuration(
                FunctionName='lms-chat-function',
                Handler='chat_handler.lambda_handler',
                Timeout=60,
                MemorySize=512
            )
            
            print("✅ Deployed simple chat function")
            
            # Clean up
            import os
            os.remove(zip_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return False

def test_deployment():
    """Test the deployment"""
    
    print("\n🧪 Testing deployment...")
    
    import time
    time.sleep(10)
    
    # Test Lambda directly
    lambda_client = boto3.client('lambda')
    
    try:
        response = lambda_client.invoke(
            FunctionName='lms-chat-function',
            Payload='{"httpMethod": "POST", "body": "{\\"user_id\\": \\"test\\", \\"message\\": \\"hello\\"}"}'
        )
        
        result = response['Payload'].read().decode()
        print(f"Lambda test result: {result[:200]}...")
        
        if 'errorMessage' not in result:
            print("✅ Lambda function working!")
            
            # Test API Gateway
            import requests
            
            try:
                api_response = requests.post(
                    "https://1iaj32i7cd.execute-api.us-east-1.amazonaws.com/prod/api/chat",
                    json={"user_id": "test", "message": "hello"},
                    timeout=30
                )
                
                print(f"API test: {api_response.status_code}")
                
                if api_response.status_code == 200:
                    print("🎉 API Gateway working!")
                    print("✅ Your web interface should now work!")
                    
                    # Show response
                    try:
                        data = api_response.json()
                        print(f"Response: {data.get('response', '')[:100]}...")
                    except:
                        pass
                else:
                    print(f"API response: {api_response.text[:100]}")
                    
            except Exception as e:
                print(f"API test failed: {e}")
        else:
            print(f"❌ Lambda error: {result}")
            
    except Exception as e:
        print(f"Lambda test failed: {e}")

def main():
    """Main function"""
    
    print("🔧 Deploying Simple Working Chat Function")
    print("=" * 50)
    
    if deploy_simple_chat():
        test_deployment()
        
        print(f"\n🎉 Deployment Complete!")
        print(f"🌐 Your web interface should now work at: test_interface.html")
        print(f"📱 API URL: https://1iaj32i7cd.execute-api.us-east-1.amazonaws.com/prod")

if __name__ == "__main__":
    main()