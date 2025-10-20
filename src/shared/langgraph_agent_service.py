"""
LangChain + LangGraph Agent Service
Provides graph-based AI agent orchestration with AWS services integration
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
from enum import Enum

# LangChain imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
# Memory will be handled by LangGraph checkpointer
# Tools will be defined as workflow nodes
from langchain_aws import ChatBedrock
from langchain_community.retrievers import AmazonKnowledgeBasesRetriever

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# AWS services
import boto3
from botocore.exceptions import ClientError

# Local imports
from .config import config
from .bedrock_agent_service import BedrockAgentService, AgentType, AgentContext
from .dynamodb_utils import db_utils

# Configure logging
logger = logging.getLogger(__name__)


class WorkflowIntent(Enum):
    """Enumeration of workflow intents"""
    SUMMARIZE = "summarize"
    QUESTION = "question"
    QUIZ = "quiz"
    TRANSLATE = "translate"
    ANALYZE = "analyze"
    GENERAL = "general"


class AgentState(TypedDict):
    """State definition for LangGraph workflow"""
    messages: List[BaseMessage]
    user_id: str
    session_id: str
    intent: str
    language: str
    documents: List[Dict[str, Any]]
    rag_context: List[Dict[str, Any]]
    user_profile: Dict[str, Any]
    tools_used: List[str]
    final_response: str
    citations: List[str]
    metadata: Dict[str, Any]


class LangGraphAgentService:
    """
    LangGraph-based AI agent with AWS services integration
    Provides dynamic workflow orchestration and state management
    """
    
    def __init__(self):
        """Initialize LangGraph agent service"""
        
        # Initialize AWS clients
        self.textract = boto3.client('textract', **config.get_aws_config())
        self.comprehend = boto3.client('comprehend', **config.get_aws_config())
        self.translate = boto3.client('translate', **config.get_aws_config())
        
        # Initialize LangChain LLM
        aws_config = config.get_aws_config()
        self.llm = ChatBedrock(
            model_id=config.BEDROCK_MODEL_ID,
            **aws_config
        )
        
        # Initialize Knowledge Base retriever
        if config.KNOWLEDGE_BASE_ID:
            self.kb_retriever = AmazonKnowledgeBasesRetriever(
                knowledge_base_id=config.KNOWLEDGE_BASE_ID,
                retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 5}}
            )
        else:
            self.kb_retriever = None
            logger.warning("Knowledge Base ID not configured - RAG retrieval disabled")
        
        # Initialize Bedrock Agent service for fallback
        self.bedrock_agent_service = BedrockAgentService()
        
        # Create LangGraph workflow
        self.workflow = self._create_workflow()
        
        # Initialize memory saver for conversation persistence
        self.memory = MemorySaver()
        
        # Compile the workflow
        self.agent_executor = self.workflow.compile(checkpointer=self.memory)
        
        logger.info("LangGraphAgentService initialized successfully")
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow with conditional routing"""
        
        # Create workflow graph
        workflow = StateGraph(AgentState)
        
        # Add processing nodes
        workflow.add_node("language_detection", self._detect_language_node)
        workflow.add_node("intent_detection", self._detect_intent_node)
        workflow.add_node("document_processing", self._process_documents_node)
        workflow.add_node("rag_retrieval", self._rag_retrieval_node)
        workflow.add_node("summarization", self._summarization_node)
        workflow.add_node("quiz_generation", self._quiz_generation_node)
        workflow.add_node("translation", self._translation_node)
        workflow.add_node("analysis", self._analysis_node)
        workflow.add_node("response_synthesis", self._response_synthesis_node)
        
        # Set entry point
        workflow.set_entry_point("language_detection")
        
        # Define workflow edges
        workflow.add_edge("language_detection", "intent_detection")
        
        # Conditional routing based on intent
        workflow.add_conditional_edges(
            "intent_detection",
            self._route_based_on_intent,
            {
                "summarize": "document_processing",
                "question": "rag_retrieval",
                "quiz": "quiz_generation",
                "translate": "translation",
                "analyze": "analysis",
                "general": "rag_retrieval"  # Default to RAG for general questions
            }
        )
        
        # Connect processing nodes to response synthesis
        workflow.add_edge("document_processing", "summarization")
        workflow.add_edge("summarization", "response_synthesis")
        workflow.add_edge("rag_retrieval", "response_synthesis")
        workflow.add_edge("quiz_generation", "response_synthesis")
        workflow.add_edge("translation", "response_synthesis")
        workflow.add_edge("analysis", "response_synthesis")
        
        # End workflow
        workflow.add_edge("response_synthesis", END)
        
        return workflow
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[AgentContext] = None
    ) -> Dict[str, Any]:
        """
        Process user message through LangGraph workflow
        
        Args:
            user_id: User identifier
            message: User message
            session_id: Optional session ID for conversation continuity
            context: Optional agent context
            
        Returns:
            Dictionary with agent response and metadata
        """
        
        try:
            # Create session ID if not provided
            if not session_id:
                session_id = f"session_{user_id}_{int(datetime.utcnow().timestamp())}"
            
            # Initialize agent state
            initial_state = {
                "messages": [HumanMessage(content=message)],
                "user_id": user_id,
                "session_id": session_id,
                "intent": "",
                "language": "en",
                "documents": [],
                "rag_context": [],
                "user_profile": context.user_profile if context else {},
                "tools_used": [],
                "final_response": "",
                "citations": [],
                "metadata": {}
            }
            
            # Execute workflow
            config_dict = {"configurable": {"thread_id": session_id}}
            result = await self.agent_executor.ainvoke(initial_state, config=config_dict)
            
            # Store conversation in DynamoDB
            await self._store_conversation(user_id, session_id, message, result)
            
            return {
                "success": True,
                "response": result["final_response"],
                "session_id": session_id,
                "intent": result["intent"],
                "language": result["language"],
                "citations": result["citations"],
                "tools_used": result["tools_used"],
                "metadata": result["metadata"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing message with LangGraph: {str(e)}")
            
            # Fallback to Bedrock Agent service
            try:
                if context:
                    fallback_response = await self.bedrock_agent_service.invoke_agent(
                        AgentType.CHAT, message, context
                    )
                    return {
                        "success": True,
                        "response": fallback_response.content,
                        "session_id": session_id,
                        "intent": "general",
                        "language": "en",
                        "citations": [str(cite) for cite in fallback_response.citations],
                        "tools_used": ["bedrock_agent_fallback"],
                        "metadata": fallback_response.metadata,
                        "timestamp": datetime.utcnow().isoformat(),
                        "fallback_used": True
                    }
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {str(fallback_error)}")
            
            return {
                "success": False,
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again later.",
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _detect_language_node(self, state: AgentState) -> AgentState:
        """Detect language of user message using Amazon Comprehend"""
        
        try:
            user_message = state["messages"][-1].content
            
            # Use Comprehend to detect language
            response = self.comprehend.detect_dominant_language(Text=user_message)
            
            if response['Languages']:
                detected_language = response['Languages'][0]['LanguageCode']
                state["language"] = detected_language
                state["tools_used"].append("comprehend_language_detection")
                
                logger.info(f"Detected language: {detected_language}")
            else:
                state["language"] = "en"  # Default to English
            
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            state["language"] = "en"  # Default to English
        
        return state
    
    async def _detect_intent_node(self, state: AgentState) -> AgentState:
        """Detect user intent using Amazon Comprehend and keyword analysis"""
        
        try:
            user_message = state["messages"][-1].content.lower()
            
            # Use Comprehend for key phrase extraction
            response = self.comprehend.detect_key_phrases(
                Text=user_message,
                LanguageCode=state["language"]
            )
            
            key_phrases = [phrase['Text'].lower() for phrase in response['KeyPhrases']]
            
            # Intent classification based on key phrases and keywords
            intent_keywords = {
                WorkflowIntent.SUMMARIZE: ['summary', 'summarize', 'key points', 'overview', 'main points'],
                WorkflowIntent.QUIZ: ['quiz', 'test', 'questions', 'assessment', 'exam'],
                WorkflowIntent.TRANSLATE: ['translate', 'translation', 'language', 'spanish', 'french'],
                WorkflowIntent.ANALYZE: ['analyze', 'analysis', 'progress', 'performance', 'insights']
            }
            
            detected_intent = WorkflowIntent.GENERAL  # Default
            
            # Check for intent keywords in message and key phrases
            for intent, keywords in intent_keywords.items():
                if any(keyword in user_message for keyword in keywords) or \
                   any(keyword in phrase for phrase in key_phrases for keyword in keywords):
                    detected_intent = intent
                    break
            
            state["intent"] = detected_intent.value
            state["tools_used"].append("comprehend_intent_detection")
            
            logger.info(f"Detected intent: {detected_intent.value}")
            
        except Exception as e:
            logger.warning(f"Intent detection failed: {str(e)}")
            state["intent"] = WorkflowIntent.GENERAL.value
        
        return state
    
    def _route_based_on_intent(self, state: AgentState) -> str:
        """Route to appropriate processing node based on detected intent"""
        
        intent = state["intent"]
        
        routing_map = {
            WorkflowIntent.SUMMARIZE.value: "summarize",
            WorkflowIntent.QUIZ.value: "quiz",
            WorkflowIntent.TRANSLATE.value: "translate",
            WorkflowIntent.ANALYZE.value: "analyze",
            WorkflowIntent.QUESTION.value: "question",
            WorkflowIntent.GENERAL.value: "general"
        }
        
        route = routing_map.get(intent, "general")
        logger.info(f"Routing to: {route}")
        
        return route
    
    async def _process_documents_node(self, state: AgentState) -> AgentState:
        """Process documents using AWS Textract and Comprehend"""
        
        try:
            # This would be enhanced to process specific documents
            # For now, we'll prepare for summarization by retrieving relevant docs
            user_message = state["messages"][-1].content
            
            # Retrieve relevant documents for summarization
            if self.kb_retriever:
                docs = await self.kb_retriever.aget_relevant_documents(user_message)
                
                state["documents"] = [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "source": doc.metadata.get("source", "Unknown")
                    }
                    for doc in docs
                ]
                
                state["tools_used"].append("knowledge_base_retrieval")
                logger.info(f"Retrieved {len(state['documents'])} documents for processing")
            
        except Exception as e:
            logger.warning(f"Document processing failed: {str(e)}")
            state["documents"] = []
        
        return state
    
    async def _rag_retrieval_node(self, state: AgentState) -> AgentState:
        """Retrieve relevant context using RAG"""
        
        try:
            user_message = state["messages"][-1].content
            
            if self.kb_retriever:
                # Retrieve relevant documents
                docs = await self.kb_retriever.aget_relevant_documents(user_message)
                
                rag_context = []
                citations = []
                
                for doc in docs:
                    rag_context.append({
                        "text": doc.page_content,
                        "source": doc.metadata.get("source", "Unknown"),
                        "score": doc.metadata.get("score", 0.0)
                    })
                    
                    # Create citation
                    source = doc.metadata.get("source", "Unknown")
                    if source not in citations:
                        citations.append(source)
                
                state["rag_context"] = rag_context
                state["citations"].extend(citations)
                state["tools_used"].append("rag_retrieval")
                
                logger.info(f"Retrieved {len(rag_context)} relevant documents")
            
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {str(e)}")
            state["rag_context"] = []
        
        return state
    
    async def _summarization_node(self, state: AgentState) -> AgentState:
        """Generate intelligent summaries using Bedrock LLM"""
        
        try:
            documents = state["documents"]
            
            if not documents:
                state["final_response"] = "I don't have any documents to summarize. Please upload some documents first."
                return state
            
            # Prepare summarization prompt
            doc_content = "\n\n".join([doc["content"][:1000] for doc in documents[:3]])
            
            summary_prompt = f"""
            Please provide a comprehensive summary of the following educational content:
            
            {doc_content}
            
            Focus on:
            - Key concepts and main ideas
            - Important details and facts
            - Learning objectives
            - Practical applications
            
            Provide a well-structured summary that would help a student understand the material.
            """
            
            # Generate summary using Bedrock LLM
            messages = [SystemMessage(content="You are an educational content summarizer."),
                       HumanMessage(content=summary_prompt)]
            
            response = await self.llm.ainvoke(messages)
            
            state["final_response"] = response.content
            state["tools_used"].append("bedrock_summarization")
            
            logger.info("Generated document summary")
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            state["final_response"] = "I apologize, but I couldn't generate a summary at this time."
        
        return state
    
    async def _quiz_generation_node(self, state: AgentState) -> AgentState:
        """Generate quiz questions using Bedrock LLM"""
        
        try:
            # This would be enhanced with document context
            user_message = state["messages"][-1].content
            
            quiz_prompt = f"""
            Based on the request: "{user_message}"
            
            Generate 5 multiple-choice questions for educational assessment.
            Format each question with:
            1. Question text
            2. Four answer options (A, B, C, D)
            3. Correct answer
            4. Brief explanation
            
            Make the questions challenging but fair for the educational level.
            """
            
            messages = [SystemMessage(content="You are an educational quiz generator."),
                       HumanMessage(content=quiz_prompt)]
            
            response = await self.llm.ainvoke(messages)
            
            state["final_response"] = response.content
            state["tools_used"].append("bedrock_quiz_generation")
            
            logger.info("Generated quiz questions")
            
        except Exception as e:
            logger.error(f"Quiz generation failed: {str(e)}")
            state["final_response"] = "I apologize, but I couldn't generate quiz questions at this time."
        
        return state
    
    async def _translation_node(self, state: AgentState) -> AgentState:
        """Handle translation using Amazon Translate"""
        
        try:
            user_message = state["messages"][-1].content
            source_language = state["language"]
            
            # Detect target language from message
            target_language = "en"  # Default to English
            
            if "spanish" in user_message.lower():
                target_language = "es"
            elif "french" in user_message.lower():
                target_language = "fr"
            
            # Translate if needed
            if source_language != target_language:
                response = self.translate.translate_text(
                    Text=user_message,
                    SourceLanguageCode=source_language,
                    TargetLanguageCode=target_language
                )
                
                translated_text = response['TranslatedText']
                
                state["final_response"] = f"Translation from {source_language} to {target_language}:\n\n{translated_text}"
                state["tools_used"].append("amazon_translate")
                
                logger.info(f"Translated text from {source_language} to {target_language}")
            else:
                state["final_response"] = "The text is already in the target language."
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            state["final_response"] = "I apologize, but I couldn't translate the text at this time."
        
        return state
    
    async def _analysis_node(self, state: AgentState) -> AgentState:
        """Perform learning analytics and progress analysis"""
        
        try:
            user_id = state["user_id"]
            
            # Basic analytics implementation
            # This would be enhanced with actual user data analysis
            
            analysis_prompt = f"""
            Provide learning analytics insights for user {user_id}.
            
            Based on the request, analyze:
            - Learning progress patterns
            - Areas of strength and improvement
            - Recommended learning paths
            - Study suggestions
            
            Provide actionable insights for educational improvement.
            """
            
            messages = [SystemMessage(content="You are an educational analytics expert."),
                       HumanMessage(content=analysis_prompt)]
            
            response = await self.llm.ainvoke(messages)
            
            state["final_response"] = response.content
            state["tools_used"].append("learning_analytics")
            
            logger.info("Generated learning analytics")
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            state["final_response"] = "I apologize, but I couldn't generate analytics at this time."
        
        return state
    
    async def _response_synthesis_node(self, state: AgentState) -> AgentState:
        """Synthesize final response with context and citations"""
        
        try:
            # If final_response is already set by a processing node, enhance it
            if state["final_response"]:
                response = state["final_response"]
            else:
                # Generate response using RAG context
                user_message = state["messages"][-1].content
                rag_context = state["rag_context"]
                
                if rag_context:
                    context_text = "\n\n".join([doc["text"][:500] for doc in rag_context[:3]])
                    
                    synthesis_prompt = f"""
                    User question: {user_message}
                    
                    Relevant context:
                    {context_text}
                    
                    Please provide a helpful and accurate response based on the context provided.
                    If the context doesn't contain relevant information, say so and provide general guidance.
                    """
                else:
                    synthesis_prompt = f"""
                    User question: {user_message}
                    
                    Please provide a helpful response. Since I don't have specific context documents,
                    I'll provide general educational guidance.
                    """
                
                messages = [SystemMessage(content="You are a helpful educational assistant."),
                           HumanMessage(content=synthesis_prompt)]
                
                response_obj = await self.llm.ainvoke(messages)
                response = response_obj.content
            
            # Add citations if available
            if state["citations"]:
                response += f"\n\nSources: {', '.join(state['citations'])}"
            
            state["final_response"] = response
            state["tools_used"].append("response_synthesis")
            
            # Add metadata
            state["metadata"] = {
                "workflow_completed": True,
                "intent_detected": state["intent"],
                "language_detected": state["language"],
                "tools_used_count": len(state["tools_used"]),
                "rag_documents_used": len(state["rag_context"]),
                "citations_count": len(state["citations"])
            }
            
            logger.info("Synthesized final response")
            
        except Exception as e:
            logger.error(f"Response synthesis failed: {str(e)}")
            state["final_response"] = "I apologize, but I couldn't generate a proper response at this time."
        
        return state
    
    async def _store_conversation(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        result: Dict[str, Any]
    ) -> None:
        """Store conversation in DynamoDB"""
        
        try:
            # Store conversation using existing DynamoDB utilities
            conversation_data = {
                "user_id": user_id,
                "session_id": session_id,
                "user_message": user_message,
                "ai_response": result["final_response"],
                "intent": result["intent"],
                "language": result["language"],
                "tools_used": result["tools_used"],
                "citations": result["citations"],
                "metadata": result["metadata"],
                "timestamp": datetime.utcnow().isoformat(),
                "workflow_type": "langgraph"
            }
            
            # Use existing DynamoDB utilities to store
            await db_utils.store_chat_message(conversation_data)
            
            logger.info(f"Stored LangGraph conversation for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {str(e)}")
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the LangGraph workflow"""
        
        return {
            "workflow_type": "LangGraph",
            "nodes": [
                "language_detection",
                "intent_detection", 
                "document_processing",
                "rag_retrieval",
                "summarization",
                "quiz_generation",
                "translation",
                "analysis",
                "response_synthesis"
            ],
            "supported_intents": [intent.value for intent in WorkflowIntent],
            "aws_services": [
                "Amazon Bedrock",
                "Amazon Comprehend",
                "Amazon Translate",
                "Amazon Textract",
                "DynamoDB"
            ],
            "features": [
                "Dynamic workflow routing",
                "Multi-language support",
                "RAG integration",
                "Conversation memory",
                "Intent detection",
                "Document processing"
            ]
        }


# Global service instance
langgraph_agent_service = LangGraphAgentService()