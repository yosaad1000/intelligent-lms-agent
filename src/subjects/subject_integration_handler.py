"""
Subject and Assignment Integration Handler
Implements subject-specific AI chat, file management, and assignment workflows
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
from supabase import create_client

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Initialize Supabase client (read-only for existing data)
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_ANON_KEY')
)

def lambda_response(status_code: int, body: Dict[Any, Any]) -> Dict[str, Any]:
    """Helper function to create Lambda response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        },
        'body': json.dumps(body)
    }

def subject_chat_handler(event, context):
    """Lambda handler for subject-specific AI chat"""
    
    try:
        # Parse request
        body = json.loads(event['body'])
        user_id = event['requestContext']['authorizer']['user_id']
        user_role = event['requestContext']['authorizer']['role']
        subject_id = event['pathParameters']['subject_id']
        
        message = body['message']
        conversation_id = body.get('conversation_id')
        
        # Initialize subject chat service
        chat_service = SubjectChatService()
        
        # Process subject-specific chat
        response = chat_service.process_subject_chat(
            user_id=user_id,
            user_role=user_role,
            subject_id=subject_id,
            message=message,
            conversation_id=conversation_id
        )
        
        return lambda_response(200, response)
        
    except Exception as e:
        return lambda_response(500, {'error': str(e)})

def subject_files_handler(event, context):
    """Lambda handler for subject-specific file management"""
    
    try:
        user_id = event['requestContext']['authorizer']['user_id']
        user_role = event['requestContext']['authorizer']['role']
        subject_id = event['pathParameters']['subject_id']
        
        # Initialize file management service
        file_service = SubjectFileService()
        
        if event['httpMethod'] == 'GET':
            # Get subject-specific files
            files = file_service.get_subject_files(user_id, subject_id, user_role)
            return lambda_response(200, {'files': files})
            
        elif event['httpMethod'] == 'POST':
            # Upload file to subject
            body = json.loads(event['body'])
            file_key = body['file_key']
            file_name = body['file_name']
            assignment_id = body.get('assignment_id')
            
            result = file_service.process_subject_file(
                user_id=user_id,
                subject_id=subject_id,
                file_key=file_key,
                file_name=file_name,
                assignment_id=assignment_id
            )
            
            return lambda_response(200, result)
            
    except Exception as e:
        return lambda_response(500, {'error': str(e)})

def assignment_quiz_handler(event, context):
    """Lambda handler for assignment-based quiz generation"""
    
    try:
        user_id = event['requestContext']['authorizer']['user_id']
        user_role = event['requestContext']['authorizer']['role']
        
        # Only teachers can generate assignment quizzes
        if user_role != 'teacher':
            return lambda_response(403, {'error': 'Only teachers can generate assignment quizzes'})
        
        body = json.loads(event['body'])
        assignment_id = body['assignment_id']
        quiz_config = body.get('quiz_config', {})
        
        # Initialize assignment quiz service
        quiz_service = AssignmentQuizService()
        
        # Generate quiz for assignment
        quiz = quiz_service.generate_assignment_quiz(
            teacher_id=user_id,
            assignment_id=assignment_id,
            quiz_config=quiz_config
        )
        
        return lambda_response(200, quiz)
        
    except Exception as e:
        return lambda_response(500, {'error': str(e)})

def teacher_dashboard_handler(event, context):
    """Lambda handler for teacher dashboard with AI-enhanced analytics"""
    
    try:
        user_id = event['requestContext']['authorizer']['user_id']
        user_role = event['requestContext']['authorizer']['role']
        
        # Only teachers can access dashboard
        if user_role != 'teacher':
            return lambda_response(403, {'error': 'Only teachers can access dashboard'})
        
        subject_id = event['pathParameters'].get('subject_id')
        
        # Initialize dashboard service
        dashboard_service = TeacherDashboardService()
        
        if event['httpMethod'] == 'GET':
            # Get dashboard data
            dashboard_data = dashboard_service.get_dashboard_data(user_id, subject_id)
            return lambda_response(200, dashboard_data)
            
    except Exception as e:
        return lambda_response(500, {'error': str(e)})

def student_progress_handler(event, context):
    """Lambda handler for student progress summaries per subject"""
    
    try:
        user_id = event['requestContext']['authorizer']['user_id']
        user_role = event['requestContext']['authorizer']['role']
        subject_id = event['pathParameters']['subject_id']
        
        # Initialize progress service
        progress_service = StudentProgressService()
        
        if user_role == 'student':
            # Get own progress
            progress = progress_service.get_student_progress(user_id, subject_id)
        elif user_role == 'teacher':
            # Get all students' progress for subject
            student_id = event['queryStringParameters'].get('student_id')
            if student_id:
                progress = progress_service.get_student_progress(student_id, subject_id)
            else:
                progress = progress_service.get_subject_progress_summary(user_id, subject_id)
        else:
            return lambda_response(403, {'error': 'Unauthorized'})
        
        return lambda_response(200, progress)
        
    except Exception as e:
        return lambda_response(500, {'error': str(e)})

class SubjectChatService:
    """Service for subject-specific AI chat functionality"""
    
    def __init__(self):
        self.chat_table = dynamodb.Table('lms-chat-history')
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
        self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
    
    def process_subject_chat(self, user_id: str, user_role: str, subject_id: str, 
                           message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """Process chat message within subject context"""
        
        # Get or create subject-specific conversation
        if not conversation_id:
            conversation_id = f"subj_{subject_id}_{user_id}_{datetime.now().strftime('%Y%m%d')}"
        
        # Get subject context for AI
        subject_context = self._get_subject_context(subject_id)
        
        # Get user's subject-specific learning profile
        user_profile = self._get_subject_user_profile(user_id, subject_id)
        
        # Prepare enhanced message with subject context
        enhanced_message = self._build_subject_aware_message(
            message, subject_context, user_profile, user_role
        )
        
        # Call Bedrock Agent with subject context
        agent_response = self._call_bedrock_agent(
            message=enhanced_message,
            session_id=conversation_id,
            user_context={
                'user_id': user_id,
                'subject_id': subject_id,
                'user_role': user_role,
                'subject_context': subject_context
            }
        )
        
        # Store conversation in DynamoDB
        self._store_subject_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            subject_id=subject_id,
            message=message,
            response=agent_response['response'],
            metadata={
                'user_role': user_role,
                'subject_name': subject_context.get('subject_name', 'Unknown'),
                'tools_used': agent_response.get('tools_used', [])
            }
        )
        
        return {
            'conversation_id': conversation_id,
            'response': agent_response['response'],
            'subject_context': {
                'subject_name': subject_context.get('subject_name'),
                'recent_topics': subject_context.get('recent_topics', [])
            },
            'citations': agent_response.get('citations', [])
        }
    
    def _get_subject_context(self, subject_id: str) -> Dict[str, Any]:
        """Get comprehensive subject context for AI interactions"""
        
        try:
            # Get subject info from Supabase (read-only)
            subject_response = supabase.table('subjects').select('*').eq('subject_id', subject_id).execute()
            
            if not subject_response.data:
                return {'subject_name': 'Unknown Subject'}
            
            subject = subject_response.data[0]
            
            # Get recent sessions for context
            sessions_response = supabase.table('sessions').select('*').eq('subject_id', subject_id).order('session_date', desc=True).limit(5).execute()
            
            # Get recent assignments
            assignments_response = supabase.table('assignments').select('*').eq('subject_id', subject_id).order('created_at', desc=True).limit(3).execute()
            
            return {
                'subject_id': subject_id,
                'subject_name': subject.get('name', 'Unknown Subject'),
                'description': subject.get('description', ''),
                'recent_sessions': [
                    {
                        'session_id': s['session_id'],
                        'title': s.get('title', ''),
                        'date': s.get('session_date', ''),
                        'topics': s.get('topics', [])
                    }
                    for s in sessions_response.data
                ],
                'recent_assignments': [
                    {
                        'assignment_id': a['assignment_id'],
                        'title': a.get('title', ''),
                        'due_date': a.get('due_date', ''),
                        'type': a.get('assignment_type', '')
                    }
                    for a in assignments_response.data
                ],
                'recent_topics': self._extract_recent_topics(sessions_response.data)
            }
            
        except Exception as e:
            print(f"Error getting subject context: {e}")
            return {'subject_name': 'Unknown Subject'}
    
    def _get_subject_user_profile(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Get user's learning profile specific to this subject"""
        
        try:
            # Get user's interactions in this subject from DynamoDB
            response = self.chat_table.query(
                IndexName='user-subject-index',
                KeyConditionExpression='user_id = :user_id AND begins_with(conversation_id, :subject_prefix)',
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':subject_prefix': f'subj_{subject_id}'
                },
                ScanIndexForward=False,
                Limit=20
            )
            
            interactions = response.get('Items', [])
            
            # Analyze interaction patterns
            total_interactions = len(interactions)
            recent_topics = []
            question_types = []
            
            for interaction in interactions:
                if 'metadata' in interaction:
                    metadata = interaction['metadata']
                    if 'topics' in metadata:
                        recent_topics.extend(metadata['topics'])
                    if 'question_type' in metadata:
                        question_types.append(metadata['question_type'])
            
            # Determine learning preferences
            engagement_level = 'high' if total_interactions > 10 else 'medium' if total_interactions > 3 else 'low'
            
            return {
                'total_interactions': total_interactions,
                'engagement_level': engagement_level,
                'recent_topics': list(set(recent_topics))[:5],
                'preferred_question_types': list(set(question_types)),
                'last_interaction': interactions[0]['timestamp'] if interactions else None
            }
            
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return {'engagement_level': 'medium'}
    
    def _build_subject_aware_message(self, message: str, subject_context: Dict[str, Any], 
                                   user_profile: Dict[str, Any], user_role: str) -> str:
        """Build enhanced message with subject context for AI"""
        
        context_prompt = f"""
Subject Context:
- Subject: {subject_context.get('subject_name', 'Unknown')}
- Description: {subject_context.get('description', 'No description available')}
- Recent Topics: {', '.join(subject_context.get('recent_topics', []))}

User Profile:
- Role: {user_role}
- Engagement Level: {user_profile.get('engagement_level', 'medium')}
- Total Interactions: {user_profile.get('total_interactions', 0)}

Recent Sessions:
{self._format_recent_sessions(subject_context.get('recent_sessions', []))}

Recent Assignments:
{self._format_recent_assignments(subject_context.get('recent_assignments', []))}

User Message: {message}

Please provide a helpful response that:
1. Is relevant to the {subject_context.get('subject_name')} subject
2. References recent class topics and assignments when appropriate
3. Adapts to the user's {user_role} role and engagement level
4. Provides educational value and encourages learning
"""
        
        return context_prompt
    
    def _format_recent_sessions(self, sessions: List[Dict[str, Any]]) -> str:
        """Format recent sessions for context"""
        if not sessions:
            return "No recent sessions available"
        
        formatted = []
        for session in sessions:
            topics_str = ', '.join(session.get('topics', []))
            formatted.append(f"- {session.get('title', 'Untitled')} ({session.get('date', 'No date')}): {topics_str}")
        
        return '\n'.join(formatted)
    
    def _format_recent_assignments(self, assignments: List[Dict[str, Any]]) -> str:
        """Format recent assignments for context"""
        if not assignments:
            return "No recent assignments available"
        
        formatted = []
        for assignment in assignments:
            formatted.append(f"- {assignment.get('title', 'Untitled')} (Due: {assignment.get('due_date', 'No due date')}) - {assignment.get('type', 'Unknown type')}")
        
        return '\n'.join(formatted)
    
    def _extract_recent_topics(self, sessions: List[Dict[str, Any]]) -> List[str]:
        """Extract recent topics from sessions"""
        topics = []
        for session in sessions:
            if 'topics' in session and session['topics']:
                topics.extend(session['topics'])
        
        return list(set(topics))[:10]  # Return unique topics, max 10
    
    def _call_bedrock_agent(self, message: str, session_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Call Bedrock Agent with subject-specific context"""
        
        try:
            response = bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=message,
                sessionAttributes={
                    'user_id': user_context['user_id'],
                    'subject_id': user_context['subject_id'],
                    'user_role': user_context['user_role'],
                    'subject_name': user_context['subject_context'].get('subject_name', ''),
                    'context_type': 'subject_specific'
                }
            )
            
            # Process streaming response
            completion = ""
            citations = []
            tools_used = []
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')
                elif 'trace' in event:
                    # Extract citations and tools used from trace
                    trace = event['trace']
                    if 'orchestrationTrace' in trace:
                        orch_trace = trace['orchestrationTrace']
                        if 'invocationInput' in orch_trace:
                            tools_used.append(orch_trace['invocationInput'].get('actionGroupInvocationInput', {}).get('actionGroupName', ''))
            
            return {
                'response': completion,
                'citations': citations,
                'tools_used': tools_used
            }
            
        except Exception as e:
            print(f"Error calling Bedrock Agent: {e}")
            return {
                'response': f"I apologize, but I encountered an error processing your request about {user_context['subject_context'].get('subject_name', 'this subject')}. Please try again.",
                'citations': [],
                'tools_used': []
            }
    
    def _store_subject_conversation(self, conversation_id: str, user_id: str, subject_id: str,
                                  message: str, response: str, metadata: Dict[str, Any]) -> None:
        """Store subject-specific conversation in DynamoDB"""
        
        try:
            self.chat_table.put_item(Item={
                'conversation_id': conversation_id,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'message': message,
                'response': response,
                'subject_id': subject_id,
                'conversation_type': 'subject',
                'metadata': metadata,
                'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())
            })
        except Exception as e:
            print(f"Error storing conversation: {e}")

class SubjectFileService:
    """Service for subject-specific file management"""
    
    def __init__(self):
        self.files_table = dynamodb.Table('lms-user-files')
        self.s3_bucket = os.getenv('S3_BUCKET_NAME', 'lms-documents')
    
    def get_subject_files(self, user_id: str, subject_id: str, user_role: str) -> List[Dict[str, Any]]:
        """Get files associated with a specific subject"""
        
        try:
            if user_role == 'student':
                # Students see their own files + shared assignment files
                response = self.files_table.scan(
                    FilterExpression='subject_id = :subject_id AND (user_id = :user_id OR file_type = :shared_type)',
                    ExpressionAttributeValues={
                        ':subject_id': subject_id,
                        ':user_id': user_id,
                        ':shared_type': 'assignment_material'
                    }
                )
            else:  # teacher
                # Teachers see all files in their subject
                response = self.files_table.scan(
                    FilterExpression='subject_id = :subject_id',
                    ExpressionAttributeValues={
                        ':subject_id': subject_id
                    }
                )
            
            files = response.get('Items', [])
            
            # Enrich with assignment info if applicable
            for file in files:
                if file.get('assignment_id'):
                    assignment_info = self._get_assignment_info(file['assignment_id'])
                    file['assignment_info'] = assignment_info
            
            return files
            
        except Exception as e:
            print(f"Error getting subject files: {e}")
            return []
    
    def process_subject_file(self, user_id: str, subject_id: str, file_key: str, 
                           file_name: str, assignment_id: Optional[str] = None) -> Dict[str, Any]:
        """Process and store a file within subject context"""
        
        file_id = str(uuid.uuid4())
        
        try:
            # Extract text content from S3
            text_content = self._extract_text_from_s3(file_key)
            
            # Get subject context for enhanced processing
            subject_context = self._get_subject_context(subject_id)
            
            # Process file with subject-aware context
            processed_content = self._process_with_subject_context(
                text_content, subject_context, assignment_id
            )
            
            # Store file metadata with subject association
            file_metadata = {
                'file_id': file_id,
                'user_id': user_id,
                'subject_id': subject_id,
                'assignment_id': assignment_id,
                'filename': file_name,
                's3_key': file_key,
                'file_type': 'assignment_material' if assignment_id else 'subject_material',
                'subject_name': subject_context.get('subject_name', 'Unknown'),
                'processed_content': processed_content,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'ttl': int((datetime.utcnow() + timedelta(days=365)).timestamp())
            }
            
            self.files_table.put_item(Item=file_metadata)
            
            # If this is assignment material, notify enrolled students
            if assignment_id:
                self._notify_assignment_file_upload(subject_id, assignment_id, file_metadata)
            
            return {
                'file_id': file_id,
                'status': 'processed',
                'subject_context': subject_context,
                'processed_content': processed_content
            }
            
        except Exception as e:
            print(f"Error processing subject file: {e}")
            return {'error': str(e)}
    
    def _get_subject_context(self, subject_id: str) -> Dict[str, Any]:
        """Get subject context for file processing"""
        try:
            subject_response = supabase.table('subjects').select('*').eq('subject_id', subject_id).execute()
            if subject_response.data:
                return {
                    'subject_id': subject_id,
                    'subject_name': subject_response.data[0].get('name', 'Unknown'),
                    'description': subject_response.data[0].get('description', '')
                }
        except Exception as e:
            print(f"Error getting subject context: {e}")
        
        return {'subject_id': subject_id, 'subject_name': 'Unknown'}
    
    def _extract_text_from_s3(self, s3_key: str) -> str:
        """Extract text content from S3 file"""
        try:
            # Get file from S3
            response = s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            file_content = response['Body'].read()
            
            # Simple text extraction (could be enhanced with Textract)
            if s3_key.lower().endswith('.txt'):
                return file_content.decode('utf-8')
            else:
                # For PDF/DOCX, return placeholder (would use Textract in production)
                return f"Content extracted from {s3_key}"
                
        except Exception as e:
            print(f"Error extracting text from S3: {e}")
            return ""
    
    def _process_with_subject_context(self, text_content: str, subject_context: Dict[str, Any], 
                                    assignment_id: Optional[str] = None) -> Dict[str, Any]:
        """Process file content with subject-specific context"""
        
        # Extract key concepts relevant to the subject
        key_concepts = self._extract_subject_concepts(text_content, subject_context)
        
        # Generate summary with subject focus
        summary = self._generate_subject_summary(text_content, subject_context)
        
        return {
            'summary': summary,
            'key_concepts': key_concepts,
            'subject_relevance': self._assess_subject_relevance(text_content, subject_context),
            'assignment_context': assignment_id is not None,
            'content_preview': text_content[:500] if text_content else ""
        }
    
    def _extract_subject_concepts(self, text_content: str, subject_context: Dict[str, Any]) -> List[str]:
        """Extract key concepts relevant to the subject"""
        # Simple keyword extraction (could be enhanced with Comprehend)
        subject_name = subject_context.get('subject_name', '').lower()
        
        # Basic concept extraction based on subject
        concepts = []
        if 'physics' in subject_name:
            physics_terms = ['force', 'energy', 'momentum', 'velocity', 'acceleration', 'gravity']
            concepts = [term for term in physics_terms if term in text_content.lower()]
        elif 'math' in subject_name:
            math_terms = ['equation', 'function', 'derivative', 'integral', 'theorem', 'proof']
            concepts = [term for term in math_terms if term in text_content.lower()]
        
        return concepts[:10]  # Return top 10 concepts
    
    def _generate_subject_summary(self, text_content: str, subject_context: Dict[str, Any]) -> str:
        """Generate a summary focused on the subject"""
        if not text_content:
            return "No content available for summary"
        
        # Simple summary (could be enhanced with Bedrock)
        subject_name = subject_context.get('subject_name', 'Unknown Subject')
        return f"Document related to {subject_name}: {text_content[:200]}..."
    
    def _assess_subject_relevance(self, text_content: str, subject_context: Dict[str, Any]) -> float:
        """Assess how relevant the content is to the subject"""
        # Simple relevance scoring (could be enhanced with ML)
        subject_name = subject_context.get('subject_name', '').lower()
        
        if subject_name in text_content.lower():
            return 0.9
        elif any(word in text_content.lower() for word in subject_name.split()):
            return 0.7
        else:
            return 0.5
    
    def _get_assignment_info(self, assignment_id: str) -> Dict[str, Any]:
        """Get assignment information from Supabase"""
        try:
            response = supabase.table('assignments').select('*').eq('assignment_id', assignment_id).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Error getting assignment info: {e}")
        
        return {}
    
    def _notify_assignment_file_upload(self, subject_id: str, assignment_id: str, file_metadata: Dict[str, Any]) -> None:
        """Notify enrolled students about new assignment file"""
        try:
            # Get enrolled students
            enrollments = supabase.table('subject_enrollments').select('student_id').eq('subject_id', subject_id).execute()
            
            # Store notification in DynamoDB (simple notification system)
            notifications_table = dynamodb.Table('lms-notifications')
            
            for enrollment in enrollments.data:
                student_id = enrollment['student_id']
                notification_id = str(uuid.uuid4())
                
                notifications_table.put_item(Item={
                    'notification_id': notification_id,
                    'user_id': student_id,
                    'type': 'assignment_file_uploaded',
                    'title': f"New file uploaded for assignment",
                    'message': f"A new file '{file_metadata['filename']}' has been uploaded for your assignment.",
                    'assignment_id': assignment_id,
                    'file_id': file_metadata['file_id'],
                    'created_at': datetime.utcnow().isoformat(),
                    'read': False,
                    'ttl': int((datetime.utcnow() + timedelta(days=30)).timestamp())
                })
                
        except Exception as e:
            print(f"Error notifying students: {e}")