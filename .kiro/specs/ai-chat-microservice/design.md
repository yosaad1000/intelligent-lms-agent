# AI Chat Microservice Design

## Architecture Overview

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Gradio Chat    │───▶│  Chat Handler   │───▶│ Bedrock Agent   │
│   Interface     │    │  & Manager      │    │   (Nova LLM)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Chat History    │    │ Context Manager │    │ Knowledge Base  │
│   Storage       │    │  & Citations    │    │   (User Notes)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   Agent Tools   │
                    │  (Quiz, Voice)  │
                    └─────────────────┘
```

### Conversation Flow
1. **Input**: User Question → Context Analysis → Agent Invocation
2. **Processing**: Bedrock Agent → Knowledge Base Query → Tool Selection
3. **Response**: AI Response → Citation Extraction → History Storage
4. **Display**: Formatted Response → Gradio Interface → User Feedback

## Technical Design

### Core Classes
```python
class FastAIChat:
    """Main AI chat handler with Bedrock Agent integration"""
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        self.dynamodb = boto3.resource('dynamodb')
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
        self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
        self.context_manager = ConversationContextManager()
        self.citation_extractor = CitationExtractor()
        
    def chat_with_ai(self, message: str, history: List, user_id: str) -> Tuple[List, str]
    def process_agent_response(self, response: dict) -> dict
    def extract_citations(self, agent_trace: dict) -> List[dict]
    def store_conversation(self, user_id: str, message: str, response: str) -> bool

class ConversationContextManager:
    """Manage conversation context and memory"""
    def __init__(self):
        self.context_window = 10  # Last 10 messages
        self.context_cache = {}
    
    def build_context(self, history: List, user_id: str) -> str
    def extract_key_concepts(self, conversation: List) -> List[str]
    def get_conversation_summary(self, history: List) -> str
    def update_user_context(self, user_id: str, new_context: dict) -> None

class BedrockAgentManager:
    """Enhanced Bedrock Agent interaction"""
    def __init__(self):
        self.agent_client = boto3.client('bedrock-agent-runtime')
        self.session_cache = {}
    
    def invoke_agent_with_context(self, message: str, context: dict) -> dict
    def handle_streaming_response(self, response_stream) -> Tuple[str, List[dict]]
    def extract_tool_usage(self, trace_data: dict) -> List[dict]
    def manage_session_state(self, user_id: str, session_data: dict) -> str

class CitationExtractor:
    """Extract and format source citations"""
    def extract_from_trace(self, trace: dict) -> List[dict]
    def format_citations(self, citations: List[dict]) -> str
    def validate_citations(self, citations: List[dict]) -> List[dict]
```

### Bedrock Agent Configuration
```json
{
  "agentName": "lms-learning-assistant",
  "foundationModel": "anthropic.claude-3-sonnet-20240229-v1:0",
  "instruction": "You are an intelligent learning assistant that helps students understand their study materials. You have access to their uploaded notes through a Knowledge Base and can use various tools to help them learn effectively.\n\nYour capabilities:\n1. Answer questions about uploaded study materials\n2. Generate personalized quizzes\n3. Analyze voice responses\n4. Create learning paths\n5. Provide explanations adapted to the student's level\n\nAlways:\n- Cite sources from their uploaded materials\n- Adapt explanations to the student's understanding level\n- Encourage learning and provide constructive feedback\n- Ask follow-up questions to deepen understanding\n- Suggest related topics for further study",
  "knowledgeBases": [
    {
      "knowledgeBaseId": "your-kb-id",
      "description": "Student uploaded study materials and notes"
    }
  ],
  "actionGroups": [
    {
      "actionGroupName": "quiz-generator",
      "description": "Generate personalized quizzes based on student content",
      "actionGroupExecutor": {
        "lambda": "arn:aws:lambda:region:account:function:quiz-generator-tool"
      }
    },
    {
      "actionGroupName": "voice-analyzer", 
      "description": "Analyze student voice responses for learning assessment",
      "actionGroupExecutor": {
        "lambda": "arn:aws:lambda:region:account:function:voice-analyzer-tool"
      }
    },
    {
      "actionGroupName": "learning-path",
      "description": "Create personalized learning paths and study recommendations",
      "actionGroupExecutor": {
        "lambda": "arn:aws:lambda:region:account:function:learning-path-tool"
      }
    }
  ]
}
```

### Advanced Chat Handler
```python
class EnhancedAIChat(FastAIChat):
    """Enhanced chat with advanced features"""
    
    def __init__(self):
        super().__init__()
        self.conversation_analyzer = ConversationAnalyzer()
        self.response_personalizer = ResponsePersonalizer()
        self.learning_tracker = LearningProgressTracker()
    
    async def chat_with_enhanced_ai(self, message: str, history: List, user_id: str) -> dict:
        """Enhanced chat with personalization and learning tracking"""
        
        # 1. Analyze conversation context
        context = self.context_manager.build_context(history, user_id)
        user_profile = await self.get_user_learning_profile(user_id)
        
        # 2. Enhance message with context
        enhanced_message = self._enhance_message_with_context(message, context, user_profile)
        
        # 3. Invoke Bedrock Agent
        agent_response = await self.invoke_agent_async(enhanced_message, user_id)
        
        # 4. Personalize response
        personalized_response = self.response_personalizer.adapt_response(
            agent_response, user_profile
        )
        
        # 5. Track learning progress
        await self.learning_tracker.update_progress(user_id, message, personalized_response)
        
        # 6. Store conversation
        await self.store_conversation_async(user_id, message, personalized_response)
        
        return {
            'response': personalized_response['text'],
            'citations': personalized_response['citations'],
            'suggestions': personalized_response['follow_up_questions'],
            'learning_insights': personalized_response['learning_insights']
        }
    
    def _enhance_message_with_context(self, message: str, context: str, profile: dict) -> str:
        """Add context and personalization to user message"""
        
        enhanced_prompt = f"""
        Student Question: {message}
        
        Conversation Context: {context}
        
        Student Learning Profile:
        - Learning Level: {profile.get('level', 'intermediate')}
        - Preferred Explanation Style: {profile.get('style', 'balanced')}
        - Strong Concepts: {', '.join(profile.get('strengths', []))}
        - Areas for Improvement: {', '.join(profile.get('weaknesses', []))}
        - Recent Topics: {', '.join(profile.get('recent_topics', []))}
        
        Please provide a response that:
        1. Directly answers the student's question
        2. Adapts to their learning level and style
        3. References their uploaded study materials when relevant
        4. Builds on their strengths and addresses weaknesses
        5. Suggests follow-up questions or related topics
        """
        
        return enhanced_prompt
```

### Conversation Storage Schema
```json
{
  "TableName": "lms-chat-history",
  "KeySchema": [
    {
      "AttributeName": "user_id",
      "KeyType": "HASH"
    },
    {
      "AttributeName": "timestamp",
      "KeyType": "RANGE"
    }
  ],
  "AttributeDefinitions": [
    {
      "AttributeName": "user_id",
      "AttributeType": "S"
    },
    {
      "AttributeName": "timestamp",
      "AttributeType": "N"
    },
    {
      "AttributeName": "conversation_id",
      "AttributeType": "S"
    }
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "conversation-id-index",
      "KeySchema": [
        {
          "AttributeName": "conversation_id",
          "KeyType": "HASH"
        }
      ]
    }
  ]
}
```

### Chat Message Structure
```json
{
  "user_id": "user-uuid",
  "timestamp": 1701234567890,
  "conversation_id": "conv-uuid",
  "message_id": "msg-uuid",
  "user_message": "Can you explain entropy?",
  "ai_response": "Entropy is a measure of disorder in a system...",
  "citations": [
    {
      "source": "thermodynamics_notes.pdf",
      "page": 15,
      "text": "Entropy always increases in isolated systems",
      "confidence": 0.95
    }
  ],
  "context_used": {
    "knowledge_base_queries": ["entropy", "thermodynamics"],
    "tools_invoked": [],
    "conversation_history_length": 5
  },
  "response_metadata": {
    "processing_time": 2.3,
    "tokens_used": 150,
    "confidence_score": 0.88,
    "personalization_applied": true
  },
  "learning_insights": {
    "concepts_discussed": ["entropy", "thermodynamics", "disorder"],
    "difficulty_level": "intermediate",
    "follow_up_suggestions": [
      "Would you like to see how entropy applies to real-world examples?",
      "Should we discuss the mathematical formulation of entropy?"
    ]
  }
}
```

## Gradio Interface Design

### Enhanced Chat Interface
```python
def create_enhanced_chat_interface():
    with gr.Blocks() as chat_app:
        gr.Markdown("# 🤖 AI Learning Assistant")
        
        # Chat interface with enhanced features
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="AI Tutor",
                    height=600,
                    show_label=True,
                    container=True,
                    bubble_full_width=False
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Ask a question",
                        placeholder="Ask me anything about your study materials...",
                        scale=4,
                        container=False
                    )
                    send_btn = gr.Button("Send 📤", variant="primary", scale=1)
                
                # Quick action buttons
                with gr.Row():
                    summarize_btn = gr.Button("📋 Summarize Notes", variant="outline")
                    quiz_btn = gr.Button("📝 Generate Quiz", variant="outline")
                    explain_btn = gr.Button("💡 Explain Concept", variant="outline")
            
            with gr.Column(scale=1):
                # Learning insights panel
                gr.Markdown("### 📊 Learning Insights")
                
                current_topic = gr.Textbox(
                    label="Current Topic",
                    interactive=False,
                    container=True
                )
                
                concepts_discussed = gr.JSON(
                    label="Concepts Discussed",
                    container=True
                )
                
                follow_up_suggestions = gr.Markdown(
                    "### 💭 Suggested Questions",
                    container=True
                )
                
                # Citation panel
                gr.Markdown("### 📚 Sources")
                citations_display = gr.JSON(
                    label="Current Citations",
                    container=True
                )
        
        # Advanced features
        with gr.Accordion("Advanced Options", open=False):
            with gr.Row():
                response_style = gr.Dropdown(
                    choices=["Simple", "Detailed", "Technical", "Conversational"],
                    value="Balanced",
                    label="Response Style"
                )
                
                difficulty_level = gr.Dropdown(
                    choices=["Beginner", "Intermediate", "Advanced"],
                    value="Intermediate", 
                    label="Explanation Level"
                )
            
            context_length = gr.Slider(
                minimum=3,
                maximum=20,
                value=10,
                step=1,
                label="Conversation Memory (messages)"
            )
        
        # Chat state management
        chat_state = gr.State({
            'conversation_id': None,
            'user_profile': {},
            'current_context': {}
        })
    
    return chat_app
```

### Response Processing Pipeline
```python
class ResponseProcessor:
    """Process and enhance AI responses"""
    
    def process_agent_response(self, raw_response: dict, user_profile: dict) -> dict:
        """Process raw agent response into enhanced format"""
        
        # Extract main response text
        response_text = self._extract_response_text(raw_response)
        
        # Extract citations
        citations = self._extract_citations(raw_response)
        
        # Generate follow-up questions
        follow_ups = self._generate_follow_up_questions(response_text, user_profile)
        
        # Extract learning insights
        insights = self._extract_learning_insights(response_text, user_profile)
        
        # Format for Gradio display
        formatted_response = self._format_for_gradio(
            response_text, citations, follow_ups, insights
        )
        
        return formatted_response
    
    def _format_for_gradio(self, text: str, citations: List, follow_ups: List, insights: dict) -> str:
        """Format response for optimal Gradio display"""
        
        formatted = text
        
        # Add citations if available
        if citations:
            formatted += "\n\n📚 **Sources:**\n"
            for i, citation in enumerate(citations[:3], 1):
                formatted += f"{i}. {citation['source']} (p. {citation.get('page', 'N/A')})\n"
        
        # Add follow-up suggestions
        if follow_ups:
            formatted += "\n\n💭 **You might also ask:**\n"
            for question in follow_ups[:2]:
                formatted += f"• {question}\n"
        
        # Add learning insight
        if insights.get('difficulty_feedback'):
            formatted += f"\n\n📈 **Learning Note:** {insights['difficulty_feedback']}"
        
        return formatted
```

## Context Management

### Conversation Context Strategy
```python
class AdvancedContextManager:
    """Advanced conversation context management"""
    
    def __init__(self):
        self.context_strategies = {
            'sliding_window': self._sliding_window_context,
            'semantic_clustering': self._semantic_clustering_context,
            'topic_based': self._topic_based_context,
            'adaptive': self._adaptive_context
        }
    
    def build_optimal_context(self, history: List, user_id: str, strategy: str = 'adaptive') -> str:
        """Build optimal context using specified strategy"""
        
        context_builder = self.context_strategies.get(strategy, self._adaptive_context)
        return context_builder(history, user_id)
    
    def _adaptive_context(self, history: List, user_id: str) -> str:
        """Adaptive context based on conversation patterns"""
        
        if len(history) <= 3:
            # Short conversation - use all history
            return self._format_full_history(history)
        
        elif self._is_topic_focused(history):
            # Topic-focused conversation - use topic-based context
            return self._topic_based_context(history, user_id)
        
        else:
            # General conversation - use sliding window
            return self._sliding_window_context(history, user_id)
    
    def _semantic_clustering_context(self, history: List, user_id: str) -> str:
        """Group related messages for better context"""
        
        # Group messages by semantic similarity
        clusters = self._cluster_messages_by_similarity(history)
        
        # Select most relevant clusters
        relevant_clusters = self._select_relevant_clusters(clusters, history[-1])
        
        # Build context from relevant clusters
        context = ""
        for cluster in relevant_clusters:
            context += f"Topic: {cluster['topic']}\n"
            for msg in cluster['messages'][-2:]:  # Last 2 from each cluster
                context += f"Student: {msg[0]}\nAI: {msg[1]}\n\n"
        
        return context
```

## Learning Progress Integration

### Learning Analytics
```python
class LearningProgressTracker:
    """Track and analyze learning progress"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.progress_table = self.dynamodb.Table('lms-learning-progress')
    
    async def update_progress(self, user_id: str, question: str, response: dict) -> None:
        """Update learning progress based on conversation"""
        
        # Extract concepts from conversation
        concepts = self._extract_concepts(question, response['text'])
        
        # Analyze question complexity
        complexity = self._analyze_question_complexity(question)
        
        # Update concept mastery
        await self._update_concept_mastery(user_id, concepts, complexity)
        
        # Track learning patterns
        await self._track_learning_patterns(user_id, {
            'question_type': self._classify_question_type(question),
            'response_quality': response.get('confidence_score', 0.5),
            'concepts': concepts,
            'timestamp': datetime.now().isoformat()
        })
    
    def _extract_concepts(self, question: str, response: str) -> List[str]:
        """Extract key concepts from conversation"""
        
        # Use simple keyword extraction for MVP
        # In production, use more sophisticated NLP
        
        combined_text = f"{question} {response}".lower()
        
        # Common academic concepts (expandable)
        concept_keywords = {
            'thermodynamics': ['thermodynamics', 'entropy', 'enthalpy', 'heat', 'temperature'],
            'physics': ['force', 'energy', 'momentum', 'velocity', 'acceleration'],
            'chemistry': ['molecule', 'atom', 'reaction', 'bond', 'element'],
            'mathematics': ['equation', 'function', 'derivative', 'integral', 'limit']
        }
        
        identified_concepts = []
        for concept, keywords in concept_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                identified_concepts.append(concept)
        
        return identified_concepts
```

## Error Handling & Recovery

### Chat Error Management
```python
class ChatErrorHandler:
    """Handle chat-specific errors gracefully"""
    
    def __init__(self):
        self.fallback_responses = {
            'bedrock_timeout': "I'm taking a bit longer to process your question. Let me try a simpler approach...",
            'knowledge_base_empty': "I don't see any uploaded study materials yet. Please upload some notes first so I can help you better!",
            'context_too_long': "Our conversation is getting quite long. Let me focus on your current question...",
            'agent_error': "I encountered a technical issue. Let me try to help you in a different way..."
        }
    
    def handle_chat_error(self, error: Exception, context: dict) -> str:
        """Handle chat errors with appropriate fallback"""
        
        error_type = self._classify_error(error)
        
        if error_type in self.fallback_responses:
            fallback_response = self.fallback_responses[error_type]
            
            # Log error for debugging
            self._log_error(error, context)
            
            # Try alternative approach
            if error_type == 'bedrock_timeout':
                return self._try_simple_response(context['message'])
            elif error_type == 'knowledge_base_empty':
                return self._provide_general_help()
            
            return fallback_response
        
        # Generic error handling
        return "I apologize, but I'm having trouble processing your request right now. Could you try rephrasing your question?"
    
    def _try_simple_response(self, message: str) -> str:
        """Provide simple response when main agent fails"""
        
        # Simple pattern matching for common questions
        message_lower = message.lower()
        
        if 'what is' in message_lower or 'define' in message_lower:
            return "I'd be happy to explain that concept! However, I'm having trouble accessing your specific study materials right now. Could you provide some context about what you're studying?"
        
        elif 'how' in message_lower:
            return "That's a great question about the process or method! While I work on accessing your materials, could you tell me more about the specific context you're asking about?"
        
        elif 'why' in message_lower:
            return "Understanding the reasoning behind concepts is important! I'm having some technical difficulties right now, but I'd love to help explain the 'why' once I can access your study materials properly."
        
        return "I'm having some technical difficulties but I'm here to help! Could you try asking your question in a different way?"
```

## Performance Optimization

### Response Caching
```python
class ResponseCache:
    """Cache responses for better performance"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_size = 1000
    
    def get_cached_response(self, message_hash: str, user_id: str) -> Optional[dict]:
        """Get cached response if available and valid"""
        
        cache_key = f"{user_id}:{message_hash}"
        
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            
            # Check if cache is still valid
            if time.time() - cached_item['timestamp'] < self.cache_ttl:
                return cached_item['response']
            else:
                # Remove expired cache
                del self.cache[cache_key]
        
        return None
    
    def cache_response(self, message_hash: str, user_id: str, response: dict) -> None:
        """Cache response for future use"""
        
        cache_key = f"{user_id}:{message_hash}"
        
        # Implement LRU eviction if cache is full
        if len(self.cache) >= self.max_cache_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        self.cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
```

## Integration Points

### With File Processor Service
- Query Knowledge Base for relevant content
- Access file metadata for context
- Reference specific documents in responses

### With Voice Interview Service
- Provide conversational AI for interview questions
- Analyze voice responses using same agent
- Share conversation context between modalities

### With Quiz Generator Service
- Generate quiz questions through agent tools
- Provide explanations for quiz answers
- Track quiz performance in conversation context

### With Authentication Service
- Validate user tokens for personalized responses
- Access user learning profiles
- Maintain user-specific conversation history

## Testing Strategy

### Unit Tests
- Test Bedrock Agent integration
- Test conversation context management
- Test citation extraction
- Test error handling scenarios

### Integration Tests
- Test Knowledge Base query functionality
- Test agent tool invocation
- Test conversation persistence
- Test cross-service communication

### Performance Tests
- Test response time under load
- Test concurrent conversation handling
- Test memory usage with long conversations
- Test caching effectiveness

### User Experience Tests
- Test conversation flow naturalness
- Test response relevance and accuracy
- Test citation quality and relevance
- Test personalization effectiveness