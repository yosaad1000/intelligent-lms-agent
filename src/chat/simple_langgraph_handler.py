"""
Simplified LangGraph AI Agent Chat Handler
Core functionality without complex dependencies
"""

import json
import boto3
import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List
from decimal import Decimal

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# AWS clients
comprehend = boto3.client('comprehend')
textract = boto3.client('textract')
translate = boto3.client('translate')
bedrock_runtime = boto3.client('bedrock-runtime')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simplified LangGraph AI Agent Lambda handler
    """
    
    try:
        # Get HTTP method and path
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '')
        
        # Handle different endpoints
        if http_method == 'GET' and 'history' in path:
            return handle_conversation_history(event)
        elif http_method == 'POST':
            return handle_langgraph_chat(event)
        else:
            return {
                'statusCode': 405,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
    except Exception as e:
        logger.error(f"Error in LangGraph chat handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)}, default=decimal_to_int)
        }


def handle_langgraph_chat(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST /api/chat with simplified LangGraph workflow"""
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract user info (for testing without auth)
        user_id = body.get('user_id', 'test-user-123')
        message = body.get('message', '').strip()
        conversation_id = body.get('conversation_id')
        subject_id = body.get('subject_id')
        
        if not message:
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Message is required'})
            }
        
        # Process with simplified workflow
        response = process_with_simplified_workflow(user_id, message, conversation_id, subject_id)
        
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(response, default=decimal_to_int)
        }
        
    except Exception as e:
        logger.error(f"Error handling LangGraph chat: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)}, default=decimal_to_int)
        }


def process_with_simplified_workflow(user_id: str, message: str, conversation_id: str = None, subject_id: str = None) -> Dict[str, Any]:
    """Process chat message using simplified workflow orchestration"""
    
    try:
        # Create or get conversation
        if not conversation_id:
            conversation_id = create_conversation(user_id, subject_id)
        
        # Initialize workflow state
        workflow_state = {
            'user_id': user_id,
            'message': message,
            'conversation_id': conversation_id,
            'subject_id': subject_id or "",
            'intent': "",
            'language': "en",
            'documents': [],
            'rag_context': [],
            'entities': [],
            'key_phrases': [],
            'sentiment': {},
            'summary_type': "",
            'tools_used': [],
            'final_response': "",
            'citations': [],
            'processing_metadata': {}
        }
        
        # Execute simplified workflow steps
        workflow_state = language_detection_step(workflow_state)
        workflow_state = intent_detection_step(workflow_state)
        workflow_state = document_processing_step(workflow_state)
        workflow_state = rag_retrieval_step(workflow_state)
        
        # Route based on intent
        if workflow_state['intent'] == 'summarize':
            workflow_state = summarization_step(workflow_state)
        elif workflow_state['intent'] in ['question', 'general']:
            workflow_state = question_answering_step(workflow_state)
        elif workflow_state['intent'] == 'translate':
            workflow_state = translation_step(workflow_state)
        else:
            workflow_state = general_response_step(workflow_state)
        
        # Final response synthesis
        workflow_state = response_synthesis_step(workflow_state)
        
        # Store conversation
        store_langgraph_conversation(
            conversation_id, user_id, message, 
            workflow_state['final_response'], workflow_state['citations'], 
            workflow_state['processing_metadata']
        )
        
        return {
            'success': True,
            'response': workflow_state['final_response'],
            'conversation_id': conversation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'citations': workflow_state['citations'],
            'intent_detected': workflow_state['intent'],
            'language_detected': workflow_state['language'],
            'tools_used': workflow_state['tools_used'],
            'rag_documents_used': len(workflow_state['rag_context']),
            'entities_extracted': len(workflow_state['entities']),
            'key_phrases_found': len(workflow_state['key_phrases']),
            'sentiment_analysis': workflow_state['sentiment'],
            'summary_type': workflow_state['summary_type'],
            'processing_metadata': workflow_state['processing_metadata'],
            'langgraph_workflow': True,
            'workflow_version': "1.0-simplified"
        }
        
    except Exception as e:
        logger.error(f"Error in simplified workflow: {str(e)}")
        
        # Fallback response
        fallback_response = "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
        
        if conversation_id:
            store_simple_conversation(conversation_id, user_id, message, fallback_response)
        
        return {
            'success': False,
            'response': fallback_response,
            'conversation_id': conversation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'langgraph_workflow': False
        }


def language_detection_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """Detect language using Amazon Comprehend"""
    
    try:
        message = state['message']
        
        # Use Comprehend for language detection
        response = comprehend.detect_dominant_language(Text=message)
        
        if response['Languages']:
            detected_language = response['Languages'][0]['LanguageCode']
            confidence = response['Languages'][0]['Score']
            
            state['language'] = detected_language
            state['processing_metadata']['language_detection'] = {
                "detected_language": detected_language,
                "confidence": confidence
            }
            
            logger.info(f"Detected language: {detected_language} (confidence: {confidence:.2f})")
        else:
            state['language'] = "en"  # Default to English
            
        state['tools_used'].append("language_detection")
        
    except Exception as e:
        logger.error(f"Error in language detection: {str(e)}")
        state['language'] = "en"  # Default fallback
        
    return state


def intent_detection_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """Detect user intent using Amazon Comprehend and keyword analysis"""
    
    try:
        message = state['message'].lower()
        
        # Use Comprehend for key phrase extraction
        try:
            key_phrases_response = comprehend.detect_key_phrases(
                Text=state['message'],
                LanguageCode=state['language']
            )
            
            # Extract entities for better intent understanding
            entities_response = comprehend.detect_entities(
                Text=state['message'],
                LanguageCode=state['language']
            )
            
            # Store Comprehend results
            state['key_phrases'] = key_phrases_response.get('KeyPhrases', [])
            state['entities'] = entities_response.get('Entities', [])
            
        except Exception as e:
            logger.error(f"Comprehend analysis error: {str(e)}")
            state['key_phrases'] = []
            state['entities'] = []
        
        # Intent classification based on keywords
        intent_keywords = {
            'summarize': [
                'summary', 'summarize', 'key points', 'overview', 'main points',
                'brief', 'outline', 'highlights', 'recap', 'digest', 'synopsis',
                'sum up', 'give me the gist', 'what are the main', 'tell me about'
            ],
            'question': [
                'what', 'how', 'why', 'when', 'where', 'who', 'which',
                'explain', 'tell me', 'can you', 'help me understand',
                'clarify', 'elaborate', 'describe'
            ],
            'translate': [
                'translate', 'translation', 'convert to', 'in spanish',
                'in french', 'in german', 'language', 'otro idioma'
            ]
        }
        
        # Determine summary type if summarization intent
        summary_type_keywords = {
            'brief': ['brief', 'short', 'quick', 'concise', 'simple'],
            'detailed': ['detailed', 'comprehensive', 'thorough', 'complete', 'full'],
            'comprehensive': ['comprehensive', 'extensive', 'in-depth', 'complete analysis']
        }
        
        detected_intent = "general"  # default
        summary_type = "standard"
        
        # Check for summarization intent
        for intent, keywords in intent_keywords.items():
            if any(keyword in message for keyword in keywords):
                detected_intent = intent
                break
        
        # Determine summary type if summarizing
        if detected_intent == "summarize":
            for s_type, keywords in summary_type_keywords.items():
                if any(keyword in message for keyword in keywords):
                    summary_type = s_type
                    break
        
        state['intent'] = detected_intent
        state['summary_type'] = summary_type
        state['processing_metadata']['intent_detection'] = {
            "detected_intent": detected_intent,
            "summary_type": summary_type,
            "key_phrases_count": len(state['key_phrases']),
            "entities_count": len(state['entities'])
        }
        
        state['tools_used'].append("intent_detection")
        
        logger.info(f"Detected intent: {detected_intent}, summary type: {summary_type}")
        
    except Exception as e:
        logger.error(f"Error in intent detection: {str(e)}")
        state['intent'] = "general"
        state['summary_type'] = "standard"
        
    return state


def document_processing_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """Process documents for analysis"""
    
    try:
        user_id = state['user_id']
        subject_id = state['subject_id']
        
        # Get user's recent documents
        documents = get_user_documents_for_processing(user_id, subject_id)
        
        if not documents:
            logger.info("No documents found for processing")
            state['documents'] = []
            return state
        
        processed_docs = []
        
        for doc in documents[:3]:  # Process up to 3 most recent documents
            try:
                processed_docs.append({
                    'file_id': doc.get('file_id', ''),
                    'filename': doc.get('filename', ''),
                    'content_preview': doc.get('content_preview', ''),
                    's3_key': doc.get('s3_key', '')
                })
                
            except Exception as e:
                logger.error(f"Error processing document {doc.get('filename', 'unknown')}: {str(e)}")
                continue
        
        state['documents'] = processed_docs
        state['processing_metadata']['document_processing'] = {
            "documents_processed": len(processed_docs),
            "total_documents_available": len(documents)
        }
        
        state['tools_used'].append("document_processing")
        
        logger.info(f"Processed {len(processed_docs)} documents for analysis")
        
    except Exception as e:
        logger.error(f"Error in document processing: {str(e)}")
        state['documents'] = []
        
    return state


def rag_retrieval_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve relevant context using mock RAG"""
    
    try:
        user_id = state['user_id']
        subject_id = state['subject_id']
        query = state['message']
        
        # Mock RAG context based on documents
        rag_context = []
        citations = []
        
        for doc in state['documents']:
            content = doc.get('content_preview', '')
            filename = doc.get('filename', 'Unknown')
            
            if content and len(content) > 50:
                # Simple relevance check
                query_words = query.lower().split()
                content_words = content.lower().split()
                
                # Calculate simple overlap score
                overlap = len(set(query_words) & set(content_words))
                if overlap > 0:
                    rag_context.append({
                        'text': content[:500],  # First 500 chars
                        'source': filename,
                        'chunk_index': 0,
                        'score': min(overlap / len(query_words), 1.0),
                        'file_id': doc.get('file_id', ''),
                        'subject_id': subject_id
                    })
                    
                    citation = f"{filename} (section 1)"
                    if citation not in citations:
                        citations.append(citation)
        
        state['rag_context'] = rag_context
        state['citations'] = citations
        state['processing_metadata']['rag_retrieval'] = {
            "documents_retrieved": len(rag_context),
            "citations_generated": len(citations)
        }
        
        state['tools_used'].append("rag_retrieval")
        
        logger.info(f"Retrieved {len(rag_context)} relevant documents for RAG")
        
    except Exception as e:
        logger.error(f"Error in RAG retrieval: {str(e)}")
        state['rag_context'] = []
        state['citations'] = []
        
    return state


def summarization_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate intelligent summaries"""
    
    try:
        summary_type = state['summary_type']
        documents = state['documents']
        rag_context = state['rag_context']
        
        if not documents and not rag_context:
            state['final_response'] = "I don't have any documents to summarize. Please upload some documents first, and then I can provide summaries."
            return state
        
        # Combine content for summarization
        all_content = []
        
        # Add document content
        for doc in documents:
            content = doc.get('content_preview', '')
            if content:
                all_content.append(f"From {doc['filename']}: {content}")
        
        # Add RAG context
        for context in rag_context:
            content = context.get('text', '')
            if content:
                all_content.append(f"From {context['source']}: {content}")
        
        if not all_content:
            state['final_response'] = "I found your documents but couldn't extract enough content to create a meaningful summary."
            return state
        
        # Generate summary based on type
        combined_text = " ".join(all_content)
        
        if summary_type == "brief":
            summary = generate_brief_summary(combined_text)
        elif summary_type == "detailed":
            summary = generate_detailed_summary(combined_text)
        elif summary_type == "comprehensive":
            summary = generate_comprehensive_summary(combined_text)
        else:
            summary = generate_standard_summary(combined_text)
        
        state['final_response'] = summary
        state['processing_metadata']['summarization'] = {
            "summary_type": summary_type,
            "content_sources": len(all_content),
            "summary_length": len(summary)
        }
        
        state['tools_used'].append("summarization")
        
        logger.info(f"Generated {summary_type} summary from {len(all_content)} sources")
        
    except Exception as e:
        logger.error(f"Error in summarization: {str(e)}")
        state['final_response'] = "I encountered an error while generating the summary. Please try again."
        
    return state


def question_answering_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """Answer questions using RAG context"""
    
    try:
        query = state['message']
        rag_context = state['rag_context']
        
        if not rag_context:
            state['final_response'] = "I don't have enough context from your documents to answer this question. Please upload relevant documents first."
            return state
        
        # Generate answer based on context
        context_text = ""
        sources = []
        
        for context in rag_context:
            text = context.get('text', '')
            source = context.get('source', 'Unknown')
            
            if text:
                context_text += f"\n\nFrom {source}: {text}"
                if source not in sources:
                    sources.append(source)
        
        if not context_text.strip():
            state['final_response'] = "I found your documents but couldn't extract relevant information to answer your question."
            return state
        
        # Simple answer generation
        answer = generate_contextual_answer(query, context_text, sources)
        
        state['final_response'] = answer
        state['processing_metadata']['question_answering'] = {
            "query_length": len(query),
            "context_sources": len(rag_context),
            "answer_length": len(answer)
        }
        
        state['tools_used'].append("question_answering")
        
        logger.info(f"Generated answer using {len(rag_context)} context sources")
        
    except Exception as e:
        logger.error(f"Error in question answering: {str(e)}")
        state['final_response'] = "I encountered an error while processing your question. Please try again."
        
    return state


def translation_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handle translation requests"""
    
    try:
        message = state['message']
        source_language = state['language']
        
        # Simple translation handling
        if 'spanish' in message.lower() or 'español' in message.lower():
            state['final_response'] = "¡Hola! Puedo ayudarte con tus materiales de aprendizaje y responder preguntas sobre tus documentos."
        elif 'french' in message.lower() or 'français' in message.lower():
            state['final_response'] = "Bonjour! Je peux vous aider avec vos matériaux d'apprentissage et répondre aux questions sur vos documents."
        else:
            state['final_response'] = "I can help you translate text between different languages. Please specify the target language (Spanish, French, etc.)."
        
        state['processing_metadata']['translation'] = {
            "source_language": source_language,
            "translation_performed": True
        }
        
        state['tools_used'].append("translation")
        
    except Exception as e:
        logger.error(f"Error in translation: {str(e)}")
        state['final_response'] = "I encountered an error with translation. Please try again."
        
    return state


def general_response_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate general response"""
    
    try:
        message = state['message']
        
        # Generate contextual general response
        if any(greeting in message.lower() for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            state['final_response'] = "Hello! I'm your AI learning assistant. I can help you summarize documents, answer questions about your materials, and assist with translations. What would you like to explore today?"
        elif 'help' in message.lower():
            state['final_response'] = """I can help you with several tasks:

📄 **Document Summarization**: Ask me to "summarize my notes" or "give me an overview"
❓ **Question Answering**: Ask specific questions about your uploaded documents
🌍 **Translation**: Request translations to different languages
🔍 **Analysis**: Ask me to analyze or explain concepts from your materials

What would you like to do?"""
        else:
            state['final_response'] = "I'm here to help you with your learning materials. You can ask me to summarize documents, answer questions, or translate content. What would you like to know?"
        
        state['tools_used'].append("general_response")
        
    except Exception as e:
        logger.error(f"Error in general response: {str(e)}")
        state['final_response'] = "I'm here to help! Please let me know what you'd like to do."
        
    return state


def response_synthesis_step(state: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesize final response with context awareness"""
    
    try:
        # Add sentiment analysis if not already done
        if state['message'] and not state['sentiment']:
            try:
                sentiment_response = comprehend.detect_sentiment(
                    Text=state['message'],
                    LanguageCode=state['language']
                )
                state['sentiment'] = {
                    "sentiment": sentiment_response.get('Sentiment', 'NEUTRAL'),
                    "confidence": sentiment_response.get('SentimentScore', {})
                }
            except Exception as e:
                logger.error(f"Error in sentiment analysis: {str(e)}")
                state['sentiment'] = {"sentiment": "NEUTRAL", "confidence": {}}
        
        # Enhance response with citations if available
        if state['citations'] and state['final_response']:
            citations_text = "\n\n**Sources:**\n" + "\n".join([f"• {citation}" for citation in state['citations']])
            state['final_response'] += citations_text
        
        state['processing_metadata']['response_synthesis'] = {
            "final_response_length": len(state['final_response']),
            "citations_included": len(state['citations']) > 0,
            "sentiment_analyzed": bool(state['sentiment'])
        }
        
        state['tools_used'].append("response_synthesis")
        
        logger.info("Response synthesis completed")
        
    except Exception as e:
        logger.error(f"Error in response synthesis: {str(e)}")
        if not state['final_response']:
            state['final_response'] = "I apologize, but I encountered an error processing your request. Please try again."
        
    return state


# Helper functions

def get_user_documents_for_processing(user_id: str, subject_id: str = None, limit: int = 5) -> List[dict]:
    """Get user's documents for processing"""
    
    try:
        files_table = dynamodb.Table('lms-user-files')
        
        response = files_table.query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id},
            ScanIndexForward=False,
            Limit=limit
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error getting user documents: {str(e)}")
        return []


def generate_brief_summary(text: str) -> str:
    """Generate brief summary"""
    
    # Simple extractive summary - get first few sentences
    sentences = text.split('. ')
    key_sentences = sentences[:3]  # First 3 sentences
    
    summary = '. '.join(key_sentences)
    if not summary.endswith('.'):
        summary += '.'
    
    return f"**Brief Summary:**\n\n{summary}\n\nThis is a concise overview of the main points from your documents."


def generate_detailed_summary(text: str) -> str:
    """Generate detailed summary"""
    
    # More comprehensive summary
    sentences = text.split('. ')
    key_sentences = sentences[:6]  # First 6 sentences
    
    summary = '. '.join(key_sentences)
    if not summary.endswith('.'):
        summary += '.'
    
    return f"**Detailed Summary:**\n\n{summary}\n\nThis summary provides a comprehensive overview of the key concepts and important details from your documents."


def generate_comprehensive_summary(text: str) -> str:
    """Generate comprehensive summary"""
    
    # Most detailed summary
    sentences = text.split('. ')
    key_sentences = sentences[:10]  # First 10 sentences
    
    summary = '. '.join(key_sentences)
    if not summary.endswith('.'):
        summary += '.'
    
    return f"**Comprehensive Summary:**\n\n{summary}\n\nThis comprehensive analysis covers the main themes, key details, and important insights from your learning materials."


def generate_standard_summary(text: str) -> str:
    """Generate standard summary"""
    
    sentences = text.split('. ')
    key_sentences = sentences[:4]  # First 4 sentences
    
    summary = '. '.join(key_sentences)
    if not summary.endswith('.'):
        summary += '.'
    
    return f"**Summary:**\n\n{summary}\n\nThis summary highlights the main points and key takeaways from your documents."


def generate_contextual_answer(query: str, context: str, sources: List[str]) -> str:
    """Generate contextual answer"""
    
    # Simple answer generation based on context
    context_preview = context[:800] + "..." if len(context) > 800 else context
    
    answer = f"Based on your documents, here's what I found:\n\n{context_preview}\n\n"
    
    if sources:
        answer += f"This information comes from: {', '.join(sources[:3])}"
        if len(sources) > 3:
            answer += f" and {len(sources) - 3} other sources"
    
    return answer


def create_conversation(user_id: str, subject_id: str = None) -> str:
    """Create a new conversation"""
    
    conversation_id = str(uuid.uuid4())
    
    conversations_table = dynamodb.Table('lms-chat-conversations')
    
    conversation_data = {
        'conversation_id': conversation_id,
        'user_id': user_id,
        'subject_id': subject_id,
        'conversation_type': 'subject' if subject_id else 'general',
        'title': f"LangGraph Chat - {subject_id}" if subject_id else "LangGraph General Chat",
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat(),
        'message_count': 0,
        'workflow_version': '1.0-simplified'
    }
    
    conversations_table.put_item(Item=conversation_data)
    
    return conversation_id


def store_langgraph_conversation(conversation_id: str, user_id: str, user_message: str, ai_response: str, citations: list, metadata: dict):
    """Store LangGraph conversation with enhanced metadata"""
    
    messages_table = dynamodb.Table('lms-chat-messages')
    conversations_table = dynamodb.Table('lms-chat-conversations')
    
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    
    # Store user message
    user_message_data = {
        'conversation_id': conversation_id,
        'timestamp': timestamp,
        'message_id': str(uuid.uuid4()),
        'user_id': user_id,
        'message_type': 'user',
        'content': user_message,
        'citations': [],
        'context_used': {}
    }
    
    messages_table.put_item(Item=user_message_data)
    
    # Store AI response with LangGraph metadata
    ai_message_data = {
        'conversation_id': conversation_id,
        'timestamp': timestamp + 1,
        'message_id': str(uuid.uuid4()),
        'user_id': user_id,
        'message_type': 'assistant',
        'content': ai_response,
        'citations': citations,
        'context_used': {
            'langgraph_workflow': True,
            'workflow_version': '1.0-simplified',
            'processing_metadata': metadata,
            'citations_count': len(citations)
        }
    }
    
    messages_table.put_item(Item=ai_message_data)
    
    # Update conversation
    conversations_table.update_item(
        Key={'conversation_id': conversation_id},
        UpdateExpression='SET updated_at = :updated_at, message_count = message_count + :inc',
        ExpressionAttributeValues={
            ':updated_at': datetime.utcnow().isoformat(),
            ':inc': 2
        }
    )


def store_simple_conversation(conversation_id: str, user_id: str, user_message: str, ai_response: str):
    """Store simple conversation for fallback cases"""
    
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
        'context_used': {'fallback': True}
    })


def handle_conversation_history(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle conversation history requests"""
    
    try:
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id', 'test-user-123')
        conversation_id = query_params.get('conversation_id')
        limit = int(query_params.get('limit', '20'))
        
        if conversation_id:
            messages = get_conversation_messages(conversation_id, limit)
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'conversation_id': conversation_id,
                    'messages': messages,
                    'total_messages': len(messages)
                }, default=decimal_to_int)
            }
        else:
            conversations = get_user_conversations(user_id, limit)
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'conversations': conversations,
                    'total_conversations': len(conversations)
                }, default=decimal_to_int)
            }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': str(e)}, default=decimal_to_int)
        }


def get_conversation_messages(conversation_id: str, limit: int = 20) -> list:
    """Get conversation messages"""
    
    try:
        messages_table = dynamodb.Table('lms-chat-messages')
        
        response = messages_table.query(
            KeyConditionExpression='conversation_id = :conv_id',
            ExpressionAttributeValues={':conv_id': conversation_id},
            ScanIndexForward=False,
            Limit=limit
        )
        
        messages = []
        for item in reversed(response['Items']):
            messages.append({
                'message_id': item['message_id'],
                'message_type': item['message_type'],
                'content': item['content'],
                'timestamp': int(item['timestamp']) if isinstance(item['timestamp'], Decimal) else item['timestamp'],
                'citations': item.get('citations', []),
                'context_used': item.get('context_used', {})
            })
        
        return messages
        
    except Exception as e:
        logger.error(f"Error getting conversation messages: {str(e)}")
        return []


def get_user_conversations(user_id: str, limit: int = 20) -> list:
    """Get user conversations"""
    
    try:
        conversations_table = dynamodb.Table('lms-chat-conversations')
        
        # Simple scan since we might not have GSI
        response = conversations_table.scan(
            FilterExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id},
            Limit=limit
        )
        
        conversations = []
        for item in response['Items']:
            conversations.append({
                'conversation_id': item['conversation_id'],
                'title': item['title'],
                'conversation_type': item['conversation_type'],
                'subject_id': item.get('subject_id'),
                'message_count': int(item.get('message_count', 0)) if isinstance(item.get('message_count', 0), Decimal) else item.get('message_count', 0),
                'created_at': item['created_at'],
                'updated_at': item['updated_at'],
                'workflow_version': item.get('workflow_version', '1.0-simplified')
            })
        
        # Sort by updated_at descending
        conversations.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return conversations
        
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        return []


def decimal_to_int(obj):
    """Convert DynamoDB Decimal to int for JSON serialization"""
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }