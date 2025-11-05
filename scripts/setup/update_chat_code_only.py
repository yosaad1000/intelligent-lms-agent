#!/usr/bin/env python3
"""
Update only the Lambda code, not configuration
"""

import boto3
import zipfile
import tempfile
from pathlib import Path

def update_chat_code():
    """Update only the Lambda function code"""
    
    print("🔄 Updating chat function code only...")
    
    # RAG chat handler code (same as before but simpler deployment)
    handler_code = '''import json
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
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps({
            'conversations': [],
            'total_conversations': 0
        })
    }

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
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create handler file
        handler_file = temp_path / "chat_handler.py"
        with open(handler_file, 'w', encoding='utf-8') as f:
            f.write(handler_code)
        
        # Create ZIP
        zip_file = "rag-chat-code.zip"
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(handler_file, "chat_handler.py")
        
        # Update only the code
        lambda_client = boto3.client('lambda')
        
        try:
            with open(zip_file, 'rb') as f:
                lambda_client.update_function_code(
                    FunctionName='lms-chat-function',
                    ZipFile=f.read()
                )
            
            print("✅ Chat function code updated!")
            
            # Clean up
            import os
            os.remove(zip_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Code update failed: {e}")
            return False

def test_rag():
    """Test RAG functionality"""
    
    print("\n🧪 Testing RAG...")
    
    import time
    time.sleep(5)
    
    import requests
    
    try:
        response = requests.post(
            "https://1iaj32i7cd.execute-api.us-east-1.amazonaws.com/prod/api/chat",
            json={"user_id": "test-user", "message": "What is machine learning?"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"🔍 RAG Enhanced: {data.get('rag_enhanced', False)}")
            print(f"📚 Documents Used: {data.get('rag_documents_used', 0)}")
            print(f"🤖 Response: {data.get('response', '')[:200]}...")
            
            if data.get('citations'):
                print(f"📖 Citations: {data.get('citations')}")
                
            if data.get('rag_enhanced'):
                print("\n🎉 RAG IS WORKING!")
                return True
            else:
                print("\n⚠️  RAG not working yet")
                return False
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main function"""
    
    if update_chat_code():
        if test_rag():
            print(f"\n🎉 SUCCESS! Your RAG system is now working!")
            print(f"🌐 Go test your web interface - it should now have working RAG functionality!")
        else:
            print(f"\n⚠️  Code updated but RAG not working yet. Check logs.")

if __name__ == "__main__":
    main()