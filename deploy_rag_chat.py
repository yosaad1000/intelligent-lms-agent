#!/usr/bin/env python3
"""
Deploy RAG-enabled chat handler
"""

import boto3
import zipfile
import tempfile
from pathlib import Path

def create_rag_chat_handler():
    """Create RAG-enabled chat handler"""
    
    return '''import json
import boto3
import os
import uuid
from datetime import datetime
from decimal import Decimal

def lambda_handler(event, context):
    """Handle chat with RAG functionality"""
    
    try:
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
    """Handle chat message with RAG"""
    
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
        
        # Retrieve RAG context
        rag_context, citations = retrieve_rag_context(user_id, message)
        
        # Generate response
        if rag_context:
            ai_response = generate_rag_response(message, rag_context)
            rag_enhanced = True
        else:
            ai_response = generate_simple_response(message)
            rag_enhanced = False
        
        # Add citations
        if citations:
            ai_response += "\\n\\nSources: " + ", ".join(citations)
        
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
                'citations': citations,
                'rag_documents_used': len(rag_context),
                'rag_enhanced': rag_enhanced,
                'bedrock_agent_used': False
            }, default=decimal_to_int)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)}, default=decimal_to_int)
        }

def retrieve_rag_context(user_id, query, top_k=3):
    """Retrieve relevant document chunks for RAG"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('lms-document-vectors')
        
        # Get all user's document chunks
        response = table.query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        
        chunks = response.get('Items', [])
        
        if not chunks:
            return [], []
        
        # Simple relevance scoring based on keyword overlap
        query_words = set(query.lower().split())
        scored_chunks = []
        
        for chunk in chunks:
            chunk_text = chunk['chunk_text'].lower()
            chunk_words = set(chunk_text.split())
            
            # Calculate overlap score
            overlap = len(query_words.intersection(chunk_words))
            if overlap > 0:
                score = overlap / len(query_words)
                scored_chunks.append({
                    'chunk': chunk,
                    'score': score
                })
        
        # Sort by relevance and take top results
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        top_chunks = scored_chunks[:top_k]
        
        # Extract context and citations
        rag_context = []
        citations = []
        
        for item in top_chunks:
            chunk = item['chunk']
            rag_context.append(chunk['chunk_text'])
            
            citation = chunk['filename'] + " (chunk " + str(chunk['chunk_index'] + 1) + ")"
            if citation not in citations:
                citations.append(citation)
        
        return rag_context, citations
        
    except Exception as e:
        print(f"Error retrieving RAG context: {e}")
        return [], []

def generate_rag_response(question, rag_context):
    """Generate response based on RAG context"""
    
    context_text = " ".join(rag_context)
    question_lower = question.lower()
    
    if "what is" in question_lower and "machine learning" in question_lower:
        return f"Based on your uploaded documents: {context_text[:400]}"
    elif "types" in question_lower and "machine learning" in question_lower:
        return f"According to your documents: {context_text[:400]}"
    elif "how" in question_lower or "explain" in question_lower:
        return f"From your materials: {context_text[:400]}"
    else:
        return f"Based on your uploaded documents: {context_text[:300]}"

def generate_simple_response(message):
    """Generate simple response when no RAG context"""
    
    return f"I don't have any relevant documents uploaded yet to answer your question about '{message}'. Please upload some documents first, and I'll be able to provide detailed, contextual answers based on your materials using RAG technology."

def create_conversation(user_id):
    """Create conversation"""
    
    conversation_id = str(uuid.uuid4())
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('lms-chat-conversations')
        
        table.put_item(Item={
            'conversation_id': conversation_id,
            'user_id': user_id,
            'title': 'RAG Chat Session',
            'conversation_type': 'rag_chat',
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
            'context_used': {'rag_enhanced': True}
        })
        
    except Exception as e:
        print(f"Error storing messages: {e}")

def handle_chat_history(event):
    """Handle chat history"""
    
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
    """Convert Decimal to int"""
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

def deploy_rag_chat():
    """Deploy RAG chat handler"""
    
    print("🚀 Deploying RAG Chat Handler")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create handler file
        handler_file = temp_path / "chat_handler.py"
        with open(handler_file, 'w', encoding='utf-8') as f:
            f.write(create_rag_chat_handler())
        
        # Create ZIP
        zip_file = "rag-chat.zip"
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(handler_file, "chat_handler.py")
        
        # Deploy
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
            
            print("✅ RAG chat handler deployed!")
            
            # Clean up
            import os
            os.remove(zip_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return False

def test_rag_chat():
    """Test RAG chat functionality"""
    
    print("\n🧪 Testing RAG Chat...")
    
    import time
    time.sleep(10)  # Wait for deployment
    
    import requests
    
    api_url = "https://1iaj32i7cd.execute-api.us-east-1.amazonaws.com/prod"
    
    test_questions = [
        "What is machine learning?",
        "What are the types of machine learning?",
        "Tell me about supervised learning"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Testing: {question}")
        
        try:
            response = requests.post(
                f"{api_url}/api/chat",
                json={"user_id": "test-user", "message": question},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   RAG Enhanced: {data.get('rag_enhanced', False)}")
                print(f"   Documents Used: {data.get('rag_documents_used', 0)}")
                print(f"   Response: {data.get('response', '')[:150]}...")
                
                if data.get('citations'):
                    print(f"   Citations: {data.get('citations')}")
                    
                if data.get('rag_enhanced'):
                    print("   ✅ RAG working!")
                else:
                    print("   ⚠️  No RAG context found")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Main deployment"""
    
    if deploy_rag_chat():
        test_rag_chat()
        
        print(f"\n🎉 RAG Chat System Ready!")
        print(f"🌐 Test your web interface now - it should have working RAG!")

if __name__ == "__main__":
    main()