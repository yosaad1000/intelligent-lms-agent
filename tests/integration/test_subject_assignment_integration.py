"""
Integration Tests for Subject and Assignment Integration
Tests the complete workflows for subject-specific features and assignment management
"""

import pytest
import json
import boto3
import os
from datetime import datetime, timedelta
from moto import mock_dynamodb, mock_s3
from unittest.mock import patch, MagicMock
import sys
import uuid

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from subjects.subject_integration_handler import (
    SubjectChatService, SubjectFileService, 
    subject_chat_handler, subject_files_handler
)
from subjects.assignment_quiz_service import AssignmentQuizService, QuizAttemptService
from subjects.teacher_dashboard_service import TeacherDashboardService
from subjects.student_progress_service import StudentProgressService

class TestSubjectChatIntegration:
    """Test subject-specific AI chat functionality"""
    
    @mock_dynamodb
    @patch('subjects.subject_integration_handler.bedrock_agent_runtime')
    @patch('subjects.subject_integration_handler.supabase')
    def test_subject_chat_workflow(self, mock_supabase, mock_bedrock):
        """Test complete subject chat workflow"""
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create chat history table
        chat_table = dynamodb.create_table(
            TableName='lms-chat-history',
            KeySchema=[{'AttributeName': 'conversation_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'conversation_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Mock Supabase responses
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'subject_id': 'physics_101',
                'name': 'Physics 101',
                'description': 'Introduction to Physics'
            }]
        )
        
        # Mock Bedrock Agent response
        mock_bedrock.invoke_agent.return_value = {
            'completion': [
                {'chunk': {'bytes': b'This is a helpful response about physics concepts.'}}
            ]
        }
        
        # Test subject chat
        chat_service = SubjectChatService()
        
        response = chat_service.process_subject_chat(
            user_id='student_123',
            user_role='student',
            subject_id='physics_101',
            message='Explain Newton\'s first law',
            conversation_id=None
        )
        
        # Verify response structure
        assert 'conversation_id' in response
        assert 'response' in response
        assert 'subject_context' in response
        assert response['subject_context']['subject_name'] == 'Physics 101'
        
        # Verify Bedrock Agent was called
        mock_bedrock.invoke_agent.assert_called_once()
        
        # Verify conversation was stored
        stored_items = chat_table.scan()['Items']
        assert len(stored_items) == 1
        assert stored_items[0]['subject_id'] == 'physics_101'
        assert stored_items[0]['user_id'] == 'student_123'
    
    @mock_dynamodb
    @patch('subjects.subject_integration_handler.supabase')
    def test_subject_chat_handler_lambda(self, mock_supabase):
        """Test subject chat Lambda handler"""
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        dynamodb.create_table(
            TableName='lms-chat-history',
            KeySchema=[{'AttributeName': 'conversation_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'conversation_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Mock Supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'subject_id': 'physics_101', 'name': 'Physics 101'}]
        )
        
        # Create Lambda event
        event = {
            'httpMethod': 'POST',
            'pathParameters': {'subject_id': 'physics_101'},
            'body': json.dumps({
                'message': 'What is gravity?',
                'conversation_id': None
            }),
            'requestContext': {
                'authorizer': {
                    'user_id': 'student_123',
                    'role': 'student'
                }
            }
        }
        
        with patch('subjects.subject_integration_handler.bedrock_agent_runtime') as mock_bedrock:
            mock_bedrock.invoke_agent.return_value = {
                'completion': [{'chunk': {'bytes': b'Gravity is a fundamental force.'}}]
            }
            
            response = subject_chat_handler(event, {})
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert 'conversation_id' in body
        assert 'response' in body

class TestSubjectFileManagement:
    """Test subject-specific file management"""
    
    @mock_dynamodb
    @mock_s3
    @patch('subjects.subject_integration_handler.supabase')
    def test_subject_file_processing(self, mock_supabase):
        """Test subject file processing workflow"""
        
        # Setup AWS resources
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        # Create DynamoDB table
        files_table = dynamodb.create_table(
            TableName='lms-user-files',
            KeySchema=[{'AttributeName': 'file_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'file_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create S3 bucket
        bucket_name = 'lms-documents'
        s3_client.create_bucket(Bucket=bucket_name)
        
        # Upload test file
        test_content = "This is a physics document about Newton's laws."
        s3_client.put_object(
            Bucket=bucket_name,
            Key='test-file.txt',
            Body=test_content
        )
        
        # Mock Supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'subject_id': 'physics_101',
                'name': 'Physics 101',
                'description': 'Introduction to Physics'
            }]
        )
        
        # Test file processing
        file_service = SubjectFileService()
        
        with patch.dict(os.environ, {'S3_BUCKET_NAME': bucket_name}):
            result = file_service.process_subject_file(
                user_id='student_123',
                subject_id='physics_101',
                file_key='test-file.txt',
                file_name='physics_notes.txt',
                assignment_id=None
            )
        
        # Verify result
        assert 'file_id' in result
        assert result['status'] == 'processed'
        assert 'subject_context' in result
        
        # Verify file was stored in DynamoDB
        stored_files = files_table.scan()['Items']
        assert len(stored_files) == 1
        assert stored_files[0]['subject_id'] == 'physics_101'
        assert stored_files[0]['user_id'] == 'student_123'
    
    @mock_dynamodb
    @patch('subjects.subject_integration_handler.supabase')
    def test_get_subject_files(self, mock_supabase):
        """Test retrieving subject-specific files"""
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        files_table = dynamodb.create_table(
            TableName='lms-user-files',
            KeySchema=[{'AttributeName': 'file_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'file_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Add test files
        test_files = [
            {
                'file_id': 'file_1',
                'user_id': 'student_123',
                'subject_id': 'physics_101',
                'filename': 'notes.pdf',
                'file_type': 'subject_material'
            },
            {
                'file_id': 'file_2',
                'user_id': 'teacher_456',
                'subject_id': 'physics_101',
                'filename': 'assignment.pdf',
                'file_type': 'assignment_material',
                'assignment_id': 'assign_1'
            }
        ]
        
        for file_data in test_files:
            files_table.put_item(Item=file_data)
        
        # Test file retrieval for student
        file_service = SubjectFileService()
        student_files = file_service.get_subject_files(
            user_id='student_123',
            subject_id='physics_101',
            user_role='student'
        )
        
        # Student should see their own files + shared assignment files
        assert len(student_files) == 2
        
        # Test file retrieval for teacher
        teacher_files = file_service.get_subject_files(
            user_id='teacher_456',
            subject_id='physics_101',
            user_role='teacher'
        )
        
        # Teacher should see all files in subject
        assert len(teacher_files) == 2

class TestAssignmentQuizGeneration:
    """Test assignment-based quiz generation"""
    
    @mock_dynamodb
    @patch('subjects.assignment_quiz_service.bedrock_agent_runtime')
    @patch('subjects.assignment_quiz_service.supabase')
    def test_assignment_quiz_generation(self, mock_supabase, mock_bedrock):
        """Test complete assignment quiz generation workflow"""
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create tables
        quizzes_table = dynamodb.create_table(
            TableName='lms-quizzes',
            KeySchema=[{'AttributeName': 'quiz_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'quiz_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        files_table = dynamodb.create_table(
            TableName='lms-user-files',
            KeySchema=[{'AttributeName': 'file_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'file_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        notifications_table = dynamodb.create_table(
            TableName='lms-notifications',
            KeySchema=[{'AttributeName': 'notification_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'notification_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Mock Supabase responses
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'assignment_id': 'assign_1',
                'title': 'Physics Assignment 1',
                'subject_id': 'physics_101',
                'description': 'Newton\'s Laws Assignment'
            }]
        )
        
        # Mock Bedrock Agent response
        quiz_response = """
        Q1: What is Newton's first law of motion?
        A) An object at rest stays at rest
        B) Force equals mass times acceleration
        C) For every action there is an equal and opposite reaction
        D) Energy cannot be created or destroyed
        Correct Answer: A
        Explanation: Newton's first law states that an object at rest stays at rest unless acted upon by an external force.
        Concept: Newton's Laws
        """
        
        mock_bedrock.invoke_agent.return_value = {
            'completion': [{'chunk': {'bytes': quiz_response.encode()}}]
        }
        
        # Test quiz generation
        quiz_service = AssignmentQuizService()
        
        result = quiz_service.generate_assignment_quiz(
            teacher_id='teacher_456',
            assignment_id='assign_1',
            quiz_config={
                'num_questions': 5,
                'difficulty': 'medium',
                'quiz_type': 'multiple_choice'
            }
        )
        
        # Verify result
        assert 'quiz_id' in result
        assert result['assignment_id'] == 'assign_1'
        assert result['status'] == 'generated'
        
        # Verify quiz was stored
        stored_quizzes = quizzes_table.scan()['Items']
        assert len(stored_quizzes) == 1
        assert stored_quizzes[0]['assignment_id'] == 'assign_1'
    
    @mock_dynamodb
    def test_quiz_attempt_workflow(self):
        """Test student quiz attempt workflow"""
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create tables
        quizzes_table = dynamodb.create_table(
            TableName='lms-quizzes',
            KeySchema=[{'AttributeName': 'quiz_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'quiz_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        attempts_table = dynamodb.create_table(
            TableName='lms-quiz-attempts',
            KeySchema=[{'AttributeName': 'attempt_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'attempt_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create test quiz
        test_quiz = {
            'quiz_id': 'quiz_1',
            'teacher_id': 'teacher_456',
            'assignment_id': 'assign_1',
            'subject_id': 'physics_101',
            'status': 'active',
            'max_attempts': 3,
            'time_limit': 30,
            'quiz_data': {
                'questions': [
                    {
                        'question_id': 'q1',
                        'question_text': 'What is Newton\'s first law?',
                        'options': [
                            {'option_id': 'A', 'text': 'Object at rest stays at rest'},
                            {'option_id': 'B', 'text': 'F = ma'},
                            {'option_id': 'C', 'text': 'Action-reaction'},
                            {'option_id': 'D', 'text': 'Energy conservation'}
                        ],
                        'correct_answer': 'A',
                        'explanation': 'First law is about inertia'
                    }
                ]
            }
        }
        
        quizzes_table.put_item(Item=test_quiz)
        
        # Test quiz attempt
        attempt_service = QuizAttemptService()
        
        # Start attempt
        attempt_result = attempt_service.start_quiz_attempt('student_123', 'quiz_1')
        
        assert 'attempt_id' in attempt_result
        assert attempt_result['quiz_id'] == 'quiz_1'
        assert len(attempt_result['questions']) == 1
        
        # Submit attempt
        answers = {'q1': 'A'}
        submission_result = attempt_service.submit_quiz_attempt(
            attempt_result['attempt_id'],
            'student_123',
            answers
        )
        
        assert submission_result['score'] == 1
        assert submission_result['max_score'] == 1
        assert submission_result['percentage'] == 100.0

class TestTeacherDashboard:
    """Test teacher dashboard functionality"""
    
    @mock_dynamodb
    @patch('subjects.teacher_dashboard_service.supabase')
    def test_teacher_dashboard_data(self, mock_supabase):
        """Test teacher dashboard data aggregation"""
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create tables
        chat_table = dynamodb.create_table(
            TableName='lms-chat-history',
            KeySchema=[{'AttributeName': 'conversation_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'conversation_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        quizzes_table = dynamodb.create_table(
            TableName='lms-quizzes',
            KeySchema=[{'AttributeName': 'quiz_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'quiz_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        attempts_table = dynamodb.create_table(
            TableName='lms-quiz-attempts',
            KeySchema=[{'AttributeName': 'attempt_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'attempt_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        files_table = dynamodb.create_table(
            TableName='lms-user-files',
            KeySchema=[{'AttributeName': 'file_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'file_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        analytics_table = dynamodb.create_table(
            TableName='lms-learning-analytics',
            KeySchema=[{'AttributeName': 'analytics_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'analytics_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Mock Supabase responses
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'subject_id': 'physics_101',
                'name': 'Physics 101',
                'description': 'Introduction to Physics'
            }]
        )
        
        # Add test data
        test_chat = {
            'conversation_id': 'conv_1',
            'user_id': 'student_123',
            'subject_id': 'physics_101',
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'What is gravity?'
        }
        chat_table.put_item(Item=test_chat)
        
        test_quiz = {
            'quiz_id': 'quiz_1',
            'teacher_id': 'teacher_456',
            'subject_id': 'physics_101',
            'created_at': datetime.utcnow().isoformat()
        }
        quizzes_table.put_item(Item=test_quiz)
        
        # Test dashboard service
        dashboard_service = TeacherDashboardService()
        
        with patch('subjects.teacher_dashboard_service.bedrock_agent_runtime') as mock_bedrock:
            mock_bedrock.invoke_agent.return_value = {
                'completion': [{'chunk': {'bytes': b'Dashboard insights: Students are engaged.'}}]
            }
            
            dashboard_data = dashboard_service.get_dashboard_data('teacher_456', 'physics_101')
        
        # Verify dashboard structure
        assert 'subject_info' in dashboard_data
        assert 'students' in dashboard_data
        assert 'quiz_performance' in dashboard_data
        assert 'ai_insights' in dashboard_data
        assert dashboard_data['subject_info']['name'] == 'Physics 101'

class TestStudentProgress:
    """Test student progress tracking"""
    
    @mock_dynamodb
    @patch('subjects.student_progress_service.supabase')
    def test_student_progress_tracking(self, mock_supabase):
        """Test student progress calculation and tracking"""
        
        # Setup DynamoDB
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create tables
        analytics_table = dynamodb.create_table(
            TableName='lms-learning-analytics',
            KeySchema=[{'AttributeName': 'analytics_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'analytics_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        chat_table = dynamodb.create_table(
            TableName='lms-chat-history',
            KeySchema=[{'AttributeName': 'conversation_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'conversation_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        attempts_table = dynamodb.create_table(
            TableName='lms-quiz-attempts',
            KeySchema=[{'AttributeName': 'attempt_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'attempt_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        files_table = dynamodb.create_table(
            TableName='lms-user-files',
            KeySchema=[{'AttributeName': 'file_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'file_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Mock Supabase
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'subject_id': 'physics_101',
                'name': 'Physics 101'
            }]
        )
        
        # Add test analytics data
        test_analytics = {
            'analytics_id': 'analytics_1',
            'user_id': 'student_123',
            'subject_id': 'physics_101',
            'overall_progress': 0.75,
            'concept_mastery': {
                'newtons_laws': 0.8,
                'gravity': 0.7,
                'momentum': 0.6
            },
            'engagement_score': 0.8,
            'timestamp': datetime.utcnow().isoformat()
        }
        analytics_table.put_item(Item=test_analytics)
        
        # Add test quiz attempt
        test_attempt = {
            'attempt_id': 'attempt_1',
            'student_id': 'student_123',
            'subject_id': 'physics_101',
            'quiz_id': 'quiz_1',
            'score': 8,
            'max_score': 10,
            'status': 'completed',
            'submitted_at': datetime.utcnow().isoformat()
        }
        attempts_table.put_item(Item=test_attempt)
        
        # Test progress service
        progress_service = StudentProgressService()
        
        with patch('subjects.student_progress_service.bedrock_agent_runtime') as mock_bedrock:
            mock_bedrock.invoke_agent.return_value = {
                'completion': [{'chunk': {'bytes': b'Focus on momentum concepts for improvement.'}}]
            }
            
            progress_data = progress_service.get_student_progress('student_123', 'physics_101')
        
        # Verify progress structure
        assert 'overall_progress' in progress_data
        assert 'concept_mastery' in progress_data
        assert 'quiz_performance' in progress_data
        assert 'recommendations' in progress_data
        
        # Verify concept mastery
        concept_mastery = progress_data['concept_mastery']
        assert 'newtons_laws' in concept_mastery
        assert concept_mastery['newtons_laws'] == 0.8
        
        # Verify quiz performance
        quiz_perf = progress_data['quiz_performance']
        assert quiz_perf['total_attempts'] == 1
        assert quiz_perf['average_score'] == 80.0  # 8/10 * 100

class TestEndToEndWorkflows:
    """Test complete end-to-end workflows"""
    
    @mock_dynamodb
    @mock_s3
    @patch('subjects.subject_integration_handler.bedrock_agent_runtime')
    @patch('subjects.assignment_quiz_service.bedrock_agent_runtime')
    @patch('subjects.subject_integration_handler.supabase')
    @patch('subjects.assignment_quiz_service.supabase')
    def test_complete_assignment_workflow(self, mock_supabase1, mock_supabase2, 
                                        mock_bedrock_quiz, mock_bedrock_chat):
        """Test complete workflow from file upload to quiz generation to student interaction"""
        
        # Setup AWS resources
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        s3_client = boto3.client('s3', region_name='us-east-1')
        
        # Create all required tables
        tables_config = [
            ('lms-user-files', 'file_id'),
            ('lms-chat-history', 'conversation_id'),
            ('lms-quizzes', 'quiz_id'),
            ('lms-quiz-attempts', 'attempt_id'),
            ('lms-notifications', 'notification_id')
        ]
        
        for table_name, key_name in tables_config:
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': key_name, 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': key_name, 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
        
        # Create S3 bucket
        bucket_name = 'lms-documents'
        s3_client.create_bucket(Bucket=bucket_name)
        
        # Upload assignment material
        assignment_content = "Newton's Laws of Motion: 1. An object at rest stays at rest..."
        s3_client.put_object(
            Bucket=bucket_name,
            Key='assignment-material.txt',
            Body=assignment_content
        )
        
        # Mock Supabase responses
        for mock_supabase in [mock_supabase1, mock_supabase2]:
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{
                    'assignment_id': 'assign_1',
                    'title': 'Newton\'s Laws Assignment',
                    'subject_id': 'physics_101',
                    'description': 'Study Newton\'s three laws of motion'
                }]
            )
        
        # Mock Bedrock responses
        mock_bedrock_chat.invoke_agent.return_value = {
            'completion': [{'chunk': {'bytes': b'Newton\'s first law states that an object at rest stays at rest.'}}]
        }
        
        quiz_response = """
        Q1: What is Newton's first law?
        A) Object at rest stays at rest
        B) F = ma
        C) Action-reaction
        D) Energy conservation
        Correct Answer: A
        Explanation: First law is about inertia
        """
        
        mock_bedrock_quiz.invoke_agent.return_value = {
            'completion': [{'chunk': {'bytes': quiz_response.encode()}}]
        }
        
        # Step 1: Teacher uploads assignment material
        file_service = SubjectFileService()
        
        with patch.dict(os.environ, {'S3_BUCKET_NAME': bucket_name}):
            file_result = file_service.process_subject_file(
                user_id='teacher_456',
                subject_id='physics_101',
                file_key='assignment-material.txt',
                file_name='newtons_laws.txt',
                assignment_id='assign_1'
            )
        
        assert file_result['status'] == 'processed'
        
        # Step 2: Teacher generates quiz from assignment
        quiz_service = AssignmentQuizService()
        
        quiz_result = quiz_service.generate_assignment_quiz(
            teacher_id='teacher_456',
            assignment_id='assign_1',
            quiz_config={
                'num_questions': 3,
                'difficulty': 'medium',
                'quiz_type': 'multiple_choice'
            }
        )
        
        assert quiz_result['status'] == 'generated'
        quiz_id = quiz_result['quiz_id']
        
        # Step 3: Student interacts with subject chat
        chat_service = SubjectChatService()
        
        chat_response = chat_service.process_subject_chat(
            user_id='student_123',
            user_role='student',
            subject_id='physics_101',
            message='Can you explain Newton\'s first law?'
        )
        
        assert 'response' in chat_response
        assert 'subject_context' in chat_response
        
        # Step 4: Student takes quiz
        attempt_service = QuizAttemptService()
        
        # Start quiz attempt
        attempt_result = attempt_service.start_quiz_attempt('student_123', quiz_id)
        assert 'attempt_id' in attempt_result
        
        # Submit quiz answers
        answers = {'q1': 'A'}  # Assuming question ID from parsed response
        submission_result = attempt_service.submit_quiz_attempt(
            attempt_result['attempt_id'],
            'student_123',
            answers
        )
        
        # Verify complete workflow
        assert submission_result['score'] >= 0
        
        # Verify all data was stored correctly
        files_table = dynamodb.Table('lms-user-files')
        stored_files = files_table.scan()['Items']
        assert len(stored_files) == 1
        assert stored_files[0]['assignment_id'] == 'assign_1'
        
        quizzes_table = dynamodb.Table('lms-quizzes')
        stored_quizzes = quizzes_table.scan()['Items']
        assert len(stored_quizzes) == 1
        assert stored_quizzes[0]['assignment_id'] == 'assign_1'
        
        chat_table = dynamodb.Table('lms-chat-history')
        stored_chats = chat_table.scan()['Items']
        assert len(stored_chats) == 1
        assert stored_chats[0]['subject_id'] == 'physics_101'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])