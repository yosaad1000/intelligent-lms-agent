"""
LangGraph AI Agent with Intelligent Document Summarization
Enhanced chat handler using LangGraph for workflow orchestration
"""

import json
import boto3
import os
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, TypedDict
from decimal import Decimal

# Simplified imports for Lambda deployment
# Note: LangGraph functionality implemented with basic Python classes
from typing import Dict, Any, List, TypedDict, Callable
from dataclasses import dataclass

# Import shared services
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.agent_utils import agent_invoker
from shared.bedrock_agent_service import BedrockAgentError, BedrockAgentService, AgentContext
from file_processing.vector_storage import vector_storage, format_rag_context
from shared.pinecone_utils import pinecone_utils

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


@dataclass
class Message:
    """Simple message class"""
    content: str
    type: str = "human"  # "human" or "ai"

class AgentState(TypedDict):
    """Simplified agent state definition"""
    messages: List[Message]
    user_id: str
    conversation_id: str
    subject_id: str
    intent: str
    language: str
    documents: List[dict]
    rag_context: List[dict]
    entities: List[dict]
    key_phrases: List[dict]
    sentiment: dict
    summary_type: str
    tools_used: List[str]
    final_response: str
    citations: List[str]
    processing_metadata: dict

class SimpleWorkflow:
    """Simplified workflow orchestration without LangGraph dependency"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.conditional_edges = {}
        self.entry_point = None
    
    def add_node(self, name: str, func: Callable):
        """Add a processing node"""
        self.nodes[name] = func
    
    def add_edge(self, from_node: str, to_node: str):
        """Add a direct edge between nodes"""
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
    
    def add_conditional_edges(self, from_node: str, condition_func: Callable, mapping: dict):
        """Add conditional edges"""
        self.conditional_edges[from_node] = {
            'condition': condition_func,
            'mapping': mapping
        }
    
    def set_entry_point(self, node_name: str):
        """Set the entry point for the workflow"""
        self.entry_point = node_name
    
    async def ainvoke(self, initial_state: AgentState) -> AgentState:
        """Execute the workflow"""
        state = initial_state
        current_node = self.entry_point
        
        while current_node and current_node != "END":
            # Execute current node
            if current_node in self.nodes:
                state = await self.nodes[current_node](state)
            
            # Determine next node
            next_node = None
            
            # Check conditional edges first
            if current_node in self.conditional_edges:
                condition_func = self.conditional_edges[current_node]['condition']
                mapping = self.conditional_edges[current_node]['mapping']
                condition_result = condition_func(state)
                next_node = mapping.get(condition_result, "END")
            
            # Check direct edges
            elif current_node in self.edges:
                next_node = self.edges[current_node][0] if self.edges[current_node] else "END"
            
            else:
                next_node = "END"
            
            current_node = next_node
        
        return state


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Enhanced Lambda handler with LangGraph AI Agent
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
    """Handle POST /api/chat with LangGraph workflow"""
    
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
        
        # Process with LangGraph workflow
        response = asyncio.run(process_with_langgraph_workflow(user_id, message, conversation_id, subject_id))
        
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


async def process_with_langgraph_workflow(user_id: str, message: str, conversation_id: str = None, subject_id: str = None) -> Dict[str, Any]:
    """Process chat message using LangGraph workflow orchestration"""
    
    try:
        # Create or get conversation
        if not conversation_id:
            conversation_id = create_conversation(user_id, subject_id)
        
        # Initialize agent state
        initial_state = AgentState(
            messages=[Message(content=message, type="human")],
            user_id=user_id,
            conversation_id=conversation_id,
            subject_id=subject_id or "",
            intent="",
            language="en",
            documents=[],
            rag_context=[],
            entities=[],
            key_phrases=[],
            sentiment={},
            summary_type="",
            tools_used=[],
            final_response="",
            citations=[],
            processing_metadata={}
        )
        
        # Create and execute LangGraph workflow
        workflow = create_langgraph_workflow()
        result = await workflow.ainvoke(initial_state)
        
        # Store conversation with enhanced metadata
        store_langgraph_conversation(
            conversation_id, user_id, message, 
            result['final_response'], result['citations'], 
            result['processing_metadata']
        )
        
        return {
            'success': True,
            'response': result['final_response'],
            'conversation_id': conversation_id,
            'timestamp': datetime.utcnow().isoformat(),
            'citations': result['citations'],
            'intent_detected': result['intent'],
            'language_detected': result['language'],
            'tools_used': result['tools_used'],
            'rag_documents_used': len(result['rag_context']),
            'entities_extracted': len(result['entities']),
            'key_phrases_found': len(result['key_phrases']),
            'sentiment_analysis': result['sentiment'],
            'summary_type': result['summary_type'],
            'processing_metadata': result['processing_metadata'],
            'langgraph_workflow': True,
            'workflow_version': "1.0"
        }
        
    except Exception as e:
        logger.error(f"Error in LangGraph workflow: {str(e)}")
        
        # Fallback response
        fallback_response = "I apologize, but I'm experiencing technical difficulties with my advanced processing. Please try again in a moment."
        
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


def create_langgraph_workflow() -> SimpleWorkflow:
    """Create simplified workflow with intelligent document summarization"""
    
    # Create workflow graph
    workflow = SimpleWorkflow()
    
    # Add processing nodes
    workflow.add_node("language_detection", language_detection_node)
    workflow.add_node("intent_detection", intent_detection_node)
    workflow.add_node("document_processing", document_processing_node)
    workflow.add_node("rag_retrieval", rag_retrieval_node)
    workflow.add_node("summarization", summarization_node)
    workflow.add_node("question_answering", question_answering_node)
    workflow.add_node("translation", translation_node)
    workflow.add_node("response_synthesis", response_synthesis_node)
    
    # Define workflow edges
    workflow.set_entry_point("language_detection")
    
    # Language detection -> Intent detection
    workflow.add_edge("language_detection", "intent_detection")
    
    # Conditional routing based on intent
    workflow.add_conditional_edges(
        "intent_detection",
        route_based_on_intent,
        {
            "summarize": "document_processing",
            "question": "rag_retrieval", 
            "translate": "translation",
            "general": "rag_retrieval"
        }
    )
    
    # Document processing -> Summarization
    workflow.add_edge("document_processing", "summarization")
    
    # RAG retrieval -> Question answering
    workflow.add_edge("rag_retrieval", "question_answering")
    
    # Translation -> Response synthesis
    workflow.add_edge("translation", "response_synthesis")
    
    # All paths lead to response synthesis
    workflow.add_edge("summarization", "response_synthesis")
    workflow.add_edge("question_answering", "response_synthesis")
    
    # Response synthesis -> END
    workflow.add_edge("response_synthesis", "END")
    
    return workflow


async def language_detection_node(state: AgentState) -> AgentState:
    """Detect language using Amazon Comprehend"""
    
    try:
        user_message = state["messages"][-1].content
        
        # Use Comprehend for language detection
        response = comprehend.detect_dominant_language(Text=user_message)
        
        if response['Languages']:
            detected_language = response['Languages'][0]['LanguageCode']
            confidence = response['Languages'][0]['Score']
            
            state["language"] = detected_language
            state["processing_metadata"]["language_detection"] = {
                "detected_language": detected_language,
                "confidence": confidence,
                "all_languages": response['Languages']
            }
            
            logger.info(f"Detected language: {detected_language} (confidence: {confidence:.2f})")
        else:
            state["language"] = "en"  # Default to English
            
        state["tools_used"].append("language_detection")
        
    except Exception as e:
        logger.error(f"Error in language detection: {str(e)}")
        state["language"] = "en"  # Default fallback
        
    return state


async def intent_detection_node(state: AgentState) -> AgentState:
    """Detect user intent using Amazon Comprehend and keyword analysis"""
    
    try:
        user_message = state["messages"][-1].content.lower()
        
        # Use Comprehend for key phrase extraction
        key_phrases_response = comprehend.detect_key_phrases(
            Text=state["messages"][-1].content,
            LanguageCode=state["language"]
        )
        
        # Extract entities for better intent understanding
        entities_response = comprehend.detect_entities(
            Text=state["messages"][-1].content,
            LanguageCode=state["language"]
        )
        
        # Store Comprehend results
        state["key_phrases"] = key_phrases_response.get('KeyPhrases', [])
        state["entities"] = entities_response.get('Entities', [])
        
        # Intent classification based on keywords and phrases
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
            if any(keyword in user_message for keyword in keywords):
                detected_intent = intent
                break
        
        # Determine summary type if summarizing
        if detected_intent == "summarize":
            for s_type, keywords in summary_type_keywords.items():
                if any(keyword in user_message for keyword in keywords):
                    summary_type = s_type
                    break
        
        state["intent"] = detected_intent
        state["summary_type"] = summary_type
        state["processing_metadata"]["intent_detection"] = {
            "detected_intent": detected_intent,
            "summary_type": summary_type,
            "key_phrases_count": len(state["key_phrases"]),
            "entities_count": len(state["entities"])
        }
        
        state["tools_used"].append("intent_detection")
        
        logger.info(f"Detected intent: {detected_intent}, summary type: {summary_type}")
        
    except Exception as e:
        logger.error(f"Error in intent detection: {str(e)}")
        state["intent"] = "general"
        state["summary_type"] = "standard"
        
    return state


async def document_processing_node(state: AgentState) -> AgentState:
    """Process documents using AWS Textract and Comprehend for enhanced analysis"""
    
    try:
        user_id = state["user_id"]
        subject_id = state["subject_id"]
        
        # Get user's recent documents for processing
        documents = await get_user_documents_for_processing(user_id, subject_id)
        
        if not documents:
            logger.info("No documents found for processing")
            state["documents"] = []
            return state
        
        processed_docs = []
        
        for doc in documents[:3]:  # Process up to 3 most recent documents
            try:
                # Get document content from S3
                s3_key = doc.get('s3_key', '')
                if not s3_key:
                    continue
                
                # Enhanced document analysis using Textract (if needed) and Comprehend
                doc_analysis = await analyze_document_with_aws_services(s3_key, doc)
                
                processed_docs.append({
                    'file_id': doc.get('file_id', ''),
                    'filename': doc.get('filename', ''),
                    'content_preview': doc.get('content_preview', ''),
                    'analysis': doc_analysis,
                    's3_key': s3_key
                })
                
            except Exception as e:
                logger.error(f"Error processing document {doc.get('filename', 'unknown')}: {str(e)}")
                continue
        
        state["documents"] = processed_docs
        state["processing_metadata"]["document_processing"] = {
            "documents_processed": len(processed_docs),
            "total_documents_available": len(documents)
        }
        
        state["tools_used"].append("document_processing")
        
        logger.info(f"Processed {len(processed_docs)} documents for analysis")
        
    except Exception as e:
        logger.error(f"Error in document processing: {str(e)}")
        state["documents"] = []
        
    return state


async def rag_retrieval_node(state: AgentState) -> AgentState:
    """Retrieve relevant context using RAG with Bedrock Knowledge Base"""
    
    try:
        user_id = state["user_id"]
        subject_id = state["subject_id"]
        query = state["messages"][-1].content
        
        # Retrieve RAG context from user's documents
        rag_context, citations = await retrieve_rag_context_enhanced(
            user_id, query, subject_id, top_k=8
        )
        
        state["rag_context"] = rag_context
        state["citations"] = citations
        state["processing_metadata"]["rag_retrieval"] = {
            "documents_retrieved": len(rag_context),
            "citations_generated": len(citations),
            "query_processed": query[:100] + "..." if len(query) > 100 else query
        }
        
        state["tools_used"].append("rag_retrieval")
        
        logger.info(f"Retrieved {len(rag_context)} relevant documents for RAG")
        
    except Exception as e:
        logger.error(f"Error in RAG retrieval: {str(e)}")
        state["rag_context"] = []
        state["citations"] = []
        
    return state


async def summarization_node(state: AgentState) -> AgentState:
    """Generate intelligent summaries using Bedrock LLM"""
    
    try:
        summary_type = state["summary_type"]
        documents = state["documents"]
        rag_context = state["rag_context"]
        
        if not documents and not rag_context:
            state["final_response"] = "I don't have any documents to summarize. Please upload some documents first, and then I can provide summaries."
            return state
        
        # Combine document content and RAG context
        content_to_summarize = []
        
        # Add document content
        for doc in documents:
            content_to_summarize.append({
                'source': doc['filename'],
                'content': doc.get('content_preview', ''),
                'type': 'document'
            })
        
        # Add RAG context
        for context in rag_context:
            content_to_summarize.append({
                'source': context.get('source', 'Unknown'),
                'content': context.get('text', ''),
                'type': 'rag_chunk'
            })
        
        # Generate summary using Bedrock
        summary = await generate_intelligent_summary(content_to_summarize, summary_type)
        
        state["final_response"] = summary
        state["processing_metadata"]["summarization"] = {
            "summary_type": summary_type,
            "content_sources": len(content_to_summarize),
            "summary_length": len(summary)
        }
        
        state["tools_used"].append("summarization")
        
        logger.info(f"Generated {summary_type} summary from {len(content_to_summarize)} sources")
        
    except Exception as e:
        logger.error(f"Error in summarization: {str(e)}")
        state["final_response"] = "I encountered an error while generating the summary. Please try again."
        
    return state


async def question_answering_node(state: AgentState) -> AgentState:
    """Answer questions using RAG context and Bedrock LLM"""
    
    try:
        query = state["messages"][-1].content
        rag_context = state["rag_context"]
        
        if not rag_context:
            state["final_response"] = "I don't have enough context from your documents to answer this question. Please upload relevant documents first."
            return state
        
        # Generate answer using Bedrock with RAG context
        answer = await generate_contextual_answer(query, rag_context)
        
        state["final_response"] = answer
        state["processing_metadata"]["question_answering"] = {
            "query_length": len(query),
            "context_sources": len(rag_context),
            "answer_length": len(answer)
        }
        
        state["tools_used"].append("question_answering")
        
        logger.info(f"Generated answer using {len(rag_context)} context sources")
        
    except Exception as e:
        logger.error(f"Error in question answering: {str(e)}")
        state["final_response"] = "I encountered an error while processing your question. Please try again."
        
    return state


async def translation_node(state: AgentState) -> AgentState:
    """Handle translation requests using Amazon Translate"""
    
    try:
        user_message = state["messages"][-1].content
        source_language = state["language"]
        
        # Detect target language from message
        target_language = detect_target_language(user_message)
        
        if source_language != 'en':
            # Translate to English first
            translation_response = translate.translate_text(
                Text=user_message,
                SourceLanguageCode=source_language,
                TargetLanguageCode='en'
            )
            translated_text = translation_response['TranslatedText']
            
            state["final_response"] = f"Translation to English: {translated_text}"
        elif target_language and target_language != 'en':
            # Translate from English to target language
            # For demo, translate a sample response
            sample_response = "Hello! I can help you with your learning materials and answer questions about your documents."
            
            translation_response = translate.translate_text(
                Text=sample_response,
                SourceLanguageCode='en',
                TargetLanguageCode=target_language
            )
            translated_response = translation_response['TranslatedText']
            
            state["final_response"] = f"Translation to {target_language}: {translated_response}"
        else:
            state["final_response"] = "I can help you translate text between different languages. Please specify the target language."
        
        state["processing_metadata"]["translation"] = {
            "source_language": source_language,
            "target_language": target_language,
            "translation_performed": True
        }
        
        state["tools_used"].append("translation")
        
    except Exception as e:
        logger.error(f"Error in translation: {str(e)}")
        state["final_response"] = "I encountered an error with translation. Please try again."
        
    return state


async def response_synthesis_node(state: AgentState) -> AgentState:
    """Synthesize final response with context awareness"""
    
    try:
        # If final_response is already set by previous nodes, enhance it
        if state["final_response"]:
            # Add sentiment analysis
            if state["messages"][-1].content:
                sentiment_response = comprehend.detect_sentiment(
                    Text=state["messages"][-1].content,
                    LanguageCode=state["language"]
                )
                state["sentiment"] = {
                    "sentiment": sentiment_response.get('Sentiment', 'NEUTRAL'),
                    "confidence": sentiment_response.get('SentimentScore', {})
                }
            
            # Enhance response with citations if available
            if state["citations"]:
                citations_text = "\n\n**Sources:**\n" + "\n".join([f"• {citation}" for citation in state["citations"]])
                state["final_response"] += citations_text
        else:
            # Generate a general response if no specific response was created
            state["final_response"] = "I'm here to help you with your learning materials. You can ask me to summarize documents, answer questions, or translate text."
        
        state["processing_metadata"]["response_synthesis"] = {
            "final_response_length": len(state["final_response"]),
            "citations_included": len(state["citations"]) > 0,
            "sentiment_analyzed": bool(state["sentiment"])
        }
        
        state["tools_used"].append("response_synthesis")
        
        logger.info("Response synthesis completed")
        
    except Exception as e:
        logger.error(f"Error in response synthesis: {str(e)}")
        if not state["final_response"]:
            state["final_response"] = "I apologize, but I encountered an error processing your request. Please try again."
        
    return state


def route_based_on_intent(state: AgentState) -> str:
    """Route to appropriate processing node based on detected intent"""
    
    intent = state["intent"]
    
    if intent == "summarize":
        return "document_processing"
    elif intent == "question":
        return "rag_retrieval"
    elif intent == "translate":
        return "translation"
    else:
        return "rag_retrieval"  # default to RAG for general queries


# Helper functions

async def get_user_documents_for_processing(user_id: str, subject_id: str = None, limit: int = 5) -> List[dict]:
    """Get user's documents for processing"""
    
    try:
        files_table = dynamodb.Table('lms-user-files')
        
        if subject_id:
            # Query by subject if provided
            response = files_table.query(
                IndexName='user-subject-index',
                KeyConditionExpression='user_id = :user_id AND subject_id = :subject_id',
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':subject_id': subject_id
                },
                ScanIndexForward=False,
                Limit=limit
            )
        else:
            # Query all user documents
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


async def analyze_document_with_aws_services(s3_key: str, doc_metadata: dict) -> dict:
    """Analyze document using AWS Textract and Comprehend"""
    
    try:
        analysis = {
            'textract_used': False,
            'comprehend_analysis': {},
            'content_stats': {}
        }
        
        # Get content preview from metadata
        content = doc_metadata.get('content_preview', '')
        
        if content:
            # Use Comprehend for text analysis
            try:
                # Entity detection
                entities_response = comprehend.detect_entities(
                    Text=content,
                    LanguageCode='en'
                )
                
                # Key phrases
                phrases_response = comprehend.detect_key_phrases(
                    Text=content,
                    LanguageCode='en'
                )
                
                # Sentiment
                sentiment_response = comprehend.detect_sentiment(
                    Text=content,
                    LanguageCode='en'
                )
                
                analysis['comprehend_analysis'] = {
                    'entities': entities_response.get('Entities', [])[:5],  # Top 5
                    'key_phrases': phrases_response.get('KeyPhrases', [])[:10],  # Top 10
                    'sentiment': sentiment_response.get('Sentiment', 'NEUTRAL')
                }
                
            except Exception as e:
                logger.error(f"Comprehend analysis error: {str(e)}")
        
        # Content statistics
        analysis['content_stats'] = {
            'character_count': len(content),
            'word_count': len(content.split()) if content else 0,
            'has_content': bool(content)
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        return {'error': str(e)}


async def retrieve_rag_context_enhanced(user_id: str, query: str, subject_id: str = None, top_k: int = 8) -> tuple:
    """Enhanced RAG retrieval with better filtering and ranking"""
    
    try:
        # Query similar vectors from Pinecone
        similar_documents = vector_storage.query_similar_vectors(
            query_text=query,
            user_id=user_id,
            top_k=top_k,
            subject_id=subject_id,
            use_mock=not vector_storage.is_available()
        )
        
        if not similar_documents:
            return [], []
        
        # Enhanced filtering and ranking
        rag_context = []
        citations = []
        
        for doc in similar_documents:
            metadata = doc.get('metadata', {})
            text = doc.get('text', '')
            score = doc.get('score', 0)
            
            # More lenient threshold for summarization
            if score < 0.6:
                continue
            
            # Add to RAG context with enhanced metadata
            rag_context.append({
                'text': text,
                'source': metadata.get('filename', 'Unknown'),
                'chunk_index': metadata.get('chunk_index', 0),
                'score': score,
                'file_id': metadata.get('file_id', ''),
                'subject_id': metadata.get('subject_id'),
                'relevance_rank': len(rag_context) + 1
            })
            
            # Create citation
            filename = metadata.get('filename', 'Unknown')
            chunk_index = metadata.get('chunk_index', 0)
            citation = f"{filename} (section {chunk_index + 1})"
            if citation not in citations:
                citations.append(citation)
        
        return rag_context, citations
        
    except Exception as e:
        logger.error(f"Error in enhanced RAG retrieval: {str(e)}")
        return [], []


async def generate_intelligent_summary(content_sources: List[dict], summary_type: str) -> str:
    """Generate intelligent summary using Bedrock LLM"""
    
    try:
        # Prepare content for summarization
        combined_content = ""
        source_list = []
        
        for source in content_sources:
            content = source.get('content', '')
            source_name = source.get('source', 'Unknown')
            
            if content:
                combined_content += f"\n\n--- From {source_name} ---\n{content}"
                source_list.append(source_name)
        
        if not combined_content.strip():
            return "I don't have enough content to generate a summary. Please upload some documents first."
        
        # Create summary prompt based on type
        if summary_type == "brief":
            prompt = f"""Please provide a brief 3-5 point summary of the following content:

{combined_content}

Focus on the most important key points and main takeaways. Keep it concise and clear."""
        
        elif summary_type == "detailed":
            prompt = f"""Please provide a comprehensive and detailed summary of the following content:

{combined_content}

Include key concepts, important details, main arguments, conclusions, and any significant insights. Organize the information clearly with proper structure."""
        
        elif summary_type == "comprehensive":
            prompt = f"""Please provide a comprehensive analysis and summary of the following content:

{combined_content}

Include:
1. Main themes and concepts
2. Key details and supporting information
3. Important conclusions and insights
4. Connections between different ideas
5. Practical implications or applications

Organize this into a well-structured, thorough analysis."""
        
        else:  # standard
            prompt = f"""Please summarize the following content, highlighting the main points and key takeaways:

{combined_content}

Provide a clear, well-organized summary that captures the essential information."""
        
        # Use Bedrock to generate summary
        summary = await invoke_bedrock_model(prompt)
        
        # Add source information
        if source_list:
            unique_sources = list(set(source_list))
            sources_text = f"\n\n**Summary generated from:** {', '.join(unique_sources)}"
            summary += sources_text
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return f"I encountered an error while generating the {summary_type} summary. Please try again."


async def generate_contextual_answer(query: str, rag_context: List[dict]) -> str:
    """Generate contextual answer using RAG context and Bedrock LLM"""
    
    try:
        # Prepare context for the LLM
        context_text = ""
        sources = []
        
        for i, context in enumerate(rag_context):
            text = context.get('text', '')
            source = context.get('source', 'Unknown')
            
            if text:
                context_text += f"\n\n[Context {i+1} from {source}]\n{text}"
                if source not in sources:
                    sources.append(source)
        
        if not context_text.strip():
            return "I don't have enough relevant information from your documents to answer this question. Please upload relevant documents or try rephrasing your question."
        
        # Create answer prompt
        prompt = f"""Based on the following context from the user's documents, please answer their question accurately and comprehensively:

Question: {query}

Context:
{context_text}

Please provide a detailed answer based on the context provided. If the context doesn't contain enough information to fully answer the question, please indicate what information is available and what might be missing."""
        
        # Use Bedrock to generate answer
        answer = await invoke_bedrock_model(prompt)
        
        return answer
        
    except Exception as e:
        logger.error(f"Error generating contextual answer: {str(e)}")
        return "I encountered an error while processing your question. Please try again."


def detect_target_language(message: str) -> str:
    """Detect target language from user message"""
    
    language_indicators = {
        'es': ['spanish', 'español', 'en español'],
        'fr': ['french', 'français', 'en français'],
        'de': ['german', 'deutsch', 'auf deutsch'],
        'it': ['italian', 'italiano', 'in italiano'],
        'pt': ['portuguese', 'português', 'em português']
    }
    
    message_lower = message.lower()
    
    for lang_code, indicators in language_indicators.items():
        if any(indicator in message_lower for indicator in indicators):
            return lang_code
    
    return None


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
        'workflow_version': '1.0'
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
            'workflow_version': '1.0',
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
        
        response = conversations_table.query(
            IndexName='user-id-index',
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id},
            ScanIndexForward=False,
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
                'workflow_version': item.get('workflow_version', '1.0')
            })
        
        return conversations
        
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        return []


def decimal_to_int(obj):
    """Convert DynamoDB Decimal to int for JSON serialization"""
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError


async def invoke_bedrock_model(prompt: str, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0") -> str:
    """Invoke Bedrock model directly using boto3"""
    
    try:
        # Prepare the request body for Claude
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Invoke the model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(body)
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        
        # Extract the generated text
        if 'content' in response_body and response_body['content']:
            return response_body['content'][0]['text']
        else:
            return "I apologize, but I couldn't generate a proper response. Please try again."
            
    except Exception as e:
        logger.error(f"Error invoking Bedrock model: {str(e)}")
        return f"I encountered an error while processing your request: {str(e)}"


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'
    }