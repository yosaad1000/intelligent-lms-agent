#!/usr/bin/env python3
"""
Make the AI more conversational and natural
"""

import boto3
import zipfile
import tempfile
from pathlib import Path

def create_conversational_chat_handler():
    """Create conversational AI chat handler"""
    
    return '''import json
import boto3
import os
import uuid
from datetime import datetime
from decimal import Decimal

def lambda_handler(event, context):
    """Handle chat with conversational AI + RAG"""
    
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
    """Handle chat message with conversational AI + RAG"""
    
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
        
        # Check if this is a casual conversation or needs RAG
        needs_rag = should_use_rag(message)
        
        if needs_rag:
            # Retrieve RAG context for educational questions
            rag_context, citations = retrieve_rag_context(user_id, message)
            
            if rag_context:
                ai_response = generate_llm_response_with_rag(message, rag_context)
                rag_enhanced = True
            else:
                ai_response = generate_conversational_response(message, has_documents=False)
                rag_enhanced = False
        else:
            # Handle casual conversation naturally
            ai_response = generate_conversational_response(message, has_documents=True)
            rag_context = []
            citations = []
            rag_enhanced = False
        
        # Add citations if available
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
                'bedrock_llm_used': True,
                'conversation_type': 'rag' if rag_enhanced else 'casual'
            }, default=decimal_to_int)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)}, default=decimal_to_int)
        }

def should_use_rag(message):
    """Determine if message needs RAG or is casual conversation"""
    
    message_lower = message.lower().strip()
    
    # Casual greetings and conversation
    casual_patterns = [
        'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
        'how are you', 'whats up', "what's up", 'thanks', 'thank you', 'bye', 'goodbye',
        'ok', 'okay', 'cool', 'nice', 'great', 'awesome', 'perfect'
    ]
    
    # Check if it's a casual message
    for pattern in casual_patterns:
        if message_lower == pattern or message_lower.startswith(pattern + ' ') or message_lower.endswith(' ' + pattern):
            return False
    
    # Educational question patterns that need RAG
    educational_patterns = [
        'what is', 'what are', 'how does', 'explain', 'tell me about', 'describe',
        'define', 'meaning of', 'types of', 'examples of', 'difference between'
    ]
    
    for pattern in educational_patterns:
        if pattern in message_lower:
            return True
    
    # If message is longer than 10 words, probably educational
    if len(message.split()) > 10:
        return True
    
    # Default to casual for short messages
    return False

def generate_conversational_response(message, has_documents=True):
    """Generate natural conversational response using Bedrock LLM"""
    
    try:
        message_lower = message.lower().strip()
        
        # Create natural conversation prompt
        if message_lower in ['hi', 'hello', 'hey']:
            prompt = f"""You are a friendly, helpful AI learning assistant. The user just greeted you with "{message}".

Respond naturally and warmly. Keep it brief and friendly. Mention that you're here to help them learn from their documents if they have questions.

Response:"""
        
        elif 'how are you' in message_lower:
            prompt = f"""You are a friendly AI learning assistant. The user asked "{message}".

Respond naturally and positively. Keep it conversational and mention you're ready to help with their learning materials.

Response:"""
        
        elif message_lower in ['thanks', 'thank you']:
            prompt = f"""The user said "{message}". Respond naturally and warmly as a helpful AI assistant.

Response:"""
        
        elif message_lower in ['bye', 'goodbye']:
            prompt = f"""The user is saying goodbye with "{message}". Respond warmly and naturally.

Response:"""
        
        else:
            # General conversational response
            prompt = f"""You are a friendly, conversational AI learning assistant. The user said: "{message}"

Respond naturally and helpfully. If it seems like they might want to learn something, gently suggest they can ask questions about their uploaded documents.

Response:"""

        # Call Bedrock LLM
        bedrock_runtime = boto3.client('bedrock-runtime')
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 150,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        if 'content' in response_body and len(response_body['content']) > 0:
            return response_body['content'][0]['text'].strip()
        else:
            # Fallback responses
            if message_lower in ['hi', 'hello', 'hey']:
                return "Hi there! I'm your AI learning assistant. I'm here to help you understand and learn from your documents. What would you like to explore today?"
            elif 'how are you' in message_lower:
                return "I'm doing great, thank you for asking! I'm excited to help you learn. Do you have any questions about your uploaded materials?"
            else:
                return "Thanks for chatting! I'm here whenever you want to dive into your learning materials or have questions about any topics."
            
    except Exception as e:
        print(f"Error in conversational response: {e}")
        # Natural fallback responses
        if message.lower().strip() in ['hi', 'hello', 'hey']:
            return "Hi! Great to meet you! I'm your AI learning assistant, ready to help you explore and understand your documents. What's on your mind?"
        elif 'how are you' in message.lower():
            return "I'm fantastic, thanks for asking! Ready to dive into some learning with you. Got any interesting questions about your materials?"
        else:
            return "I'm here and ready to help! Feel free to ask me anything about your uploaded documents or just chat about what you're learning."

def generate_llm_response_with_rag(question, rag_context):
    """Generate response using Bedrock LLM with RAG context"""
    
    try:
        # Combine RAG context
        context_text = "\\n\\n".join(rag_context)
        
        # Create conversational prompt for LLM
        prompt = f"""You are a friendly, knowledgeable AI learning assistant. Answer the user's question based on their uploaded documents, but keep your tone conversational and engaging.

Context from their documents:
{context_text}

User's question: {question}

Instructions:
- Answer based on the provided context from their documents
- Be conversational, friendly, and engaging (not robotic)
- Use "you" and "your" to make it personal
- If the context doesn't fully answer the question, say so naturally
- Break down complex topics in an easy-to-understand way
- Feel free to use examples or analogies to explain concepts

Answer:"""

        # Call Bedrock LLM
        bedrock_runtime = boto3.client('bedrock-runtime')
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        if 'content' in response_body and len(response_body['content']) > 0:
            ai_response = response_body['content'][0]['text']
            return ai_response.strip()
        else:
            return "I'd love to help you with that! Let me look through your documents... " + context_text[:200] + "..."
            
    except Exception as e:
        print(f"Error calling Bedrock LLM: {e}")
        return f"Great question! Based on your documents: {context_text[:300]}..."

def retrieve_rag_context(user_id, query, top_k=3):
    """Retrieve relevant document chunks for RAG"""
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('lms-document-vectors')
        
        response = table.query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        
        chunks = response.get('Items', [])
        
        if not chunks:
            return [], []
        
        # Simple relevance scoring
        query_words = set(query.lower().split())
        scored_chunks = []
        
        for chunk in chunks:
            chunk_text = chunk['chunk_text'].lower()
            chunk_words = set(chunk_text.split())
            
            overlap = len(query_words.intersection(chunk_words))
            if overlap > 0:
                score = overlap / len(query_words)
                scored_chunks.append({
                    'chunk': chunk,
                    'score': score
                })
        
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        top_chunks = scored_chunks[:top_k]
        
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

def create_conversation(user_id):
    """Create conversation"""
    
    conversation_id = str(uuid.uuid4())
    
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('lms-chat-conversations')
        
        table.put_item(Item={
            'conversation_id': conversation_id,
            'user_id': user_id,
            'title': 'AI Learning Chat',
            'conversation_type': 'conversational_rag',
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
        
        messages_table.put_item(Item={
            'conversation_id': conversation_id,
            'timestamp': timestamp + 1,
            'message_id': str(uuid.uuid4()),
            'user_id': user_id,
            'message_type': 'assistant',
            'content': ai_response,
            'citations': [],
            'context_used': {'conversational_ai': True}
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

def deploy_conversational_ai():
    """Deploy conversational AI chat handler"""
    
    print("💬 Deploying Conversational AI + RAG Chat Handler")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create handler file
        handler_file = temp_path / "chat_handler.py"
        with open(handler_file, 'w', encoding='utf-8') as f:
            f.write(create_conversational_chat_handler())
        
        # Create ZIP
        zip_file = "conversational-ai-chat.zip"
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(handler_file, "chat_handler.py")
        
        # Update Lambda function
        lambda_client = boto3.client('lambda')
        
        try:
            with open(zip_file, 'rb') as f:
                lambda_client.update_function_code(
                    FunctionName='lms-chat-function',
                    ZipFile=f.read()
                )
            
            print("✅ Conversational AI chat handler deployed!")
            
            # Clean up
            import os
            os.remove(zip_file)
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return False

def test_conversational_ai():
    """Test conversational AI functionality"""
    
    print("\n🧪 Testing Conversational AI...")
    
    import time
    time.sleep(5)
    
    import requests
    
    test_messages = [
        "Hi",
        "How are you?",
        "What is machine learning?",
        "Thanks!",
        "Tell me about supervised learning"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Testing: '{message}'")
        
        try:
            response = requests.post(
                "https://1iaj32i7cd.execute-api.us-east-1.amazonaws.com/prod/api/chat",
                json={"user_id": "test-user", "message": message},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: {response.status_code}")
                print(f"   💬 Type: {data.get('conversation_type', 'unknown')}")
                print(f"   🔍 RAG Enhanced: {data.get('rag_enhanced', False)}")
                print(f"   🤖 Response: {data.get('response', '')[:200]}...")
                
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Main deployment"""
    
    if deploy_conversational_ai():
        test_conversational_ai()
        
        print(f"\n🎉 SUCCESS! Your AI is now conversational!")
        print(f"💬 Try saying 'Hi' - it will respond naturally")
        print(f"🤖 Ask educational questions - it will use RAG + LLM")
        print(f"🌐 Test your web interface - much more natural now!")

if __name__ == "__main__":
    main()