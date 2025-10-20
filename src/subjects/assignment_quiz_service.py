"""
Assignment-based Quiz Generation Service
Implements AI-powered quiz generation for teachers based on assignments and subject content
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
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
comprehend = boto3.client('comprehend')

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_ANON_KEY')
)

class AssignmentQuizService:
    """Service for generating quizzes based on assignments and subject content"""
    
    def __init__(self):
        self.quizzes_table = dynamodb.Table('lms-quizzes')
        self.files_table = dynamodb.Table('lms-user-files')
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
        self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
    
    def generate_assignment_quiz(self, teacher_id: str, assignment_id: str, 
                               quiz_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a quiz based on assignment content and requirements"""
        
        try:
            # Get assignment details
            assignment = self._get_assignment_details(assignment_id)
            if not assignment:
                raise ValueError("Assignment not found")
            
            # Verify teacher has permission for this assignment
            if not self._verify_teacher_permission(teacher_id, assignment['subject_id']):
                raise ValueError("Teacher does not have permission for this subject")
            
            # Get assignment-related content
            assignment_content = self._get_assignment_content(assignment_id, assignment['subject_id'])
            
            # Get subject context for quiz generation
            subject_context = self._get_subject_context(assignment['subject_id'])
            
            # Generate quiz using AI
            quiz_data = self._generate_quiz_with_ai(
                assignment=assignment,
                content=assignment_content,
                subject_context=subject_context,
                config=quiz_config
            )
            
            # Store quiz in database
            quiz_id = self._store_quiz(
                teacher_id=teacher_id,
                assignment_id=assignment_id,
                subject_id=assignment['subject_id'],
                quiz_data=quiz_data,
                config=quiz_config
            )
            
            # Notify enrolled students about new quiz
            self._notify_students_about_quiz(assignment['subject_id'], quiz_id, assignment)
            
            return {
                'quiz_id': quiz_id,
                'assignment_id': assignment_id,
                'subject_id': assignment['subject_id'],
                'quiz_data': quiz_data,
                'status': 'generated',
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating assignment quiz: {e}")
            raise
    
    def get_assignment_quizzes(self, teacher_id: str, assignment_id: Optional[str] = None, 
                             subject_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get quizzes for assignments"""
        
        try:
            if assignment_id:
                # Get specific assignment quiz
                response = self.quizzes_table.query(
                    IndexName='assignment-id-index',
                    KeyConditionExpression='assignment_id = :assignment_id',
                    ExpressionAttributeValues={':assignment_id': assignment_id}
                )
            elif subject_id:
                # Get all quizzes for subject
                response = self.quizzes_table.scan(
                    FilterExpression='subject_id = :subject_id AND teacher_id = :teacher_id',
                    ExpressionAttributeValues={
                        ':subject_id': subject_id,
                        ':teacher_id': teacher_id
                    }
                )
            else:
                # Get all quizzes for teacher
                response = self.quizzes_table.scan(
                    FilterExpression='teacher_id = :teacher_id',
                    ExpressionAttributeValues={':teacher_id': teacher_id}
                )
            
            return response.get('Items', [])
            
        except Exception as e:
            print(f"Error getting assignment quizzes: {e}")
            return []
    
    def update_quiz_settings(self, quiz_id: str, teacher_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update quiz settings (due date, attempts, etc.)"""
        
        try:
            # Verify ownership
            quiz = self.quizzes_table.get_item(Key={'quiz_id': quiz_id})['Item']
            if quiz['teacher_id'] != teacher_id:
                raise ValueError("Unauthorized to modify this quiz")
            
            # Update settings
            update_expression = "SET "
            expression_values = {}
            
            allowed_settings = ['due_date', 'max_attempts', 'time_limit', 'show_correct_answers', 'randomize_questions']
            
            for key, value in settings.items():
                if key in allowed_settings:
                    update_expression += f"{key} = :{key}, "
                    expression_values[f":{key}"] = value
            
            update_expression += "updated_at = :updated_at"
            expression_values[':updated_at'] = datetime.utcnow().isoformat()
            
            self.quizzes_table.update_item(
                Key={'quiz_id': quiz_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values
            )
            
            return {'status': 'updated', 'quiz_id': quiz_id}
            
        except Exception as e:
            print(f"Error updating quiz settings: {e}")
            raise
    
    def _get_assignment_details(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """Get assignment details from Supabase"""
        
        try:
            response = supabase.table('assignments').select('*').eq('assignment_id', assignment_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting assignment details: {e}")
            return None
    
    def _verify_teacher_permission(self, teacher_id: str, subject_id: str) -> bool:
        """Verify teacher has permission to create quizzes for this subject"""
        
        try:
            # Check if teacher is assigned to this subject
            response = supabase.table('subject_teachers').select('*').eq('teacher_id', teacher_id).eq('subject_id', subject_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error verifying teacher permission: {e}")
            return False
    
    def _get_assignment_content(self, assignment_id: str, subject_id: str) -> Dict[str, Any]:
        """Get content related to the assignment for quiz generation"""
        
        try:
            # Get assignment-specific files
            assignment_files = self.files_table.scan(
                FilterExpression='assignment_id = :assignment_id',
                ExpressionAttributeValues={':assignment_id': assignment_id}
            )
            
            # Get subject-related files that could be relevant
            subject_files = self.files_table.scan(
                FilterExpression='subject_id = :subject_id AND attribute_not_exists(assignment_id)',
                ExpressionAttributeValues={':subject_id': subject_id}
            )
            
            # Combine and process content
            all_files = assignment_files.get('Items', []) + subject_files.get('Items', [])
            
            content_summary = []
            key_concepts = set()
            
            for file in all_files:
                if 'processed_content' in file:
                    processed = file['processed_content']
                    if 'summary' in processed:
                        content_summary.append(processed['summary'])
                    if 'key_concepts' in processed:
                        key_concepts.update(processed['key_concepts'])
            
            return {
                'content_summaries': content_summary,
                'key_concepts': list(key_concepts),
                'total_files': len(all_files),
                'assignment_files': len(assignment_files.get('Items', [])),
                'subject_files': len(subject_files.get('Items', []))
            }
            
        except Exception as e:
            print(f"Error getting assignment content: {e}")
            return {'content_summaries': [], 'key_concepts': []}
    
    def _get_subject_context(self, subject_id: str) -> Dict[str, Any]:
        """Get subject context for quiz generation"""
        
        try:
            # Get subject details
            subject_response = supabase.table('subjects').select('*').eq('subject_id', subject_id).execute()
            subject = subject_response.data[0] if subject_response.data else {}
            
            # Get recent sessions for context
            sessions_response = supabase.table('sessions').select('*').eq('subject_id', subject_id).order('session_date', desc=True).limit(5).execute()
            
            return {
                'subject_name': subject.get('name', 'Unknown Subject'),
                'description': subject.get('description', ''),
                'level': subject.get('level', 'intermediate'),
                'recent_sessions': sessions_response.data,
                'learning_objectives': subject.get('learning_objectives', [])
            }
            
        except Exception as e:
            print(f"Error getting subject context: {e}")
            return {'subject_name': 'Unknown Subject'}
    
    def _generate_quiz_with_ai(self, assignment: Dict[str, Any], content: Dict[str, Any], 
                             subject_context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quiz questions using Bedrock Agent"""
        
        try:
            # Build comprehensive prompt for quiz generation
            quiz_prompt = self._build_quiz_generation_prompt(assignment, content, subject_context, config)
            
            # Call Bedrock Agent for quiz generation
            session_id = f"quiz_gen_{assignment['assignment_id']}_{int(datetime.now().timestamp())}"
            
            response = bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=quiz_prompt,
                sessionAttributes={
                    'task_type': 'quiz_generation',
                    'assignment_id': assignment['assignment_id'],
                    'subject_id': assignment['subject_id'],
                    'subject_name': subject_context.get('subject_name', ''),
                    'quiz_type': config.get('quiz_type', 'multiple_choice')
                }
            )
            
            # Process response
            completion = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')
            
            # Parse AI response into structured quiz data
            quiz_data = self._parse_ai_quiz_response(completion, config)
            
            return quiz_data
            
        except Exception as e:
            print(f"Error generating quiz with AI: {e}")
            # Fallback to basic quiz generation
            return self._generate_fallback_quiz(assignment, content, config)
    
    def _build_quiz_generation_prompt(self, assignment: Dict[str, Any], content: Dict[str, Any], 
                                    subject_context: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Build comprehensive prompt for AI quiz generation"""
        
        num_questions = config.get('num_questions', 5)
        difficulty = config.get('difficulty', 'medium')
        quiz_type = config.get('quiz_type', 'multiple_choice')
        focus_areas = config.get('focus_areas', [])
        
        prompt = f"""
Generate a {quiz_type} quiz for the following assignment:

Assignment Details:
- Title: {assignment.get('title', 'Untitled Assignment')}
- Description: {assignment.get('description', 'No description')}
- Type: {assignment.get('assignment_type', 'general')}
- Due Date: {assignment.get('due_date', 'No due date')}

Subject Context:
- Subject: {subject_context.get('subject_name', 'Unknown')}
- Level: {subject_context.get('level', 'intermediate')}
- Description: {subject_context.get('description', '')}

Content Summary:
{chr(10).join(content.get('content_summaries', ['No content available']))}

Key Concepts to Cover:
{', '.join(content.get('key_concepts', ['General concepts']))}

Quiz Requirements:
- Number of Questions: {num_questions}
- Difficulty Level: {difficulty}
- Question Type: {quiz_type}
- Focus Areas: {', '.join(focus_areas) if focus_areas else 'All relevant topics'}

Please generate {num_questions} {difficulty}-level {quiz_type} questions that:
1. Test understanding of the key concepts from the assignment
2. Are appropriate for the {subject_context.get('level', 'intermediate')} level
3. Include clear, unambiguous questions
4. Have one correct answer and plausible distractors (for multiple choice)
5. Cover different aspects of the material

Format each question as:
Q[number]: [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
Correct Answer: [Letter]
Explanation: [Brief explanation of why this is correct]
Difficulty: {difficulty}
Concept: [Main concept being tested]

Generate the quiz now:
"""
        
        return prompt
    
    def _parse_ai_quiz_response(self, ai_response: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response into structured quiz data"""
        
        try:
            questions = []
            current_question = {}
            
            lines = ai_response.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('Q') and ':' in line:
                    # Save previous question if exists
                    if current_question:
                        questions.append(current_question)
                    
                    # Start new question
                    current_question = {
                        'question_id': str(uuid.uuid4()),
                        'question_text': line.split(':', 1)[1].strip(),
                        'options': [],
                        'correct_answer': '',
                        'explanation': '',
                        'difficulty': config.get('difficulty', 'medium'),
                        'concept': ''
                    }
                
                elif line.startswith(('A)', 'B)', 'C)', 'D)')):
                    if current_question:
                        option_text = line[2:].strip()
                        current_question['options'].append({
                            'option_id': line[0],
                            'text': option_text
                        })
                
                elif line.startswith('Correct Answer:'):
                    if current_question:
                        current_question['correct_answer'] = line.split(':', 1)[1].strip()
                
                elif line.startswith('Explanation:'):
                    if current_question:
                        current_question['explanation'] = line.split(':', 1)[1].strip()
                
                elif line.startswith('Concept:'):
                    if current_question:
                        current_question['concept'] = line.split(':', 1)[1].strip()
            
            # Add last question
            if current_question:
                questions.append(current_question)
            
            return {
                'questions': questions,
                'total_questions': len(questions),
                'quiz_type': config.get('quiz_type', 'multiple_choice'),
                'difficulty': config.get('difficulty', 'medium'),
                'estimated_time': len(questions) * 2,  # 2 minutes per question
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error parsing AI quiz response: {e}")
            return self._generate_fallback_quiz({}, {}, config)
    
    def _generate_fallback_quiz(self, assignment: Dict[str, Any], content: Dict[str, Any], 
                              config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic fallback quiz if AI generation fails"""
        
        num_questions = config.get('num_questions', 3)
        
        questions = []
        for i in range(num_questions):
            questions.append({
                'question_id': str(uuid.uuid4()),
                'question_text': f"Question {i+1} about the assignment content",
                'options': [
                    {'option_id': 'A', 'text': 'Option A'},
                    {'option_id': 'B', 'text': 'Option B'},
                    {'option_id': 'C', 'text': 'Option C'},
                    {'option_id': 'D', 'text': 'Option D'}
                ],
                'correct_answer': 'A',
                'explanation': 'This is the correct answer.',
                'difficulty': config.get('difficulty', 'medium'),
                'concept': 'General concept'
            })
        
        return {
            'questions': questions,
            'total_questions': len(questions),
            'quiz_type': config.get('quiz_type', 'multiple_choice'),
            'difficulty': config.get('difficulty', 'medium'),
            'estimated_time': len(questions) * 2,
            'generated_at': datetime.utcnow().isoformat(),
            'fallback': True
        }
    
    def _store_quiz(self, teacher_id: str, assignment_id: str, subject_id: str, 
                   quiz_data: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Store generated quiz in DynamoDB"""
        
        quiz_id = str(uuid.uuid4())
        
        try:
            quiz_item = {
                'quiz_id': quiz_id,
                'teacher_id': teacher_id,
                'assignment_id': assignment_id,
                'subject_id': subject_id,
                'quiz_data': quiz_data,
                'config': config,
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'due_date': config.get('due_date'),
                'max_attempts': config.get('max_attempts', 3),
                'time_limit': config.get('time_limit', 30),  # minutes
                'show_correct_answers': config.get('show_correct_answers', True),
                'randomize_questions': config.get('randomize_questions', False),
                'ttl': int((datetime.utcnow() + timedelta(days=180)).timestamp())
            }
            
            self.quizzes_table.put_item(Item=quiz_item)
            
            return quiz_id
            
        except Exception as e:
            print(f"Error storing quiz: {e}")
            raise
    
    def _notify_students_about_quiz(self, subject_id: str, quiz_id: str, assignment: Dict[str, Any]) -> None:
        """Notify enrolled students about new quiz"""
        
        try:
            # Get enrolled students
            enrollments = supabase.table('subject_enrollments').select('student_id').eq('subject_id', subject_id).execute()
            
            # Store notifications
            notifications_table = dynamodb.Table('lms-notifications')
            
            for enrollment in enrollments.data:
                student_id = enrollment['student_id']
                notification_id = str(uuid.uuid4())
                
                notifications_table.put_item(Item={
                    'notification_id': notification_id,
                    'user_id': student_id,
                    'type': 'quiz_available',
                    'title': f"New quiz available for {assignment.get('title', 'assignment')}",
                    'message': f"A new quiz has been created for the assignment '{assignment.get('title', 'Untitled')}'.",
                    'quiz_id': quiz_id,
                    'assignment_id': assignment['assignment_id'],
                    'subject_id': subject_id,
                    'created_at': datetime.utcnow().isoformat(),
                    'read': False,
                    'ttl': int((datetime.utcnow() + timedelta(days=30)).timestamp())
                })
                
        except Exception as e:
            print(f"Error notifying students about quiz: {e}")

class QuizAttemptService:
    """Service for handling student quiz attempts"""
    
    def __init__(self):
        self.attempts_table = dynamodb.Table('lms-quiz-attempts')
        self.quizzes_table = dynamodb.Table('lms-quizzes')
    
    def start_quiz_attempt(self, student_id: str, quiz_id: str) -> Dict[str, Any]:
        """Start a new quiz attempt for a student"""
        
        try:
            # Get quiz details
            quiz = self.quizzes_table.get_item(Key={'quiz_id': quiz_id})['Item']
            
            # Check if student can attempt this quiz
            can_attempt, reason = self._can_student_attempt_quiz(student_id, quiz_id, quiz)
            if not can_attempt:
                raise ValueError(reason)
            
            # Create attempt record
            attempt_id = str(uuid.uuid4())
            
            attempt_item = {
                'attempt_id': attempt_id,
                'student_id': student_id,
                'quiz_id': quiz_id,
                'assignment_id': quiz['assignment_id'],
                'subject_id': quiz['subject_id'],
                'started_at': datetime.utcnow().isoformat(),
                'status': 'in_progress',
                'answers': {},
                'time_limit': quiz.get('time_limit', 30),
                'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())
            }
            
            self.attempts_table.put_item(Item=attempt_item)
            
            # Return quiz questions (randomized if configured)
            questions = self._prepare_quiz_questions(quiz, quiz.get('randomize_questions', False))
            
            return {
                'attempt_id': attempt_id,
                'quiz_id': quiz_id,
                'questions': questions,
                'time_limit': quiz.get('time_limit', 30),
                'total_questions': len(questions),
                'started_at': attempt_item['started_at']
            }
            
        except Exception as e:
            print(f"Error starting quiz attempt: {e}")
            raise
    
    def submit_quiz_attempt(self, attempt_id: str, student_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
        """Submit and score a quiz attempt"""
        
        try:
            # Get attempt record
            attempt = self.attempts_table.get_item(Key={'attempt_id': attempt_id})['Item']
            
            # Verify ownership
            if attempt['student_id'] != student_id:
                raise ValueError("Unauthorized to submit this attempt")
            
            # Check if attempt is still valid
            if attempt['status'] != 'in_progress':
                raise ValueError("Attempt is no longer active")
            
            # Get quiz for scoring
            quiz = self.quizzes_table.get_item(Key={'quiz_id': attempt['quiz_id']})['Item']
            
            # Score the attempt
            score_result = self._score_quiz_attempt(quiz, answers)
            
            # Update attempt record
            self.attempts_table.update_item(
                Key={'attempt_id': attempt_id},
                UpdateExpression='SET answers = :answers, score = :score, max_score = :max_score, submitted_at = :submitted_at, status = :status',
                ExpressionAttributeValues={
                    ':answers': answers,
                    ':score': score_result['score'],
                    ':max_score': score_result['max_score'],
                    ':submitted_at': datetime.utcnow().isoformat(),
                    ':status': 'completed'
                }
            )
            
            return {
                'attempt_id': attempt_id,
                'score': score_result['score'],
                'max_score': score_result['max_score'],
                'percentage': score_result['percentage'],
                'correct_answers': score_result['correct_count'],
                'total_questions': score_result['total_questions'],
                'feedback': score_result['feedback'],
                'submitted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error submitting quiz attempt: {e}")
            raise
    
    def _can_student_attempt_quiz(self, student_id: str, quiz_id: str, quiz: Dict[str, Any]) -> tuple:
        """Check if student can attempt the quiz"""
        
        try:
            # Check if quiz is active
            if quiz.get('status') != 'active':
                return False, "Quiz is not active"
            
            # Check due date
            if quiz.get('due_date'):
                due_date = datetime.fromisoformat(quiz['due_date'])
                if datetime.utcnow() > due_date:
                    return False, "Quiz due date has passed"
            
            # Check previous attempts
            previous_attempts = self.attempts_table.scan(
                FilterExpression='student_id = :student_id AND quiz_id = :quiz_id',
                ExpressionAttributeValues={
                    ':student_id': student_id,
                    ':quiz_id': quiz_id
                }
            )
            
            max_attempts = quiz.get('max_attempts', 3)
            if len(previous_attempts.get('Items', [])) >= max_attempts:
                return False, f"Maximum attempts ({max_attempts}) exceeded"
            
            return True, "Can attempt quiz"
            
        except Exception as e:
            print(f"Error checking quiz attempt eligibility: {e}")
            return False, "Error checking eligibility"
    
    def _prepare_quiz_questions(self, quiz: Dict[str, Any], randomize: bool = False) -> List[Dict[str, Any]]:
        """Prepare quiz questions for student (optionally randomized)"""
        
        questions = quiz['quiz_data']['questions'].copy()
        
        if randomize:
            import random
            random.shuffle(questions)
        
        # Remove correct answers and explanations from student view
        student_questions = []
        for q in questions:
            student_q = {
                'question_id': q['question_id'],
                'question_text': q['question_text'],
                'options': q['options'].copy()
            }
            
            # Randomize options if configured
            if randomize:
                import random
                random.shuffle(student_q['options'])
            
            student_questions.append(student_q)
        
        return student_questions
    
    def _score_quiz_attempt(self, quiz: Dict[str, Any], answers: Dict[str, str]) -> Dict[str, Any]:
        """Score a quiz attempt"""
        
        questions = quiz['quiz_data']['questions']
        correct_count = 0
        total_questions = len(questions)
        feedback = []
        
        for question in questions:
            question_id = question['question_id']
            correct_answer = question['correct_answer']
            student_answer = answers.get(question_id, '')
            
            is_correct = student_answer.upper() == correct_answer.upper()
            if is_correct:
                correct_count += 1
            
            feedback.append({
                'question_id': question_id,
                'question_text': question['question_text'],
                'student_answer': student_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question.get('explanation', '') if quiz.get('show_correct_answers', True) else ''
            })
        
        percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        return {
            'score': correct_count,
            'max_score': total_questions,
            'percentage': round(percentage, 2),
            'correct_count': correct_count,
            'total_questions': total_questions,
            'feedback': feedback
        }