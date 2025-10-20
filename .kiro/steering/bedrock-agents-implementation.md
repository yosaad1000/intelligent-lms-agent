# LangGraph + Bedrock AgentCore Implementation Guide

## Core Architecture
We are building production-grade AI Agents using **LangGraph + LangChain** for agent logic deployed on **Amazon Bedrock AgentCore** infrastructure. This combines the flexibility of LangGraph workflows with AWS's fully managed deployment platform.

## Technology Stack

### Core Framework
- **LangGraph**: Graph-based agent workflow orchestration
- **LangChain**: Agent building blocks (tools, memory, retrievers)
- **Amazon Bedrock AgentCore**: Fully managed deployment and scaling
- **AWS Bedrock**: LLM inference (Claude, Nova models)
- **Bedrock Knowledge Bases**: Managed RAG with vector storage

### AWS Services Integration
- **AWS Textract**: Advanced document text extraction (PDFs, images, forms)
- **Amazon Comprehend**: Natural language processing (sentiment, entities, key phrases)
- **Amazon Translate**: Multi-language support
- **Bedrock Knowledge Base**: Managed vector storage and retrieval
- **DynamoDB**: Conversation memory and user data
- **S3**: Document storage
- **API Gateway**: RESTful endpoints for agent invocation

## LangGraph Agent Architecture

### LangGraph Workflow Definition
```python
from langgraph.graph import StateGraph, END
from langchain.tools import Tool
from langchain_aws import BedrockLLM
from langchain.memory import DynamoDBChatMessageHistory
from typing import TypedDict, List
from langchain.schema import BaseMessage, HumanMessage, AIMessage

# Define agent state
class LMSAgentState(TypedDict):
    messages: List[BaseMessage]
    user_id: str
    documents: List[dict]
    intent: str
    tools_used: List[str]
    context: dict
    final_response: str

class LMSLangGraphAgent:
    def __init__(self):
        self.llm = BedrockLLM(
            model_id="amazon.nova-micro-v1:0",  # Cost-effective for development
            region_name="us-east-1"
        )
        self.workflow = self._create_workflow()
        self.agent_executor = self.workflow.compile()
    
    def _create_workflow(self):
        """Create LangGraph workflow for LMS agent"""
        
        workflow = StateGraph(LMSAgentState)
        
        # Add nodes (processing steps)
        workflow.add_node("intent_detection", self.detect_intent)
        workflow.add_node("document_processing", self.process_documents)
        workflow.add_node("rag_retrieval", self.retrieve_context)
        workflow.add_node("summarization", self.generate_summary)
        workflow.add_node("quiz_generation", self.create_quiz)
        workflow.add_node("analytics", self.track_analytics)
        workflow.add_node("response_synthesis", self.synthesize_response)
        
        # Define conditional edges (dynamic routing)
        workflow.add_conditional_edges(
            "intent_detection",
            self.route_based_on_intent,
            {
                "summarize": "document_processing",
                "question": "rag_retrieval", 
                "quiz": "quiz_generation",
                "analytics": "analytics",
                "default": "rag_retrieval"
            }
        )
        
        # Connect processing nodes to response synthesis
        workflow.add_edge("document_processing", "response_synthesis")
        workflow.add_edge("rag_retrieval", "response_synthesis")
        workflow.add_edge("quiz_generation", "response_synthesis")
        workflow.add_edge("analytics", "response_synthesis")
        workflow.add_edge("response_synthesis", END)
        
        # Set entry point
        workflow.set_entry_point("intent_detection")
        
        return workflow
    
    async def detect_intent(self, state: LMSAgentState) -> LMSAgentState:
        """Detect user intent using LLM"""
        
        user_message = state["messages"][-1].content
        
        intent_prompt = f"""
        Analyze the user message and classify the intent:
        
        User message: "{user_message}"
        
        Intent categories:
        - summarize: User wants a summary of documents
        - question: User has a question about content
        - quiz: User wants to generate or take a quiz
        - analytics: User wants learning progress/analytics
        
        Respond with just the intent category.
        """
        
        intent_response = await self.llm.ainvoke(intent_prompt)
        detected_intent = intent_response.content.strip().lower()
        
        state["intent"] = detected_intent
        return state
    
    def route_based_on_intent(self, state: LMSAgentState) -> str:
        """Route to appropriate processing node based on intent"""
        
        intent = state["intent"]
        
        if "summarize" in intent:
            return "summarize"
        elif "quiz" in intent:
            return "quiz"
        elif "analytics" in intent:
            return "analytics"
        else:
            return "question"  # default to RAG retrieval
    
    async def process_documents(self, state: LMSAgentState) -> LMSAgentState:
        """Process documents using AWS services"""
        
        # Use Textract and Comprehend for document analysis
        import boto3
        
        textract = boto3.client('textract')
        comprehend = boto3.client('comprehend')
        
        # Process user's documents
        processed_docs = []
        for doc in state.get("documents", []):
            # Extract text with Textract
            text_response = textract.detect_document_text(
                Document={'S3Object': {'Bucket': 'lms-docs', 'Name': doc['key']}}
            )
            
            text = " ".join([block['Text'] for block in text_response['Blocks'] 
                           if block['BlockType'] == 'LINE'])
            
            # Analyze with Comprehend
            entities = comprehend.detect_entities(Text=text, LanguageCode='en')
            key_phrases = comprehend.detect_key_phrases(Text=text, LanguageCode='en')
            
            processed_docs.append({
                'text': text,
                'entities': entities['Entities'],
                'key_phrases': key_phrases['KeyPhrases'],
                'source': doc['name']
            })
        
        state["context"] = {"processed_documents": processed_docs}
        state["tools_used"].append("document_processor")
        return state
    
    async def retrieve_context(self, state: LMSAgentState) -> LMSAgentState:
        """Retrieve context using Bedrock Knowledge Base"""
        
        from langchain.retrievers import AmazonKnowledgeBasesRetriever
        
        retriever = AmazonKnowledgeBasesRetriever(
            knowledge_base_id="your-kb-id",
            retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 5}}
        )
        
        user_query = state["messages"][-1].content
        
        # Retrieve relevant documents
        docs = await retriever.aget_relevant_documents(user_query)
        
        context_docs = [
            {
                'content': doc.page_content,
                'source': doc.metadata.get('source'),
                'score': doc.metadata.get('score', 0)
            }
            for doc in docs
        ]
        
        state["context"] = {"retrieved_documents": context_docs}
        state["tools_used"].append("knowledge_base_retrieval")
        return state
```

## Deploying LangGraph Agent on Bedrock AgentCore

### 1. Package LangGraph Agent for AgentCore
```python
import json
from langgraph.graph import StateGraph
from langchain_aws import BedrockLLM

class BedrockLangGraphDeployer:
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.lms_agent = LMSLangGraphAgent()
    
    def create_agent_package(self):
        """Package LangGraph agent for Bedrock deployment"""
        
        # Create agent configuration
        agent_config = {
            'agentName': 'lms-langgraph-assistant',
            'description': 'LangGraph-powered Learning Management System Assistant',
            'foundationModel': 'amazon.nova-micro-v1:0',
            'instruction': '''
            You are an AI Learning Assistant powered by LangGraph workflows.
            Your capabilities include:
            1. Intent-based routing for different learning tasks
            2. Document analysis and summarization using AWS Textract
            3. RAG-based question answering with Bedrock Knowledge Base
            4. Quiz generation from learning content
            5. Learning analytics and progress tracking
            
            Use the LangGraph workflow to process requests efficiently.
            Always provide helpful, accurate, and educational responses.
            ''',
            'idleSessionTTLInSeconds': 1800,
            'agentResourceRoleArn': 'arn:aws:iam::ACCOUNT:role/BedrockLangGraphAgentRole'
        }
        
        # Create agent
        response = self.bedrock_agent.create_agent(**agent_config)
        agent_id = response['agent']['agentId']
        
        return agent_id
    
    def add_langgraph_action_group(self, agent_id):
        """Add LangGraph workflow as action group"""
        
        langgraph_action_group = {
            'agentId': agent_id,
            'agentVersion': 'DRAFT',
            'actionGroupName': 'LangGraphWorkflow',
            'description': 'LangGraph-powered workflow execution',
            'actionGroupExecutor': {
                'lambda': 'arn:aws:lambda:region:account:function:lms-langgraph-executor'
            },
            'apiSchema': {
                'payload': json.dumps({
                    "openapi": "3.0.0",
                    "info": {"title": "LangGraph Workflow", "version": "1.0.0"},
                    "paths": {
                        "/execute-workflow": {
                            "post": {
                                "description": "Execute LangGraph workflow for user request",
                                "requestBody": {
                                    "required": True,
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "user_input": {"type": "string"},
                                                    "user_id": {"type": "string"},
                                                    "session_id": {"type": "string"},
                                                    "documents": {"type": "array"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                })
            }
        }
        
        self.bedrock_agent.create_agent_action_group(**langgraph_action_group)

def invoke_agent(self, agent_id, alias_id, user_input, session_id):
    """Invoke deployed agent"""
    
    response = self.bedrock_runtime.invoke_agent(
        agentId=agent_id,
        agentAliasId=alias_id,
        sessionId=session_id,
        inputText=user_input
    )
    
    # Process streaming response
    completion = ""
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            if 'bytes' in chunk:
                completion += chunk['bytes'].decode('utf-8')
    
    return completion
```

#### 2. Lambda Executor for LangGraph Workflow
```python
import json
import boto3
from langgraph.graph import StateGraph
from langchain.memory import DynamoDBChatMessageHistory

def lambda_handler(event, context):
    """Lambda function to execute LangGraph workflow"""
    
    try:
        # Parse the action group request
        body = json.loads(event['body'])
        user_input = body['user_input']
        user_id = body['user_id']
        session_id = body.get('session_id', f"session_{user_id}")
        documents = body.get('documents', [])
        
        # Initialize LangGraph agent
        lms_agent = LMSLangGraphAgent()
        
        # Initialize memory
        memory = DynamoDBChatMessageHistory(
            table_name="lms-chat-memory",
            session_id=session_id
        )
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_id": user_id,
            "documents": documents,
            "intent": "",
            "tools_used": [],
            "context": {},
            "final_response": ""
        }
        
        # Execute LangGraph workflow
        result = await lms_agent.agent_executor.ainvoke(initial_state)
        
        # Store conversation in memory
        memory.add_user_message(user_input)
        memory.add_ai_message(result["final_response"])
        
        # Return response in Bedrock action group format
        return {
            'statusCode': 200,
            'body': json.dumps({
                'response': result["final_response"],
                'tools_used': result["tools_used"],
                'session_id': session_id,
                'workflow_state': {
                    'intent': result["intent"],
                    'context_summary': str(result["context"])[:500]
                }
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"LangGraph workflow execution failed: {str(e)}"
            })
        }

# Additional workflow nodes
async def create_quiz(self, state: LMSAgentState) -> LMSAgentState:
    """Generate quiz using LLM"""
    
    context = state.get("context", {})
    user_message = state["messages"][-1].content
    
    quiz_prompt = f"""
    Based on the user request: "{user_message}"
    
    Context: {context}
    
    Generate a quiz with 5 multiple-choice questions.
    Format as JSON with questions, options, and correct answers.
    """
    
    quiz_response = await self.llm.ainvoke(quiz_prompt)
    
    state["final_response"] = quiz_response.content
    state["tools_used"].append("quiz_generator")
    return state

async def track_analytics(self, state: LMSAgentState) -> LMSAgentState:
    """Track learning analytics"""
    
    import boto3
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('lms-analytics')
    
    user_id = state["user_id"]
    
    # Get user analytics
    response = table.get_item(Key={'user_id': user_id})
    analytics = response.get('Item', {})
    
    analytics_summary = f"""
    Learning Progress for User {user_id}:
    - Documents processed: {analytics.get('documents_processed', 0)}
    - Quizzes taken: {analytics.get('quizzes_taken', 0)}
    - Average score: {analytics.get('average_score', 0)}%
    - Study time: {analytics.get('study_time_hours', 0)} hours
    """
    
    state["final_response"] = analytics_summary
    state["tools_used"].append("analytics_tracker")
    return state
```

#### 3. Bedrock Flows Integration
```python
def create_agent_flow(self):
    """Create Bedrock Flow for complex workflows"""
    
    flow_definition = {
        "nodes": [
            {
                "name": "InputNode",
                "type": "Input",
                "configuration": {
                    "input": {
                        "expression": "$.input"
                    }
                }
            },
            {
                "name": "IntentClassification",
                "type": "LLMNode",
                "configuration": {
                    "llm": {
                        "modelId": "amazon.nova-micro-v1:0"
                    },
                    "prompt": {
                        "template": "Classify the user intent: {{input}}. Categories: summarize, question, quiz, translate"
                    }
                }
            },
            {
                "name": "DocumentProcessor",
                "type": "ConditionNode",
                "configuration": {
                    "conditions": [
                        {
                            "name": "IsSummarize",
                            "expression": "$.IntentClassification.output contains 'summarize'"
                        }
                    ]
                }
            },
            {
                "name": "RAGRetrieval",
                "type": "RetrievalNode",
                "configuration": {
                    "knowledgeBase": {
                        "knowledgeBaseId": "KB_ID_HERE"
                    }
                }
            },
            {
                "name": "OutputNode",
                "type": "Output",
                "configuration": {
                    "output": {
                        "expression": "$.RAGRetrieval.output"
                    }
                }
            }
        ],
        "connections": [
            {
                "name": "InputToIntent",
                "source": "InputNode",
                "target": "IntentClassification"
            },
            {
                "name": "IntentToProcessor",
                "source": "IntentClassification",
                "target": "DocumentProcessor"
            },
            {
                "name": "ProcessorToRAG",
                "source": "DocumentProcessor",
                "target": "RAGRetrieval"
            },
            {
                "name": "RAGToOutput",
                "source": "RAGRetrieval",
                "target": "OutputNode"
            }
        ]
    }
    
    flow_response = self.bedrock_agent.create_flow(
        name='lms-agent-flow',
        description='LMS agent workflow with conditional routing',
        definition=flow_definition,
        executionRoleArn='arn:aws:iam::ACCOUNT:role/BedrockFlowRole'
    )
    
    return flow_response['id']
```

### LangGraph Workflow Nodes

#### Intent Detection Node
```python
async def detect_user_intent(state: AgentState) -> AgentState:
    """Use Comprehend to detect user intent"""
    
    user_message = state["messages"][-1].content
    
    # Use Comprehend for intent classification
    comprehend = boto3.client('comprehend')
    
    # Detect key phrases to understand intent
    key_phrases = comprehend.detect_key_phrases(
        Text=user_message, 
        LanguageCode='en'
    )
    
    # Simple intent mapping based on key phrases
    intent_keywords = {
        'summarize': ['summary', 'summarize', 'key points', 'overview'],
        'question': ['what', 'how', 'why', 'explain', 'tell me'],
        'quiz': ['quiz', 'test', 'questions', 'assessment'],
        'translate': ['translate', 'translation', 'language']
    }
    
    detected_intent = "question"  # default
    for intent, keywords in intent_keywords.items():
        if any(keyword in user_message.lower() for keyword in keywords):
            detected_intent = intent
            break
    
    state["intent"] = detected_intent
    return state
```

#### Conditional Routing
```python
def route_based_on_intent(state: AgentState) -> str:
    """Route to appropriate processing node based on intent"""
    
    intent = state["intent"]
    
    if intent == "summarize":
        return "document_processing"
    elif intent == "question":
        return "rag_retrieval"
    elif intent == "quiz":
        return "quiz_generation"
    elif intent == "translate":
        return "translation"
    else:
        return "rag_retrieval"  # default
```

## Agent Testing and Validation

### 1. Bedrock Console Testing
```python
import boto3
import json

class AgentTester:
    def __init__(self):
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
        self.agent_id = 'YOUR_AGENT_ID'
        self.alias_id = 'production'
    
    def test_agent_capabilities(self):
        """Test various agent capabilities"""
        
        test_cases = [
            {
                'name': 'Document Summarization',
                'input': 'Summarize the uploaded machine learning document',
                'expected_tools': ['document_processor']
            },
            {
                'name': 'Quiz Generation',
                'input': 'Create a 5-question quiz about neural networks',
                'expected_tools': ['quiz_generator']
            },
            {
                'name': 'Knowledge Retrieval',
                'input': 'What is backpropagation in neural networks?',
                'expected_tools': ['knowledge_base_retrieval']
            },
            {
                'name': 'Learning Analytics',
                'input': 'Show my learning progress for this week',
                'expected_tools': ['analytics_tracker']
            }
        ]
        
        results = []
        for test in test_cases:
            try:
                response = self.bedrock_runtime.invoke_agent(
                    agentId=self.agent_id,
                    agentAliasId=self.alias_id,
                    sessionId=f"test-{test['name'].lower().replace(' ', '-')}",
                    inputText=test['input']
                )
                
                # Process response
                completion = ""
                for event in response['completion']:
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            completion += chunk['bytes'].decode('utf-8')
                
                results.append({
                    'test': test['name'],
                    'status': 'PASSED',
                    'response': completion[:200] + '...',
                    'tools_used': self._extract_tools_used(response)
                })
                
            except Exception as e:
                results.append({
                    'test': test['name'],
                    'status': 'FAILED',
                    'error': str(e)
                })
        
        return results
    
    def _extract_tools_used(self, response):
        """Extract which tools were used from agent response"""
        # Implementation depends on response format
        return []

# Usage
tester = AgentTester()
test_results = tester.test_agent_capabilities()
for result in test_results:
    print(f"Test: {result['test']} - Status: {result['status']}")
```

### 2. API Gateway Integration (Optional)
```python
import json
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """API Gateway Lambda proxy for external agent access"""
    
    try:
        # Parse request
        body = json.loads(event['body'])
        user_id = event['requestContext']['authorizer']['user_id']
        message = body['message']
        session_id = body.get('session_id', f"session_{user_id}")
        
        # Initialize Bedrock Agent Runtime
        bedrock_runtime = boto3.client('bedrock-agent-runtime')
        
        # Invoke agent
        response = bedrock_runtime.invoke_agent(
            agentId=os.environ['AGENT_ID'],
            agentAliasId='production',
            sessionId=session_id,
            inputText=message
        )
        
        # Process streaming response
        completion = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    completion += chunk['bytes'].decode('utf-8')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'response': completion,
                'session_id': session_id,
                'agent_id': os.environ['AGENT_ID']
            })
        }
        
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
```

### 2. Multi-Language Support
```python
async def translation_node(state: AgentState) -> AgentState:
    """Handle translation requests using Amazon Translate"""
    
    translate = boto3.client('translate')
    user_message = state["messages"][-1].content
    
    # Detect source language
    comprehend = boto3.client('comprehend')
    language_detection = comprehend.detect_dominant_language(Text=user_message)
    source_language = language_detection['Languages'][0]['LanguageCode']
    
    # Translate if needed
    if source_language != 'en':
        translation = translate.translate_text(
            Text=user_message,
            SourceLanguageCode=source_language,
            TargetLanguageCode='en'
        )
        translated_message = translation['TranslatedText']
        
        # Update state with translated message
        state["messages"].append(AIMessage(content=f"Translated: {translated_message}"))
    
    return state
```

## Key Benefits

1. **Best of Both Worlds**: LangGraph flexibility + Bedrock AgentCore reliability
2. **Graph-Based Logic**: Complex conditional workflows with LangGraph
3. **Managed Infrastructure**: No server management, auto-scaling, monitoring
4. **AWS Native Integration**: Seamless Textract, Comprehend, Knowledge Base access
5. **Version Control**: Built-in agent versioning and alias management
6. **Cost Effective**: Pay-per-request with optimized LangGraph execution
7. **Production Ready**: Enterprise-grade security and compliance

## Implementation Priority

1. **Build LangGraph workflow with intent detection and routing**
2. **Create Lambda executor for LangGraph agent**
3. **Deploy Bedrock Agent with LangGraph action group**
4. **Set up Knowledge Base with S3 data source**
5. **Test agent workflows via Bedrock console**
6. **Create production alias for stable deployment**
7. **Add monitoring and analytics tracking**
8. **Optimize performance and cost**

## Deployment Architecture

```
External Systems (Optional)
    ↓ HTTPS/API
API Gateway (Optional)
    ↓ Lambda Proxy
Bedrock Agent (AgentCore) - Production Alias
    ↓ Action Group Call
Lambda Function (LangGraph Executor)
    ↓ Workflow Execution
LangGraph Agent (Intent → Route → Process → Respond)
    ↓ Native AWS Services
Knowledge Base + S3 + DynamoDB + Textract + Comprehend
```

Remember: We're combining LangGraph's workflow power with Bedrock's managed infrastructure!