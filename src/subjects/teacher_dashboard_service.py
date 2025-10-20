"""
Teacher Dashboard Service with AI-Enhanced Analytics
Provides comprehensive analytics and insights for teachers about their subjects and students
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import statistics
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

class TeacherDashboardService:
    """Service for teacher dashboard with AI-enhanced analytics"""
    
    def __init__(self):
        self.chat_table = dynamodb.Table('lms-chat-history')
        self.files_table = dynamodb.Table('lms-user-files')
        self.quizzes_table = dynamodb.Table('lms-quizzes')
        self.attempts_table = dynamodb.Table('lms-quiz-attempts')
        self.analytics_table = dynamodb.Table('lms-learning-analytics')
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
        self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
    
    def get_dashboard_data(self, teacher_id: str, subject_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive dashboard data for teacher"""
        
        try:
            if subject_id:
                # Get data for specific subject
                dashboard_data = self._get_subject_dashboard_data(teacher_id, subject_id)
            else:
                # Get overview data for all teacher's subjects
                dashboard_data = self._get_teacher_overview_data(teacher_id)
            
            # Add AI-generated insights
            dashboard_data['ai_insights'] = self._generate_ai_insights(teacher_id, subject_id, dashboard_data)
            
            return dashboard_data
            
        except Exception as e:
            print(f"Error getting dashboard data: {e}")
            return {'error': str(e)}
    
    def _get_subject_dashboard_data(self, teacher_id: str, subject_id: str) -> Dict[str, Any]:
        """Get detailed dashboard data for a specific subject"""
        
        # Get subject information
        subject_info = self._get_subject_info(subject_id)
        
        # Get enrolled students
        students = self._get_enrolled_students(subject_id)
        
        # Get student engagement metrics
        engagement_metrics = self._get_student_engagement_metrics(subject_id, students)
        
        # Get quiz performance data
        quiz_performance = self._get_quiz_performance_data(teacher_id, subject_id)
        
        # Get file upload and interaction data
        file_metrics = self._get_file_interaction_metrics(subject_id)
        
        # Get recent activity
        recent_activity = self._get_recent_activity(subject_id)
        
        # Get learning progress analytics
        learning_progress = self._get_learning_progress_analytics(subject_id, students)
        
        # Get AI chat analytics
        chat_analytics = self._get_chat_analytics(subject_id)
        
        return {
            'subject_info': subject_info,
            'students': {
                'total_enrolled': len(students),
                'active_students': engagement_metrics['active_students'],
                'engagement_levels': engagement_metrics['engagement_levels'],
                'students_list': students
            },
            'quiz_performance': quiz_performance,
            'file_metrics': file_metrics,
            'recent_activity': recent_activity,
            'learning_progress': learning_progress,
            'chat_analytics': chat_analytics,
            'summary_stats': {
                'total_interactions': engagement_metrics['total_interactions'],
                'avg_quiz_score': quiz_performance['average_score'],
                'files_uploaded': file_metrics['total_files'],
                'active_assignments': self._count_active_assignments(subject_id)
            }
        }
    
    def _get_teacher_overview_data(self, teacher_id: str) -> Dict[str, Any]:
        """Get overview data for all teacher's subjects"""
        
        # Get teacher's subjects
        teacher_subjects = self._get_teacher_subjects(teacher_id)
        
        overview_data = {
            'total_subjects': len(teacher_subjects),
            'subjects': [],
            'overall_stats': {
                'total_students': 0,
                'total_quizzes': 0,
                'total_files': 0,
                'avg_engagement': 0
            }
        }
        
        total_engagement = 0
        
        for subject in teacher_subjects:
            subject_id = subject['subject_id']
            
            # Get basic metrics for each subject
            students = self._get_enrolled_students(subject_id)
            engagement = self._get_student_engagement_metrics(subject_id, students)
            quiz_count = self._count_subject_quizzes(teacher_id, subject_id)
            file_count = self._count_subject_files(subject_id)
            
            subject_data = {
                'subject_id': subject_id,
                'subject_name': subject.get('name', 'Unknown'),
                'student_count': len(students),
                'active_students': engagement['active_students'],
                'quiz_count': quiz_count,
                'file_count': file_count,
                'engagement_score': engagement['avg_engagement_score']
            }
            
            overview_data['subjects'].append(subject_data)
            
            # Update overall stats
            overview_data['overall_stats']['total_students'] += len(students)
            overview_data['overall_stats']['total_quizzes'] += quiz_count
            overview_data['overall_stats']['total_files'] += file_count
            total_engagement += engagement['avg_engagement_score']
        
        # Calculate average engagement
        if len(teacher_subjects) > 0:
            overview_data['overall_stats']['avg_engagement'] = total_engagement / len(teacher_subjects)
        
        return overview_data
    
    def _get_subject_info(self, subject_id: str) -> Dict[str, Any]:
        """Get subject information from Supabase"""
        
        try:
            response = supabase.table('subjects').select('*').eq('subject_id', subject_id).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Error getting subject info: {e}")
        
        return {'subject_id': subject_id, 'name': 'Unknown Subject'}
    
    def _get_enrolled_students(self, subject_id: str) -> List[Dict[str, Any]]:
        """Get list of enrolled students"""
        
        try:
            # Get enrollments
            enrollments = supabase.table('subject_enrollments').select('student_id').eq('subject_id', subject_id).execute()
            
            students = []
            for enrollment in enrollments.data:
                student_id = enrollment['student_id']
                
                # Get student info
                student_info = supabase.table('users').select('*').eq('user_id', student_id).execute()
                if student_info.data:
                    students.append(student_info.data[0])
            
            return students
            
        except Exception as e:
            print(f"Error getting enrolled students: {e}")
            return []
    
    def _get_student_engagement_metrics(self, subject_id: str, students: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate student engagement metrics"""
        
        try:
            engagement_data = {
                'active_students': 0,
                'engagement_levels': {'high': 0, 'medium': 0, 'low': 0},
                'total_interactions': 0,
                'avg_engagement_score': 0,
                'student_details': []
            }
            
            total_engagement_score = 0
            
            for student in students:
                student_id = student['user_id']
                
                # Get student's interactions in this subject
                interactions = self._get_student_subject_interactions(student_id, subject_id)
                
                # Calculate engagement score
                engagement_score = self._calculate_engagement_score(interactions)
                
                # Categorize engagement level
                if engagement_score >= 0.7:
                    level = 'high'
                elif engagement_score >= 0.4:
                    level = 'medium'
                else:
                    level = 'low'
                
                engagement_data['engagement_levels'][level] += 1
                
                if engagement_score > 0.1:  # Consider active if any meaningful interaction
                    engagement_data['active_students'] += 1
                
                engagement_data['total_interactions'] += interactions['total_count']
                total_engagement_score += engagement_score
                
                engagement_data['student_details'].append({
                    'student_id': student_id,
                    'name': student.get('name', 'Unknown'),
                    'email': student.get('email', ''),
                    'engagement_score': engagement_score,
                    'engagement_level': level,
                    'total_interactions': interactions['total_count'],
                    'last_activity': interactions['last_activity']
                })
            
            # Calculate average engagement
            if len(students) > 0:
                engagement_data['avg_engagement_score'] = total_engagement_score / len(students)
            
            return engagement_data
            
        except Exception as e:
            print(f"Error calculating engagement metrics: {e}")
            return {'active_students': 0, 'engagement_levels': {'high': 0, 'medium': 0, 'low': 0}, 'total_interactions': 0, 'avg_engagement_score': 0}
    
    def _get_student_subject_interactions(self, student_id: str, subject_id: str) -> Dict[str, Any]:
        """Get student's interactions within a specific subject"""
        
        try:
            # Get chat interactions
            chat_response = self.chat_table.scan(
                FilterExpression='user_id = :user_id AND subject_id = :subject_id',
                ExpressionAttributeValues={
                    ':user_id': student_id,
                    ':subject_id': subject_id
                }
            )
            
            # Get quiz attempts
            quiz_response = self.attempts_table.scan(
                FilterExpression='student_id = :student_id AND subject_id = :subject_id',
                ExpressionAttributeValues={
                    ':student_id': student_id,
                    ':subject_id': subject_id
                }
            )
            
            # Get file uploads
            file_response = self.files_table.scan(
                FilterExpression='user_id = :user_id AND subject_id = :subject_id',
                ExpressionAttributeValues={
                    ':user_id': student_id,
                    ':subject_id': subject_id
                }
            )
            
            chat_interactions = chat_response.get('Items', [])
            quiz_attempts = quiz_response.get('Items', [])
            file_uploads = file_response.get('Items', [])
            
            # Find last activity
            all_timestamps = []
            for item in chat_interactions + quiz_attempts + file_uploads:
                if 'timestamp' in item:
                    all_timestamps.append(item['timestamp'])
                elif 'submitted_at' in item:
                    all_timestamps.append(item['submitted_at'])
                elif 'upload_timestamp' in item:
                    all_timestamps.append(item['upload_timestamp'])
            
            last_activity = max(all_timestamps) if all_timestamps else None
            
            return {
                'chat_count': len(chat_interactions),
                'quiz_count': len(quiz_attempts),
                'file_count': len(file_uploads),
                'total_count': len(chat_interactions) + len(quiz_attempts) + len(file_uploads),
                'last_activity': last_activity
            }
            
        except Exception as e:
            print(f"Error getting student interactions: {e}")
            return {'chat_count': 0, 'quiz_count': 0, 'file_count': 0, 'total_count': 0, 'last_activity': None}
    
    def _calculate_engagement_score(self, interactions: Dict[str, Any]) -> float:
        """Calculate engagement score based on interactions"""
        
        # Simple engagement scoring algorithm
        chat_weight = 0.4
        quiz_weight = 0.4
        file_weight = 0.2
        
        # Normalize counts (cap at reasonable maximums)
        chat_score = min(interactions['chat_count'] / 10, 1.0)  # Max 10 chats = full score
        quiz_score = min(interactions['quiz_count'] / 5, 1.0)   # Max 5 quizzes = full score
        file_score = min(interactions['file_count'] / 3, 1.0)   # Max 3 files = full score
        
        engagement_score = (chat_score * chat_weight + 
                          quiz_score * quiz_weight + 
                          file_score * file_weight)
        
        # Boost for recent activity
        if interactions['last_activity']:
            try:
                last_activity_date = datetime.fromisoformat(interactions['last_activity'])
                days_since_activity = (datetime.utcnow() - last_activity_date).days
                
                if days_since_activity <= 7:
                    engagement_score *= 1.2  # 20% boost for activity within a week
                elif days_since_activity <= 30:
                    engagement_score *= 1.1  # 10% boost for activity within a month
            except:
                pass
        
        return min(engagement_score, 1.0)  # Cap at 1.0
    
    def _get_quiz_performance_data(self, teacher_id: str, subject_id: str) -> Dict[str, Any]:
        """Get quiz performance analytics"""
        
        try:
            # Get all quizzes for this subject
            quizzes = self.quizzes_table.scan(
                FilterExpression='teacher_id = :teacher_id AND subject_id = :subject_id',
                ExpressionAttributeValues={
                    ':teacher_id': teacher_id,
                    ':subject_id': subject_id
                }
            )
            
            quiz_data = []
            all_scores = []
            total_attempts = 0
            
            for quiz in quizzes.get('Items', []):
                quiz_id = quiz['quiz_id']
                
                # Get attempts for this quiz
                attempts = self.attempts_table.scan(
                    FilterExpression='quiz_id = :quiz_id AND #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':quiz_id': quiz_id,
                        ':status': 'completed'
                    }
                )
                
                quiz_attempts = attempts.get('Items', [])
                quiz_scores = [float(attempt.get('score', 0)) / float(attempt.get('max_score', 1)) * 100 
                             for attempt in quiz_attempts if attempt.get('max_score', 0) > 0]
                
                quiz_info = {
                    'quiz_id': quiz_id,
                    'assignment_id': quiz.get('assignment_id'),
                    'created_at': quiz.get('created_at'),
                    'total_attempts': len(quiz_attempts),
                    'average_score': statistics.mean(quiz_scores) if quiz_scores else 0,
                    'highest_score': max(quiz_scores) if quiz_scores else 0,
                    'lowest_score': min(quiz_scores) if quiz_scores else 0,
                    'completion_rate': len(quiz_attempts) / max(len(self._get_enrolled_students(subject_id)), 1) * 100
                }
                
                quiz_data.append(quiz_info)
                all_scores.extend(quiz_scores)
                total_attempts += len(quiz_attempts)
            
            return {
                'total_quizzes': len(quizzes.get('Items', [])),
                'total_attempts': total_attempts,
                'average_score': statistics.mean(all_scores) if all_scores else 0,
                'score_distribution': self._calculate_score_distribution(all_scores),
                'quiz_details': quiz_data
            }
            
        except Exception as e:
            print(f"Error getting quiz performance data: {e}")
            return {'total_quizzes': 0, 'total_attempts': 0, 'average_score': 0, 'quiz_details': []}
    
    def _calculate_score_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate score distribution by grade ranges"""
        
        distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        
        for score in scores:
            if score >= 90:
                distribution['A'] += 1
            elif score >= 80:
                distribution['B'] += 1
            elif score >= 70:
                distribution['C'] += 1
            elif score >= 60:
                distribution['D'] += 1
            else:
                distribution['F'] += 1
        
        return distribution
    
    def _get_file_interaction_metrics(self, subject_id: str) -> Dict[str, Any]:
        """Get file upload and interaction metrics"""
        
        try:
            # Get all files for this subject
            files = self.files_table.scan(
                FilterExpression='subject_id = :subject_id',
                ExpressionAttributeValues={':subject_id': subject_id}
            )
            
            file_items = files.get('Items', [])
            
            # Categorize files
            file_types = defaultdict(int)
            assignment_files = 0
            student_files = 0
            
            for file in file_items:
                file_type = file.get('file_type', 'unknown')
                file_types[file_type] += 1
                
                if file.get('assignment_id'):
                    assignment_files += 1
                else:
                    student_files += 1
            
            return {
                'total_files': len(file_items),
                'assignment_files': assignment_files,
                'student_files': student_files,
                'file_types': dict(file_types),
                'recent_uploads': self._get_recent_file_uploads(subject_id)
            }
            
        except Exception as e:
            print(f"Error getting file metrics: {e}")
            return {'total_files': 0, 'assignment_files': 0, 'student_files': 0}
    
    def _get_recent_file_uploads(self, subject_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent file uploads for the subject"""
        
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            files = self.files_table.scan(
                FilterExpression='subject_id = :subject_id AND upload_timestamp > :cutoff',
                ExpressionAttributeValues={
                    ':subject_id': subject_id,
                    ':cutoff': cutoff_date
                }
            )
            
            recent_files = []
            for file in files.get('Items', []):
                recent_files.append({
                    'filename': file.get('filename', 'Unknown'),
                    'user_id': file.get('user_id'),
                    'upload_timestamp': file.get('upload_timestamp'),
                    'file_type': file.get('file_type', 'unknown')
                })
            
            # Sort by upload time (most recent first)
            recent_files.sort(key=lambda x: x.get('upload_timestamp', ''), reverse=True)
            
            return recent_files[:10]  # Return top 10 recent files
            
        except Exception as e:
            print(f"Error getting recent file uploads: {e}")
            return []
    
    def _get_recent_activity(self, subject_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent activity in the subject"""
        
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            activities = []
            
            # Get recent chat interactions
            chats = self.chat_table.scan(
                FilterExpression='subject_id = :subject_id AND #timestamp > :cutoff',
                ExpressionAttributeNames={'#timestamp': 'timestamp'},
                ExpressionAttributeValues={
                    ':subject_id': subject_id,
                    ':cutoff': cutoff_date
                }
            )
            
            for chat in chats.get('Items', []):
                activities.append({
                    'type': 'chat',
                    'user_id': chat.get('user_id'),
                    'timestamp': chat.get('timestamp'),
                    'description': f"AI chat interaction"
                })
            
            # Get recent quiz attempts
            attempts = self.attempts_table.scan(
                FilterExpression='subject_id = :subject_id AND started_at > :cutoff',
                ExpressionAttributeValues={
                    ':subject_id': subject_id,
                    ':cutoff': cutoff_date
                }
            )
            
            for attempt in attempts.get('Items', []):
                activities.append({
                    'type': 'quiz_attempt',
                    'user_id': attempt.get('student_id'),
                    'timestamp': attempt.get('started_at'),
                    'description': f"Quiz attempt"
                })
            
            # Sort by timestamp (most recent first)
            activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return activities[:20]  # Return top 20 recent activities
            
        except Exception as e:
            print(f"Error getting recent activity: {e}")
            return []
    
    def _get_learning_progress_analytics(self, subject_id: str, students: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get learning progress analytics for students"""
        
        try:
            progress_data = {
                'overall_progress': 0,
                'students_on_track': 0,
                'students_struggling': 0,
                'concept_mastery': {},
                'student_progress': []
            }
            
            total_progress = 0
            
            for student in students:
                student_id = student['user_id']
                
                # Get student's learning analytics
                analytics = self.analytics_table.scan(
                    FilterExpression='user_id = :user_id AND subject_id = :subject_id',
                    ExpressionAttributeValues={
                        ':user_id': student_id,
                        ':subject_id': subject_id
                    }
                )
                
                student_analytics = analytics.get('Items', [])
                
                # Calculate progress metrics
                if student_analytics:
                    # Use the most recent analytics record
                    latest_analytics = max(student_analytics, key=lambda x: x.get('timestamp', ''))
                    
                    progress_score = latest_analytics.get('overall_progress', 0)
                    mastery_data = latest_analytics.get('concept_mastery', {})
                    
                    # Categorize student progress
                    if progress_score >= 0.7:
                        progress_data['students_on_track'] += 1
                    elif progress_score < 0.4:
                        progress_data['students_struggling'] += 1
                    
                    total_progress += progress_score
                    
                    # Aggregate concept mastery
                    for concept, mastery in mastery_data.items():
                        if concept not in progress_data['concept_mastery']:
                            progress_data['concept_mastery'][concept] = []
                        progress_data['concept_mastery'][concept].append(mastery)
                    
                    progress_data['student_progress'].append({
                        'student_id': student_id,
                        'name': student.get('name', 'Unknown'),
                        'progress_score': progress_score,
                        'concept_mastery': mastery_data
                    })
                else:
                    # No analytics data available
                    progress_data['student_progress'].append({
                        'student_id': student_id,
                        'name': student.get('name', 'Unknown'),
                        'progress_score': 0,
                        'concept_mastery': {}
                    })
            
            # Calculate overall progress
            if len(students) > 0:
                progress_data['overall_progress'] = total_progress / len(students)
            
            # Calculate average concept mastery
            for concept, masteries in progress_data['concept_mastery'].items():
                progress_data['concept_mastery'][concept] = statistics.mean(masteries) if masteries else 0
            
            return progress_data
            
        except Exception as e:
            print(f"Error getting learning progress analytics: {e}")
            return {'overall_progress': 0, 'students_on_track': 0, 'students_struggling': 0}
    
    def _get_chat_analytics(self, subject_id: str) -> Dict[str, Any]:
        """Get AI chat analytics for the subject"""
        
        try:
            # Get all chat interactions for this subject
            chats = self.chat_table.scan(
                FilterExpression='subject_id = :subject_id',
                ExpressionAttributeValues={':subject_id': subject_id}
            )
            
            chat_items = chats.get('Items', [])
            
            # Analyze chat patterns
            total_chats = len(chat_items)
            unique_users = len(set(chat.get('user_id') for chat in chat_items))
            
            # Analyze question types and topics
            question_types = defaultdict(int)
            topics = defaultdict(int)
            
            for chat in chat_items:
                metadata = chat.get('metadata', {})
                
                # Extract question type if available
                if 'question_type' in metadata:
                    question_types[metadata['question_type']] += 1
                
                # Extract topics if available
                if 'topics' in metadata:
                    for topic in metadata['topics']:
                        topics[topic] += 1
            
            return {
                'total_interactions': total_chats,
                'unique_users': unique_users,
                'avg_interactions_per_user': total_chats / max(unique_users, 1),
                'question_types': dict(question_types),
                'popular_topics': dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10])
            }
            
        except Exception as e:
            print(f"Error getting chat analytics: {e}")
            return {'total_interactions': 0, 'unique_users': 0}
    
    def _generate_ai_insights(self, teacher_id: str, subject_id: Optional[str], 
                            dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights for the teacher dashboard"""
        
        try:
            # Build context for AI analysis
            context = self._build_insights_context(dashboard_data, subject_id)
            
            # Generate insights using Bedrock Agent
            insights_prompt = f"""
            Analyze the following teacher dashboard data and provide actionable insights:
            
            {context}
            
            Please provide:
            1. Key observations about student engagement and performance
            2. Areas of concern that need attention
            3. Recommendations for improving student outcomes
            4. Trends and patterns in the data
            5. Specific actions the teacher can take
            
            Format your response as structured insights with clear recommendations.
            """
            
            session_id = f"insights_{teacher_id}_{int(datetime.now().timestamp())}"
            
            response = bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=insights_prompt,
                sessionAttributes={
                    'task_type': 'teacher_insights',
                    'teacher_id': teacher_id,
                    'subject_id': subject_id or 'overview',
                    'context_type': 'dashboard_analytics'
                }
            )
            
            # Process response
            completion = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')
            
            return {
                'ai_generated_insights': completion,
                'generated_at': datetime.utcnow().isoformat(),
                'context_summary': self._summarize_context(dashboard_data)
            }
            
        except Exception as e:
            print(f"Error generating AI insights: {e}")
            return {
                'ai_generated_insights': "Unable to generate AI insights at this time.",
                'error': str(e)
            }
    
    def _build_insights_context(self, dashboard_data: Dict[str, Any], subject_id: Optional[str]) -> str:
        """Build context string for AI insights generation"""
        
        context_parts = []
        
        if subject_id:
            # Subject-specific context
            subject_info = dashboard_data.get('subject_info', {})
            students = dashboard_data.get('students', {})
            quiz_performance = dashboard_data.get('quiz_performance', {})
            
            context_parts.append(f"Subject: {subject_info.get('name', 'Unknown')}")
            context_parts.append(f"Total Students: {students.get('total_enrolled', 0)}")
            context_parts.append(f"Active Students: {students.get('active_students', 0)}")
            context_parts.append(f"Average Quiz Score: {quiz_performance.get('average_score', 0):.1f}%")
            
            # Engagement levels
            engagement = students.get('engagement_levels', {})
            context_parts.append(f"Engagement - High: {engagement.get('high', 0)}, Medium: {engagement.get('medium', 0)}, Low: {engagement.get('low', 0)}")
            
        else:
            # Overview context
            overall_stats = dashboard_data.get('overall_stats', {})
            context_parts.append(f"Total Subjects: {dashboard_data.get('total_subjects', 0)}")
            context_parts.append(f"Total Students: {overall_stats.get('total_students', 0)}")
            context_parts.append(f"Average Engagement: {overall_stats.get('avg_engagement', 0):.2f}")
        
        return "\n".join(context_parts)
    
    def _summarize_context(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize key metrics for context"""
        
        if 'students' in dashboard_data:
            # Subject-specific summary
            return {
                'total_students': dashboard_data.get('students', {}).get('total_enrolled', 0),
                'active_students': dashboard_data.get('students', {}).get('active_students', 0),
                'avg_quiz_score': dashboard_data.get('quiz_performance', {}).get('average_score', 0),
                'total_interactions': dashboard_data.get('summary_stats', {}).get('total_interactions', 0)
            }
        else:
            # Overview summary
            return {
                'total_subjects': dashboard_data.get('total_subjects', 0),
                'total_students': dashboard_data.get('overall_stats', {}).get('total_students', 0),
                'avg_engagement': dashboard_data.get('overall_stats', {}).get('avg_engagement', 0)
            }
    
    def _get_teacher_subjects(self, teacher_id: str) -> List[Dict[str, Any]]:
        """Get subjects taught by the teacher"""
        
        try:
            # Get teacher's subject assignments
            assignments = supabase.table('subject_teachers').select('subject_id').eq('teacher_id', teacher_id).execute()
            
            subjects = []
            for assignment in assignments.data:
                subject_id = assignment['subject_id']
                
                # Get subject details
                subject_info = supabase.table('subjects').select('*').eq('subject_id', subject_id).execute()
                if subject_info.data:
                    subjects.append(subject_info.data[0])
            
            return subjects
            
        except Exception as e:
            print(f"Error getting teacher subjects: {e}")
            return []
    
    def _count_subject_quizzes(self, teacher_id: str, subject_id: str) -> int:
        """Count quizzes for a subject"""
        
        try:
            response = self.quizzes_table.scan(
                FilterExpression='teacher_id = :teacher_id AND subject_id = :subject_id',
                ExpressionAttributeValues={
                    ':teacher_id': teacher_id,
                    ':subject_id': subject_id
                },
                Select='COUNT'
            )
            return response.get('Count', 0)
        except Exception as e:
            print(f"Error counting subject quizzes: {e}")
            return 0
    
    def _count_subject_files(self, subject_id: str) -> int:
        """Count files for a subject"""
        
        try:
            response = self.files_table.scan(
                FilterExpression='subject_id = :subject_id',
                ExpressionAttributeValues={':subject_id': subject_id},
                Select='COUNT'
            )
            return response.get('Count', 0)
        except Exception as e:
            print(f"Error counting subject files: {e}")
            return 0
    
    def _count_active_assignments(self, subject_id: str) -> int:
        """Count active assignments for a subject"""
        
        try:
            current_date = datetime.utcnow().isoformat()
            
            response = supabase.table('assignments').select('assignment_id').eq('subject_id', subject_id).gte('due_date', current_date).execute()
            return len(response.data)
        except Exception as e:
            print(f"Error counting active assignments: {e}")
            return 0