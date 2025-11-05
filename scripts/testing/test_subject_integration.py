#!/usr/bin/env python3
"""
Simple test runner for Subject and Assignment Integration
Tests core functionality without full pytest setup
"""

import sys
import os
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Mock external dependencies
sys.modules['supabase'] = MagicMock()
sys.modules['boto3'] = MagicMock()

def test_subject_chat_service():
    """Test SubjectChatService basic functionality"""
    
    print("Testing SubjectChatService...")
    
    try:
        from subjects.subject_integration_handler import SubjectChatService
        
        # Mock dependencies
        with patch('subjects.subject_integration_handler.dynamodb') as mock_dynamodb, \
             patch('subjects.subject_integration_handler.supabase') as mock_supabase, \
             patch('subjects.subject_integration_handler.bedrock_agent_runtime') as mock_bedrock:
            
            # Setup mocks
            mock_table = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{
                    'subject_id': 'physics_101',
                    'name': 'Physics 101',
                    'description': 'Introduction to Physics'
                }]
            )
            
            mock_bedrock.invoke_agent.return_value = {
                'completion': [
                    {'chunk': {'bytes': b'This is a helpful response about physics.'}}
                ]
            }
            
            # Test the service
            chat_service = SubjectChatService()
            
            response = chat_service.process_subject_chat(
                user_id='student_123',
                user_role='student',
                subject_id='physics_101',
                message='What is gravity?'
            )
            
            # Verify response structure
            assert 'conversation_id' in response
            assert 'response' in response
            assert 'subject_context' in response
            
            print("✅ SubjectChatService test passed")
            return True
            
    except Exception as e:
        print(f"❌ SubjectChatService test failed: {e}")
        return False

def test_assignment_quiz_service():
    """Test AssignmentQuizService basic functionality"""
    
    print("Testing AssignmentQuizService...")
    
    try:
        from subjects.assignment_quiz_service import AssignmentQuizService
        
        with patch('subjects.assignment_quiz_service.dynamodb') as mock_dynamodb, \
             patch('subjects.assignment_quiz_service.supabase') as mock_supabase, \
             patch('subjects.assignment_quiz_service.bedrock_agent_runtime') as mock_bedrock:
            
            # Setup mocks
            mock_table = MagicMock()
            mock_dynamodb.Table.return_value = mock_table
            
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{
                    'assignment_id': 'assign_1',
                    'title': 'Physics Assignment',
                    'subject_id': 'physics_101'
                }]
            )
            
            # Mock quiz generation response
            quiz_response = """
            Q1: What is Newton's first law?
            A) Object at rest stays at rest
            B) F = ma
            C) Action-reaction
            D) Energy conservation
            Correct Answer: A
            Explanation: First law is about inertia
            """
            
            mock_bedrock.invoke_agent.return_value = {
                'completion': [{'chunk': {'bytes': quiz_response.encode()}}]
            }
            
            # Test the service
            quiz_service = AssignmentQuizService()
            
            # Mock the permission check
            with patch.object(quiz_service, '_verify_teacher_permission', return_value=True):
                result = quiz_service.generate_assignment_quiz(
                    teacher_id='teacher_456',
                    assignment_id='assign_1',
                    quiz_config={
                        'num_questions': 3,
                        'difficulty': 'medium'
                    }
                )
            
            # Verify result structure
            assert 'quiz_id' in result
            assert result['assignment_id'] == 'assign_1'
            assert result['status'] == 'generated'
            
            print("✅ AssignmentQuizService test passed")
            return True
            
    except Exception as e:
        print(f"❌ AssignmentQuizService test failed: {e}")
        return False

def test_teacher_dashboard_service():
    """Test TeacherDashboardService basic functionality"""
    
    print("Testing TeacherDashboardService...")
    
    try:
        from subjects.teacher_dashboard_service import TeacherDashboardService
        
        with patch('subjects.teacher_dashboard_service.dynamodb') as mock_dynamodb, \
             patch('subjects.teacher_dashboard_service.supabase') as mock_supabase, \
             patch('subjects.teacher_dashboard_service.bedrock_agent_runtime') as mock_bedrock:
            
            # Setup mocks
            mock_table = MagicMock()
            mock_table.scan.return_value = {'Items': []}
            mock_dynamodb.Table.return_value = mock_table
            
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{
                    'subject_id': 'physics_101',
                    'name': 'Physics 101'
                }]
            )
            
            mock_bedrock.invoke_agent.return_value = {
                'completion': [{'chunk': {'bytes': b'Dashboard insights generated.'}}]
            }
            
            # Test the service
            dashboard_service = TeacherDashboardService()
            
            dashboard_data = dashboard_service.get_dashboard_data('teacher_456', 'physics_101')
            
            # Verify dashboard structure
            assert 'subject_info' in dashboard_data
            assert 'students' in dashboard_data
            assert 'ai_insights' in dashboard_data
            
            print("✅ TeacherDashboardService test passed")
            return True
            
    except Exception as e:
        print(f"❌ TeacherDashboardService test failed: {e}")
        return False

def test_student_progress_service():
    """Test StudentProgressService basic functionality"""
    
    print("Testing StudentProgressService...")
    
    try:
        from subjects.student_progress_service import StudentProgressService
        
        with patch('subjects.student_progress_service.dynamodb') as mock_dynamodb, \
             patch('subjects.student_progress_service.supabase') as mock_supabase, \
             patch('subjects.student_progress_service.bedrock_agent_runtime') as mock_bedrock:
            
            # Setup mocks
            mock_table = MagicMock()
            mock_table.scan.return_value = {'Items': []}
            mock_dynamodb.Table.return_value = mock_table
            
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{
                    'subject_id': 'physics_101',
                    'name': 'Physics 101'
                }]
            )
            
            mock_bedrock.invoke_agent.return_value = {
                'completion': [{'chunk': {'bytes': b'Focus on momentum concepts.'}}]
            }
            
            # Test the service
            progress_service = StudentProgressService()
            
            progress_data = progress_service.get_student_progress('student_123', 'physics_101')
            
            # Verify progress structure
            assert 'overall_progress' in progress_data
            assert 'learning_analytics' in progress_data
            assert 'recommendations' in progress_data
            
            print("✅ StudentProgressService test passed")
            return True
            
    except Exception as e:
        print(f"❌ StudentProgressService test failed: {e}")
        return False

def test_lambda_handlers():
    """Test Lambda handler functions"""
    
    print("Testing Lambda handlers...")
    
    try:
        from subjects.subject_integration_handler import (
            subject_chat_handler, subject_files_handler, 
            assignment_quiz_handler, teacher_dashboard_handler,
            student_progress_handler
        )
        
        # Test subject chat handler
        event = {
            'httpMethod': 'POST',
            'pathParameters': {'subject_id': 'physics_101'},
            'body': json.dumps({'message': 'What is gravity?'}),
            'requestContext': {
                'authorizer': {
                    'user_id': 'student_123',
                    'role': 'student'
                }
            }
        }
        
        with patch('subjects.subject_integration_handler.SubjectChatService') as mock_service:
            mock_service.return_value.process_subject_chat.return_value = {
                'conversation_id': 'conv_123',
                'response': 'Gravity is a fundamental force.',
                'subject_context': {'subject_name': 'Physics 101'}
            }
            
            response = subject_chat_handler(event, {})
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'conversation_id' in body
        
        print("✅ Lambda handlers test passed")
        return True
        
    except Exception as e:
        print(f"❌ Lambda handlers test failed: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 Starting Subject and Assignment Integration Tests")
    print("=" * 60)
    
    tests = [
        test_subject_chat_service,
        test_assignment_quiz_service,
        test_teacher_dashboard_service,
        test_student_progress_service,
        test_lambda_handlers
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Subject and Assignment Integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)