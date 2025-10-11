# AI Chat Microservice - MVP Requirements

## Overview
**Priority: CRITICAL (Build Third)**  
Core AI chat functionality using Bedrock Agent + Gradio for immediate student-AI interaction.

## Core User Stories

### US-CHAT-001: Ask Questions About Notes
**As a** student  
**I want to** ask questions about my uploaded notes  
**So that** I can get personalized explanations

#### Acceptance Criteria (EARS Format)
1. WHEN a student types a question THEN the system SHALL send it to Bedrock Agent
2. WHEN agent processes the query THEN the system SHALL retrieve context from student's Knowledge Base
3. WHEN response is generated THEN the system SHALL display answer with source citations
4. WHEN conversation continues THEN the system SHALL maintain chat history
5. IF no relevant content found THEN the system SHALL suggest uploading more materials

### US-CHAT-002: Conversational Learning
**As a** student  
**I want to** have natural conversations with AI  
**So that** I can learn through interactive dialogue

#### Acceptance Criteria
1. WHEN student asks follow-up questions THEN the system SHALL maintain conversation context
2. WHEN AI responds THEN the system SHALL adapt explanation complexity to student level
3. WHEN conversation gets long THEN the system SHALL summarize key points
4. WHEN student seems confused THEN the system SHALL offer alternative explanations

## Technical Implementation (Fast Build)

### Technology Stack
- **Frontend**: Gradio Chatbot component
- **AI Engine**: AWS Bedrock Agent with Nova LLM
- **Context**: Bedrock Knowledge Base integration
- **Storage**: DynamoDB for chat history (optional for MVP)

### MVP Implementation
```python
import gradio as gr
import boto3
import json
import uuid
from datetime import datetime

class FastAIChat:
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        self.agent_id = 'your-bedrock-agent-id'
        self.agent_alias_id = 'TSTALIASID'  # Test alias
        
    def chat_with_ai(self, message, history, user_id="demo_user"):
        """Main chat function"""
        if not message.strip():
            return history, ""
        
        try:
            # Generate session ID for conversation continuity
            session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H')}"
            
            # Call Bedrock Agent
            response = self.bedrock_agent.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=message,
                sessionState={
                    'sessionAttributes': {
                        'userId': user_id,
                        'timestamp': str(datetime.now())
                    }
                }
            )
            
            # Process streaming response
            ai_response = ""
            citations = []
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        ai_response += chunk['bytes'].decode('utf-8')
                elif 'trace' in event:
                    # Extract citations if available
                    trace = event['trace']
                    if 'orchestrationTrace' in trace:
                        citations.extend(self._extract_citations(trace))
            
            # Format response with citations
            formatted_response = ai_response
            if citations:
                formatted_response += "\n\n📚 **Sources:**\n"
                for i, citation in enumerate(citations[:3], 1):  # Limit to 3 sources
                    formatted_response += f"{i}. {citation}\n"
            
            # Update chat history
            history.append([message, formatted_response])
            
            return history, ""
            
        except Exception as e:
            error_response = f"❌ Sorry, I encountered an error: {str(e)}\n\nPlease try rephrasing your question or check if you have uploaded study materials."
            history.append([message, error_response])
            return history, ""
    
    def _extract_citations(self, trace):
        """Extract source citations from agent trace"""
        citations = []
        try:
            # This would extract actual citations from the trace
            # For MVP, return placeholder
            citations.append("Your uploaded study notes")
        except:
            pass
        return citations
    
    def clear_chat(self):
        """Clear chat history"""
        return []
    
    def get_suggested_questions(self, user_id="demo_user"):
        """Generate suggested questions based on uploaded content"""
        suggestions = [
            "What are the main concepts in my notes?",
            "Can you summarize the key points?",
            "Explain this topic in simple terms",
            "What should I focus on studying?",
            "Create a study plan for me"
        ]
        return suggestions

# Gradio Interface
def create_chat_interface():
    ai_chat = FastAIChat()
    
    with gr.Blocks() as chat_app:
        gr.Markdown("# 🤖 AI Learning Assistant")
        gr.Markdown("Ask questions about your uploaded study materials!")
        
        # Main chat interface
        chatbot = gr.Chatbot(
            label="AI Tutor",
            height=500,
            placeholder="👋 Hi! I'm your AI learning assistant. Upload some study notes and ask me questions about them!"
        )
        
        with gr.Row():
            msg_input = gr.Textbox(
                label="Your Question",
                placeholder="Ask me anything about your study materials...",
                scale=4
            )
            send_btn = gr.Button("Send 📤", variant="primary", scale=1)
        
        with gr.Row():
            clear_btn = gr.Button("Clear Chat 🗑️", variant="secondary")
            
        # Suggested questions
        gr.Markdown("### 💡 Suggested Questions")
        suggestions = ai_chat.get_suggested_questions()
        
        with gr.Row():
            for i, suggestion in enumerate(suggestions[:3]):
                suggest_btn = gr.Button(suggestion, variant="outline")
                suggest_btn.click(
                    lambda s=suggestion: s,
                    outputs=[msg_input]
                )
        
        # Event handlers
        send_btn.click(
            fn=ai_chat.chat_with_ai,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )
        
        msg_input.submit(
            fn=ai_chat.chat_with_ai,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )
        
        clear_btn.click(
            fn=ai_chat.clear_chat,
            outputs=[chatbot]
        )
    
    return chat_app

# Enhanced version with context awareness
class EnhancedAIChat(FastAIChat):
    def __init__(self):
        super().__init__()
        self.conversation_context = {}
    
    def chat_with_context(self, message, history, user_id="demo_user"):
        """Enhanced chat with better context management"""
        
        # Add conversation context to the message
        context_message = self._add_context(message, history, user_id)
        
        # Use the base chat function
        return self.chat_with_ai(context_message, history, user_id)
    
    def _add_context(self, message, history, user_id):
        """Add relevant context to improve AI responses"""
        
        # For MVP, keep it simple
        if len(history) > 0:
            recent_context = f"Previous conversation context: {history[-1][0] if history else ''}\n\nCurrent question: {message}"
            return recent_context
        
        return message
```

## Testing Strategy
1. **Unit Test**: Test Bedrock Agent integration with mock responses
2. **Integration Test**: Upload file → Ask questions → Verify relevant answers
3. **Manual Test**: Have conversations via Gradio interface
4. **Context Test**: Verify conversation continuity and context retention

## Dependencies
- File Processor service (for Knowledge Base content)
- Authentication service (for user identification)

## Delivery Timeline
- **Day 1**: Basic Bedrock Agent integration
- **Day 2**: Gradio chat interface and conversation flow
- **Day 3**: Context management and citation extraction
- **Day 4**: Testing and optimization