"""
Student Progress Service
Provides detailed progress tracking and analytics for students per subject
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics
from collections import defaultdict
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

class StudentProgressService:
    """Service for tracking and analyzing student progress per subject"""
    
    def __init__(self):
        self.analytics_table = dynamodb.Table('lms-learning-analytics')
        self.chat_table = dynamodb.Table('lms-chat-history')
        self.attempts_table = dynamodb.Table('lms-quiz-attempts')
        self.files_table = dynamodb.Table('lms-user-files')
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
        self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
    
    def get_student_progress(self, student_id: str, subject_id: str) -> Dict[str, Any]:
        """Get comprehensive progress data for a student in a specific subject"""
        
        try:
            # Get subject information
            subject_info = self._get_subject_info(subject_id)
            
            # Get student's learning analytics
            learning_analytics = self._get_student_learning_analytics(student_id, subject_id)
            
            # Get interaction history
            interaction_history = self._get_student_interactions(student_id, subject_id)
            
            # Get quiz performance
            quiz_performance = self._get_student_quiz_performance(student_id, subject_id)
            
            # Get concept mastery
            concept_mastery = self._get_concept_mastery(student_id, subject_id)
            
            # Get learning trajectory
            learning_trajectory = self._calculate_learning_trajectory(student_id, subject_id)
            
            # Get recommendations
            recommendations = self._generate_learning_recommendations(
                student_id, subject_id, learning_analytics, quiz_performance, concept_mastery
            )
            
            # Calculate overall progress score
            overall_progress = self._calculate_overall_progress(
                learning_analytics, quiz_performance, concept_mastery, interaction_history
            )
            
            return {
                'student_id': student_id,
                'subject_info': subject_info,
                'overall_progress': overall_progress,
                'learning_analytics': learning_analytics,
                'interaction_history': interaction_history,
                'quiz_performance': quiz_performance,
                'concept_mastery': concept_mastery,
                'learning_trajectory': learning_trajectory,
                'recommendations': recommendations,
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting student progress: {e}")
            return {'error': str(e)}
    
    def get_subject_progress_summary(self, teacher_id: str, subject_id: str) -> Dict[str, Any]:
        """Get progress summary for all students in a subject (teacher view)"""
        
        try:
            # Verify teacher permission
            if not self._verify_teacher_permission(teacher_id, subject_id):
                raise ValueError("Teacher does not have permission for this subject")
            
            # Get enrolled students
            students = self._get_enrolled_students(subject_id)
            
            # Get progress data for each student
            student_progress = []
            overall_metrics = {
                'total_students': len(students),
                'students_on_track': 0,
                'students_struggling': 0,
                'average_progress': 0,
                'concept_mastery_overview': defaultdict(list)
            }
            
            total_progress = 0
            
            for student in students:
                student_id = student['user_id']
                
                # Get basic progress metrics
                progress_data = self._get_basic_student_progress(student_id, subject_id)
                
                student_summary = {
                    'student_id': student_id,
                    'name': student.get('name', 'Unknown'),
                    'email': student.get('email', ''),
                    'overall_progress': progress_data['overall_progress'],
                    'quiz_average': progress_data['quiz_average'],
                    'interaction_count': progress_data['interaction_count'],
                    'last_activity': progress_data['last_activity'],
                    'status': self._determine_student_status(progress_data['overall_progress']),
                    'concept_mastery': progress_data['concept_mastery']
                }
                
                student_progress.append(student_summary)
                
                # Update overall metrics
                total_progress += progress_data['overall_progress']
                
                if progress_data['overall_progress'] >= 0.7:
                    overall_metrics['students_on_track'] += 1
                elif progress_data['overall_progress'] < 0.4:
                    overall_metrics['students_struggling'] += 1
                
                # Aggregate concept mastery
                for concept, mastery in progress_data['concept_mastery'].items():
                    overall_metrics['concept_mastery_overview'][concept].append(mastery)
            
            # Calculate averages
            if len(students) > 0:
                overall_metrics['average_progress'] = total_progress / len(students)
            
            # Calculate average concept mastery
            concept_averages = {}
            for concept, masteries in overall_metrics['concept_mastery_overview'].items():
                concept_averages[concept] = statistics.mean(masteries) if masteries else 0
            
            overall_metrics['concept_mastery_overview'] = concept_averages
            
            return {
                'subject_id': subject_id,
                'subject_info': self._get_subject_info(subject_id),
                'overall_metrics': overall_metrics,
                'student_progress': student_progress,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting subject progress summary: {e}")
            return {'error': str(e)}
    
    def update_student_progress(self, student_id: str, subject_id: str, 
                              interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update student progress based on new interaction"""
        
        try:
            # Get current analytics
            current_analytics = self._get_student_learning_analytics(student_id, subject_id)
            
            # Update analytics based on interaction
            updated_analytics = self._update_analytics_with_interaction(
                current_analytics, interaction_data
            )
            
            # Store updated analytics
            self._store_learning_analytics(student_id, subject_id, updated_analytics)
            
            return {
                'status': 'updated',
                'student_id': student_id,
                'subject_id': subject_id,
                'updated_analytics': updated_analytics
            }
            
        except Exception as e:
            print(f"Error updating student progress: {e}")
            return {'error': str(e)}
    
    def _get_subject_info(self, subject_id: str) -> Dict[str, Any]:
        """Get subject information"""
        
        try:
            response = supabase.table('subjects').select('*').eq('subject_id', subject_id).execute()
            if response.data:
                return response.data[0]
        except Exception as e:
            print(f"Error getting subject info: {e}")
        
        return {'subject_id': subject_id, 'name': 'Unknown Subject'}
    
    def _get_student_learning_analytics(self, student_id: str, subject_id: str) -> Dict[str, Any]:
        """Get student's learning analytics for the subject"""
        
        try:
            response = self.analytics_table.scan(
                FilterExpression='user_id = :user_id AND subject_id = :subject_id',
                ExpressionAttributeValues={
                    ':user_id': student_id,
                    ':subject_id': subject_id
                }
            )
            
            analytics_records = response.get('Items', [])
            
            if analytics_records:
                # Get the most recent analytics record
                latest_record = max(analytics_records, key=lambda x: x.get('timestamp', ''))
                return latest_record
            else:
                # Return default analytics structure
                return {
                    'user_id': student_id,
                    'subject_id': subject_id,
                    'overall_progress': 0.0,
                    'concept_mastery': {},
                    'learning_velocity': 0.0,
                    'engagement_score': 0.0,
                    'difficulty_preference': 'medium',
                    'learning_style': 'balanced',
                    'total_interactions': 0,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            print(f"Error getting learning analytics: {e}")
            return {}
    
    def _get_student_interactions(self, student_id: str, subject_id: str) -> Dict[str, Any]:
        """Get student's interaction history in the subject"""
        
        try:
            # Get chat interactions
            chat_response = self.chat_table.scan(
                FilterExpression='user_id = :user_id AND subject_id = :subject_id',
                ExpressionAttributeValues={
                    ':user_id': student_id,
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
            file_uploads = file_response.get('Items', [])
            
            # Sort interactions by timestamp
            all_interactions = []
            
            for chat in chat_interactions:
                all_interactions.append({
                    'type': 'chat',
                    'timestamp': chat.get('timestamp'),
                    'content': chat.get('message', '')[:100] + '...',  # Preview
                    'metadata': chat.get('metadata', {})
                })
            
            for file in file_uploads:
                all_interactions.append({
                    'type': 'file_upload',
                    'timestamp': file.get('upload_timestamp'),
                    'content': f"Uploaded: {file.get('filename', 'Unknown file')}",
                    'metadata': {'file_type': file.get('file_type', 'unknown')}
                })
            
            # Sort by timestamp (most recent first)
            all_interactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return {
                'total_interactions': len(all_interactions),
                'chat_count': len(chat_interactions),
                'file_count': len(file_uploads),
                'recent_interactions': all_interactions[:20],  # Last 20 interactions
                'first_interaction': min([i.get('timestamp', '') for i in all_interactions]) if all_interactions else None,
                'last_interaction': max([i.get('timestamp', '') for i in all_interactions]) if all_interactions else None
            }
            
        except Exception as e:
            print(f"Error getting student interactions: {e}")
            return {'total_interactions': 0, 'chat_count': 0, 'file_count': 0}
    
    def _get_student_quiz_performance(self, student_id: str, subject_id: str) -> Dict[str, Any]:
        """Get student's quiz performance in the subject"""
        
        try:
            response = self.attempts_table.scan(
                FilterExpression='student_id = :student_id AND subject_id = :subject_id AND #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':student_id': student_id,
                    ':subject_id': subject_id,
                    ':status': 'completed'
                }
            )
            
            attempts = response.get('Items', [])
            
            if not attempts:
                return {
                    'total_attempts': 0,
                    'average_score': 0,
                    'highest_score': 0,
                    'lowest_score': 0,
                    'improvement_trend': 'no_data',
                    'recent_attempts': []
                }
            
            # Calculate scores as percentages
            scores = []
            for attempt in attempts:
                if attempt.get('max_score', 0) > 0:
                    percentage = (float(attempt.get('score', 0)) / float(attempt['max_score'])) * 100
                    scores.append(percentage)
            
            # Sort attempts by submission time
            attempts.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
            
            # Calculate improvement trend
            improvement_trend = self._calculate_improvement_trend(scores)
            
            return {
                'total_attempts': len(attempts),
                'average_score': statistics.mean(scores) if scores else 0,
                'highest_score': max(scores) if scores else 0,
                'lowest_score': min(scores) if scores else 0,
                'improvement_trend': improvement_trend,
                'recent_attempts': [
                    {
                        'quiz_id': attempt.get('quiz_id'),
                        'score': float(attempt.get('score', 0)),
                        'max_score': float(attempt.get('max_score', 1)),
                        'percentage': (float(attempt.get('score', 0)) / float(attempt.get('max_score', 1))) * 100 if attempt.get('max_score', 0) > 0 else 0,
                        'submitted_at': attempt.get('submitted_at')
                    }
                    for attempt in attempts[:10]  # Last 10 attempts
                ]
            }
            
        except Exception as e:
            print(f"Error getting quiz performance: {e}")
            return {'total_attempts': 0, 'average_score': 0}
    
    def _get_concept_mastery(self, student_id: str, subject_id: str) -> Dict[str, float]:
        """Get student's concept mastery levels"""
        
        try:
            # Get latest analytics record
            analytics = self._get_student_learning_analytics(student_id, subject_id)
            
            concept_mastery = analytics.get('concept_mastery', {})
            
            # If no concept mastery data, infer from interactions
            if not concept_mastery:
                concept_mastery = self._infer_concept_mastery_from_interactions(student_id, subject_id)
            
            return concept_mastery
            
        except Exception as e:
            print(f"Error getting concept mastery: {e}")
            return {}
    
    def _calculate_learning_trajectory(self, student_id: str, subject_id: str) -> Dict[str, Any]:
        """Calculate student's learning trajectory over time"""
        
        try:
            # Get all analytics records for this student/subject
            response = self.analytics_table.scan(
                FilterExpression='user_id = :user_id AND subject_id = :subject_id',
                ExpressionAttributeValues={
                    ':user_id': student_id,
                    ':subject_id': subject_id
                }
            )
            
            analytics_records = response.get('Items', [])
            
            if len(analytics_records) < 2:
                return {
                    'trend': 'insufficient_data',
                    'velocity': 0,
                    'trajectory_points': []
                }
            
            # Sort by timestamp
            analytics_records.sort(key=lambda x: x.get('timestamp', ''))
            
            # Calculate trajectory points
            trajectory_points = []
            for record in analytics_records:
                trajectory_points.append({
                    'timestamp': record.get('timestamp'),
                    'overall_progress': record.get('overall_progress', 0),
                    'engagement_score': record.get('engagement_score', 0)
                })
            
            # Calculate trend
            progress_values = [point['overall_progress'] for point in trajectory_points]
            trend = self._calculate_trend(progress_values)
            
            # Calculate learning velocity (progress per day)
            if len(trajectory_points) >= 2:
                first_point = trajectory_points[0]
                last_point = trajectory_points[-1]
                
                try:
                    first_date = datetime.fromisoformat(first_point['timestamp'])
                    last_date = datetime.fromisoformat(last_point['timestamp'])
                    days_diff = (last_date - first_date).days
                    
                    if days_diff > 0:
                        progress_diff = last_point['overall_progress'] - first_point['overall_progress']
                        velocity = progress_diff / days_diff
                    else:
                        velocity = 0
                except:
                    velocity = 0
            else:
                velocity = 0
            
            return {
                'trend': trend,
                'velocity': velocity,
                'trajectory_points': trajectory_points[-10:]  # Last 10 points
            }
            
        except Exception as e:
            print(f"Error calculating learning trajectory: {e}")
            return {'trend': 'error', 'velocity': 0, 'trajectory_points': []}
    
    def _generate_learning_recommendations(self, student_id: str, subject_id: str,
                                         learning_analytics: Dict[str, Any],
                                         quiz_performance: Dict[str, Any],
                                         concept_mastery: Dict[str, float]) -> Dict[str, Any]:
        """Generate personalized learning recommendations using AI"""
        
        try:
            # Build context for AI recommendations
            context = self._build_recommendation_context(
                learning_analytics, quiz_performance, concept_mastery
            )
            
            # Generate recommendations using Bedrock Agent
            recommendations_prompt = f"""
            Based on the following student learning data, provide personalized learning recommendations:
            
            {context}
            
            Please provide:
            1. Specific areas where the student should focus their study efforts
            2. Recommended learning activities or resources
            3. Study strategies that would be most effective for this student
            4. Concepts that need reinforcement
            5. Next steps for continued learning progress
            
            Format your response as actionable recommendations with clear explanations.
            """
            
            session_id = f"recommendations_{student_id}_{int(datetime.now().timestamp())}"
            
            response = bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=recommendations_prompt,
                sessionAttributes={
                    'task_type': 'learning_recommendations',
                    'student_id': student_id,
                    'subject_id': subject_id,
                    'context_type': 'progress_analysis'
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
                'ai_recommendations': completion,
                'focus_areas': self._identify_focus_areas(concept_mastery),
                'difficulty_adjustment': self._recommend_difficulty_adjustment(learning_analytics, quiz_performance),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return {
                'ai_recommendations': "Unable to generate personalized recommendations at this time.",
                'focus_areas': [],
                'difficulty_adjustment': 'maintain'
            }
    
    def _calculate_overall_progress(self, learning_analytics: Dict[str, Any],
                                  quiz_performance: Dict[str, Any],
                                  concept_mastery: Dict[str, float],
                                  interaction_history: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall progress score and metrics"""
        
        try:
            # Weight different components
            analytics_weight = 0.4
            quiz_weight = 0.3
            concept_weight = 0.2
            engagement_weight = 0.1
            
            # Analytics component
            analytics_score = learning_analytics.get('overall_progress', 0)
            
            # Quiz component
            quiz_score = quiz_performance.get('average_score', 0) / 100  # Convert to 0-1 scale
            
            # Concept mastery component
            if concept_mastery:
                concept_score = statistics.mean(concept_mastery.values())
            else:
                concept_score = 0
            
            # Engagement component
            total_interactions = interaction_history.get('total_interactions', 0)
            engagement_score = min(total_interactions / 20, 1.0)  # Cap at 20 interactions = full score
            
            # Calculate weighted overall score
            overall_score = (
                analytics_score * analytics_weight +
                quiz_score * quiz_weight +
                concept_score * concept_weight +
                engagement_score * engagement_weight
            )
            
            # Determine progress level
            if overall_score >= 0.8:
                level = 'excellent'
            elif overall_score >= 0.6:
                level = 'good'
            elif overall_score >= 0.4:
                level = 'satisfactory'
            elif overall_score >= 0.2:
                level = 'needs_improvement'
            else:
                level = 'struggling'
            
            return {
                'overall_score': overall_score,
                'level': level,
                'components': {
                    'analytics': analytics_score,
                    'quiz_performance': quiz_score,
                    'concept_mastery': concept_score,
                    'engagement': engagement_score
                },
                'calculated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error calculating overall progress: {e}")
            return {'overall_score': 0, 'level': 'unknown'}
    
    def _get_basic_student_progress(self, student_id: str, subject_id: str) -> Dict[str, Any]:
        """Get basic progress metrics for a student (used in summary views)"""
        
        try:
            # Get learning analytics
            analytics = self._get_student_learning_analytics(student_id, subject_id)
            
            # Get quiz performance
            quiz_perf = self._get_student_quiz_performance(student_id, subject_id)
            
            # Get interaction count
            interactions = self._get_student_interactions(student_id, subject_id)
            
            # Get concept mastery
            concepts = self._get_concept_mastery(student_id, subject_id)
            
            return {
                'overall_progress': analytics.get('overall_progress', 0),
                'quiz_average': quiz_perf.get('average_score', 0),
                'interaction_count': interactions.get('total_interactions', 0),
                'last_activity': interactions.get('last_interaction'),
                'concept_mastery': concepts
            }
            
        except Exception as e:
            print(f"Error getting basic student progress: {e}")
            return {
                'overall_progress': 0,
                'quiz_average': 0,
                'interaction_count': 0,
                'last_activity': None,
                'concept_mastery': {}
            }
    
    def _verify_teacher_permission(self, teacher_id: str, subject_id: str) -> bool:
        """Verify teacher has permission for the subject"""
        
        try:
            response = supabase.table('subject_teachers').select('*').eq('teacher_id', teacher_id).eq('subject_id', subject_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error verifying teacher permission: {e}")
            return False
    
    def _get_enrolled_students(self, subject_id: str) -> List[Dict[str, Any]]:
        """Get enrolled students for a subject"""
        
        try:
            enrollments = supabase.table('subject_enrollments').select('student_id').eq('subject_id', subject_id).execute()
            
            students = []
            for enrollment in enrollments.data:
                student_id = enrollment['student_id']
                student_info = supabase.table('users').select('*').eq('user_id', student_id).execute()
                if student_info.data:
                    students.append(student_info.data[0])
            
            return students
            
        except Exception as e:
            print(f"Error getting enrolled students: {e}")
            return []
    
    def _determine_student_status(self, progress_score: float) -> str:
        """Determine student status based on progress score"""
        
        if progress_score >= 0.7:
            return 'on_track'
        elif progress_score >= 0.4:
            return 'needs_attention'
        else:
            return 'struggling'
    
    def _calculate_improvement_trend(self, scores: List[float]) -> str:
        """Calculate improvement trend from quiz scores"""
        
        if len(scores) < 2:
            return 'insufficient_data'
        
        # Take last 5 scores for trend analysis
        recent_scores = scores[-5:]
        
        if len(recent_scores) < 2:
            return 'insufficient_data'
        
        # Simple linear trend calculation
        trend_sum = 0
        for i in range(1, len(recent_scores)):
            trend_sum += recent_scores[i] - recent_scores[i-1]
        
        avg_trend = trend_sum / (len(recent_scores) - 1)
        
        if avg_trend > 2:
            return 'improving'
        elif avg_trend < -2:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from a list of values"""
        
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if second_avg > first_avg + 0.1:
            return 'improving'
        elif second_avg < first_avg - 0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _infer_concept_mastery_from_interactions(self, student_id: str, subject_id: str) -> Dict[str, float]:
        """Infer concept mastery from student interactions"""
        
        try:
            # Get chat interactions to analyze topics
            chats = self.chat_table.scan(
                FilterExpression='user_id = :user_id AND subject_id = :subject_id',
                ExpressionAttributeValues={
                    ':user_id': student_id,
                    ':subject_id': subject_id
                }
            )
            
            concept_interactions = defaultdict(int)
            
            for chat in chats.get('Items', []):
                metadata = chat.get('metadata', {})
                if 'topics' in metadata:
                    for topic in metadata['topics']:
                        concept_interactions[topic] += 1
            
            # Convert interaction counts to mastery scores (simple heuristic)
            concept_mastery = {}
            for concept, count in concept_interactions.items():
                # More interactions = higher mastery (capped at 1.0)
                mastery = min(count / 10, 1.0)
                concept_mastery[concept] = mastery
            
            return concept_mastery
            
        except Exception as e:
            print(f"Error inferring concept mastery: {e}")
            return {}
    
    def _build_recommendation_context(self, learning_analytics: Dict[str, Any],
                                   quiz_performance: Dict[str, Any],
                                   concept_mastery: Dict[str, float]) -> str:
        """Build context for AI recommendation generation"""
        
        context_parts = [
            f"Overall Progress: {learning_analytics.get('overall_progress', 0):.2f}",
            f"Learning Velocity: {learning_analytics.get('learning_velocity', 0):.2f}",
            f"Engagement Score: {learning_analytics.get('engagement_score', 0):.2f}",
            f"Quiz Average: {quiz_performance.get('average_score', 0):.1f}%",
            f"Total Quiz Attempts: {quiz_performance.get('total_attempts', 0)}",
            f"Improvement Trend: {quiz_performance.get('improvement_trend', 'unknown')}"
        ]
        
        if concept_mastery:
            context_parts.append("Concept Mastery Levels:")
            for concept, mastery in concept_mastery.items():
                context_parts.append(f"  - {concept}: {mastery:.2f}")
        
        return "\n".join(context_parts)
    
    def _identify_focus_areas(self, concept_mastery: Dict[str, float]) -> List[str]:
        """Identify areas that need focus based on concept mastery"""
        
        focus_areas = []
        
        for concept, mastery in concept_mastery.items():
            if mastery < 0.6:  # Below 60% mastery
                focus_areas.append(concept)
        
        # Sort by mastery level (lowest first)
        focus_areas.sort(key=lambda x: concept_mastery[x])
        
        return focus_areas[:5]  # Return top 5 focus areas
    
    def _recommend_difficulty_adjustment(self, learning_analytics: Dict[str, Any],
                                       quiz_performance: Dict[str, Any]) -> str:
        """Recommend difficulty adjustment based on performance"""
        
        overall_progress = learning_analytics.get('overall_progress', 0)
        quiz_average = quiz_performance.get('average_score', 0)
        improvement_trend = quiz_performance.get('improvement_trend', 'stable')
        
        # High performance and improving trend
        if overall_progress > 0.8 and quiz_average > 85 and improvement_trend == 'improving':
            return 'increase'
        
        # Low performance or declining trend
        elif overall_progress < 0.4 or quiz_average < 60 or improvement_trend == 'declining':
            return 'decrease'
        
        # Moderate performance
        else:
            return 'maintain'
    
    def _update_analytics_with_interaction(self, current_analytics: Dict[str, Any],
                                         interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update analytics based on new interaction"""
        
        updated_analytics = current_analytics.copy()
        
        # Update interaction count
        updated_analytics['total_interactions'] = updated_analytics.get('total_interactions', 0) + 1
        
        # Update engagement score
        engagement_boost = 0.1 if interaction_data.get('type') == 'chat' else 0.05
        current_engagement = updated_analytics.get('engagement_score', 0)
        updated_analytics['engagement_score'] = min(current_engagement + engagement_boost, 1.0)
        
        # Update concept mastery if concepts are identified
        if 'concepts' in interaction_data:
            concept_mastery = updated_analytics.get('concept_mastery', {})
            for concept in interaction_data['concepts']:
                current_mastery = concept_mastery.get(concept, 0)
                # Small boost for each interaction with the concept
                concept_mastery[concept] = min(current_mastery + 0.05, 1.0)
            updated_analytics['concept_mastery'] = concept_mastery
        
        # Update timestamp
        updated_analytics['timestamp'] = datetime.utcnow().isoformat()
        
        return updated_analytics
    
    def _store_learning_analytics(self, student_id: str, subject_id: str,
                                analytics_data: Dict[str, Any]) -> None:
        """Store updated learning analytics"""
        
        try:
            analytics_item = {
                'analytics_id': f"{student_id}_{subject_id}_{int(datetime.now().timestamp())}",
                'user_id': student_id,
                'subject_id': subject_id,
                **analytics_data,
                'ttl': int((datetime.utcnow() + timedelta(days=365)).timestamp())
            }
            
            self.analytics_table.put_item(Item=analytics_item)
            
        except Exception as e:
            print(f"Error storing learning analytics: {e}")