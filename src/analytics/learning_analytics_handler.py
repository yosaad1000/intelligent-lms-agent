"""
Learning Analytics Action Group Handler
Provides comprehensive learning analytics and progress tracking for the LMS system
"""

import json
import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
import uuid

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class LearningAnalyticsHandler:
    """Handler for learning analytics operations"""
    
    def __init__(self):
        """Initialize analytics handler with AWS services"""
        
        # AWS clients
        self.dynamodb = boto3.resource('dynamodb')
        self.comprehend = boto3.client('comprehend')
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        
        # DynamoDB tables
        self.analytics_table = self.dynamodb.Table('lms-user-analytics')
        self.progress_table = self.dynamodb.Table('lms-learning-progress')
        self.chat_table = self.dynamodb.Table('lms-chat-conversations')
        self.quiz_table = self.dynamodb.Table('lms-quiz-submissions')
        
        # Configuration
        self.bedrock_model_id = 'amazon.nova-micro-v1:0'
        
    def lambda_handler(self, event, context):
        """Main Lambda handler for learning analytics"""
        
        try:
            logger.info(f"Analytics event: {json.dumps(event)}")
            
            # Parse the action group request
            action_group = event.get('actionGroup', '')
            api_path = event.get('apiPath', '')
            http_method = event.get('httpMethod', 'POST')
            request_body = event.get('requestBody', {})
            
            # Extract parameters
            if 'content' in request_body:
                parameters = json.loads(request_body['content'])
            else:
                parameters = {}
            
            user_id = parameters.get('user_id', 'demo_user')
            
            # Route to appropriate analytics function
            if api_path == '/analyze-progress':
                result = self.analyze_learning_progress(user_id, parameters)
            elif api_path == '/track-interaction':
                result = self.track_learning_interaction(user_id, parameters)
            elif api_path == '/get-recommendations':
                result = self.get_personalized_recommendations(user_id, parameters)
            elif api_path == '/concept-mastery':
                result = self.calculate_concept_mastery(user_id, parameters)
            elif api_path == '/teacher-analytics':
                result = self.generate_teacher_analytics(parameters)
            else:
                result = {
                    'success': False,
                    'error': f'Unknown API path: {api_path}'
                }
            
            # Format response for Bedrock Agent
            response_body = {
                'application/json': {
                    'body': json.dumps(result)
                }
            }
            
            return {
                'messageVersion': '1.0',
                'response': {
                    'actionGroup': action_group,
                    'apiPath': api_path,
                    'httpMethod': http_method,
                    'httpStatusCode': 200,
                    'responseBody': response_body
                }
            }
            
        except Exception as e:
            logger.error(f"Analytics handler error: {str(e)}")
            
            error_response = {
                'application/json': {
                    'body': json.dumps({
                        'success': False,
                        'error': str(e)
                    })
                }
            }
            
            return {
                'messageVersion': '1.0',
                'response': {
                    'actionGroup': action_group,
                    'apiPath': api_path,
                    'httpMethod': http_method,
                    'httpStatusCode': 500,
                    'responseBody': error_response
                }
            }
    
    def analyze_learning_progress(self, user_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze comprehensive learning progress for a user"""
        
        try:
            logger.info(f"Analyzing learning progress for user: {user_id}")
            
            # Get time range for analysis
            days_back = parameters.get('days_back', 30)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Collect learning data from multiple sources
            chat_interactions = self._get_chat_interactions(user_id, start_date, end_date)
            quiz_performance = self._get_quiz_performance(user_id, start_date, end_date)
            concept_mastery = self._get_concept_mastery(user_id)
            
            # Perform sentiment analysis on recent interactions
            sentiment_analysis = self._analyze_interaction_sentiment(chat_interactions)
            
            # Calculate learning metrics
            metrics = self._calculate_learning_metrics(
                chat_interactions, quiz_performance, concept_mastery, sentiment_analysis
            )
            
            # Generate AI insights using Bedrock
            ai_insights = self._generate_ai_insights(user_id, metrics)
            
            # Store analytics results
            analytics_record = {
                'user_id': user_id,
                'analysis_date': end_date.isoformat(),
                'time_period_days': days_back,
                'metrics': metrics,
                'sentiment_analysis': sentiment_analysis,
                'ai_insights': ai_insights,
                'updated_at': int(end_date.timestamp() * 1000)
            }
            
            self.analytics_table.put_item(Item=analytics_record)
            
            return {
                'success': True,
                'user_id': user_id,
                'analysis_period': f'{days_back} days',
                'learning_metrics': metrics,
                'sentiment_analysis': sentiment_analysis,
                'ai_insights': ai_insights,
                'recommendations': self._generate_learning_recommendations(metrics),
                'timestamp': end_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Progress analysis error: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to analyze learning progress: {str(e)}'
            }
    
    def track_learning_interaction(self, user_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Track and analyze a learning interaction"""
        
        try:
            interaction_type = parameters.get('interaction_type', 'chat')
            content = parameters.get('content', '')
            subject = parameters.get('subject', 'general')
            difficulty = parameters.get('difficulty', 'medium')
            
            logger.info(f"Tracking interaction for user {user_id}: {interaction_type}")
            
            # Analyze interaction content with Comprehend
            content_analysis = self._analyze_content_with_comprehend(content)
            
            # Extract learning concepts
            concepts = self._extract_learning_concepts(content, content_analysis)
            
            # Calculate engagement score
            engagement_score = self._calculate_engagement_score(
                interaction_type, content, content_analysis
            )
            
            # Update concept mastery
            mastery_updates = self._update_concept_mastery(
                user_id, concepts, engagement_score, difficulty
            )
            
            # Store interaction record
            interaction_record = {
                'interaction_id': str(uuid.uuid4()),
                'user_id': user_id,
                'interaction_type': interaction_type,
                'subject': subject,
                'difficulty': difficulty,
                'content_preview': content[:200],
                'concepts_identified': concepts,
                'engagement_score': engagement_score,
                'content_analysis': content_analysis,
                'mastery_updates': mastery_updates,
                'timestamp': int(datetime.utcnow().timestamp() * 1000)
            }
            
            self.progress_table.put_item(Item=interaction_record)
            
            return {
                'success': True,
                'interaction_id': interaction_record['interaction_id'],
                'concepts_identified': concepts,
                'engagement_score': engagement_score,
                'mastery_updates': mastery_updates,
                'content_insights': content_analysis
            }
            
        except Exception as e:
            logger.error(f"Interaction tracking error: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to track interaction: {str(e)}'
            }
    
    def get_personalized_recommendations(self, user_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized learning recommendations"""
        
        try:
            logger.info(f"Generating recommendations for user: {user_id}")
            
            # Get user's learning profile
            concept_mastery = self._get_concept_mastery(user_id)
            recent_performance = self._get_recent_performance(user_id)
            learning_patterns = self._analyze_learning_patterns(user_id)
            
            # Generate AI-powered recommendations
            recommendations = self._generate_ai_recommendations(
                user_id, concept_mastery, recent_performance, learning_patterns
            )
            
            # Prioritize recommendations
            prioritized_recommendations = self._prioritize_recommendations(
                recommendations, concept_mastery
            )
            
            return {
                'success': True,
                'user_id': user_id,
                'recommendations': prioritized_recommendations,
                'learning_profile': {
                    'concept_mastery': concept_mastery,
                    'recent_performance': recent_performance,
                    'learning_patterns': learning_patterns
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Recommendations error: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to generate recommendations: {str(e)}'
            }
    
    def calculate_concept_mastery(self, user_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed concept mastery using Knowledge Base similarity"""
        
        try:
            subject = parameters.get('subject', 'all')
            concept = parameters.get('concept', None)
            
            logger.info(f"Calculating concept mastery for user {user_id}, subject: {subject}")
            
            # Get user's interaction history
            interactions = self._get_user_interactions(user_id, subject)
            
            # Calculate mastery for each concept
            if concept:
                # Calculate mastery for specific concept
                mastery_score = self._calculate_single_concept_mastery(
                    user_id, concept, interactions
                )
                concept_mastery = {concept: mastery_score}
            else:
                # Calculate mastery for all concepts
                concept_mastery = self._calculate_all_concepts_mastery(
                    user_id, interactions, subject
                )
            
            # Generate mastery insights
            mastery_insights = self._generate_mastery_insights(concept_mastery)
            
            # Store mastery data
            mastery_record = {
                'user_id': user_id,
                'subject': subject,
                'concept_mastery': concept_mastery,
                'mastery_insights': mastery_insights,
                'calculation_date': datetime.utcnow().isoformat(),
                'updated_at': int(datetime.utcnow().timestamp() * 1000)
            }
            
            # Update or create mastery record
            self.progress_table.put_item(Item=mastery_record)
            
            return {
                'success': True,
                'user_id': user_id,
                'subject': subject,
                'concept_mastery': concept_mastery,
                'mastery_insights': mastery_insights,
                'improvement_areas': self._identify_improvement_areas(concept_mastery),
                'strengths': self._identify_strengths(concept_mastery)
            }
            
        except Exception as e:
            logger.error(f"Concept mastery calculation error: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to calculate concept mastery: {str(e)}'
            }
    
    def generate_teacher_analytics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analytics for teachers"""
        
        try:
            class_id = parameters.get('class_id', 'all')
            subject_id = parameters.get('subject_id', 'all')
            time_period = parameters.get('time_period', 30)  # days
            
            logger.info(f"Generating teacher analytics for class: {class_id}, subject: {subject_id}")
            
            # Get class performance data
            class_performance = self._get_class_performance(class_id, subject_id, time_period)
            
            # Analyze learning trends
            learning_trends = self._analyze_class_learning_trends(class_performance)
            
            # Identify at-risk students
            at_risk_students = self._identify_at_risk_students(class_performance)
            
            # Generate engagement insights
            engagement_insights = self._analyze_class_engagement(class_performance)
            
            # Create AI-powered teaching recommendations
            teaching_recommendations = self._generate_teaching_recommendations(
                class_performance, learning_trends, at_risk_students
            )
            
            # Compile comprehensive analytics
            teacher_analytics = {
                'class_id': class_id,
                'subject_id': subject_id,
                'time_period_days': time_period,
                'class_performance': class_performance,
                'learning_trends': learning_trends,
                'at_risk_students': at_risk_students,
                'engagement_insights': engagement_insights,
                'teaching_recommendations': teaching_recommendations,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return {
                'success': True,
                'teacher_analytics': teacher_analytics,
                'summary': self._generate_analytics_summary(teacher_analytics)
            }
            
        except Exception as e:
            logger.error(f"Teacher analytics error: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to generate teacher analytics: {str(e)}'
            }
    
    # Helper methods for analytics calculations
    
    def _get_chat_interactions(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get chat interactions for time period"""
        try:
            # This would query the chat table for user interactions
            # For now, return mock data structure
            return [
                {
                    'timestamp': datetime.utcnow().isoformat(),
                    'content': 'Sample interaction',
                    'type': 'question',
                    'subject': 'physics'
                }
            ]
        except Exception:
            return []
    
    def _get_quiz_performance(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get quiz performance for time period"""
        try:
            # This would query quiz submissions
            return [
                {
                    'quiz_id': 'quiz_1',
                    'score': 85.0,
                    'subject': 'physics',
                    'timestamp': datetime.utcnow().isoformat()
                }
            ]
        except Exception:
            return []
    
    def _get_concept_mastery(self, user_id: str) -> Dict[str, float]:
        """Get current concept mastery levels"""
        try:
            # This would retrieve stored mastery data
            return {
                'physics_mechanics': 0.75,
                'physics_thermodynamics': 0.60,
                'mathematics_calculus': 0.80
            }
        except Exception:
            return {}
    
    def _analyze_interaction_sentiment(self, interactions: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment of learning interactions"""
        try:
            if not interactions:
                return {'overall_sentiment': 'neutral', 'confidence': 0.5}
            
            # Use Amazon Comprehend for sentiment analysis
            combined_text = ' '.join([interaction.get('content', '') for interaction in interactions[:10]])
            
            if not combined_text.strip():
                return {'overall_sentiment': 'neutral', 'confidence': 0.5}
            
            response = self.comprehend.detect_sentiment(
                Text=combined_text[:5000],  # Limit text length
                LanguageCode='en'
            )
            
            return {
                'overall_sentiment': response['Sentiment'].lower(),
                'confidence': response['SentimentScore'][response['Sentiment']],
                'sentiment_scores': response['SentimentScore']
            }
            
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {str(e)}")
            return {'overall_sentiment': 'neutral', 'confidence': 0.5}
    
    def _calculate_learning_metrics(self, chat_interactions: List, quiz_performance: List, 
                                  concept_mastery: Dict, sentiment_analysis: Dict) -> Dict[str, Any]:
        """Calculate comprehensive learning metrics"""
        
        # Calculate engagement metrics
        total_interactions = len(chat_interactions)
        avg_quiz_score = sum([q.get('score', 0) for q in quiz_performance]) / max(len(quiz_performance), 1)
        
        # Calculate mastery metrics
        avg_mastery = sum(concept_mastery.values()) / max(len(concept_mastery), 1)
        mastery_distribution = self._calculate_mastery_distribution(concept_mastery)
        
        # Calculate progress metrics
        learning_velocity = self._calculate_learning_velocity(chat_interactions, quiz_performance)
        
        return {
            'engagement': {
                'total_interactions': total_interactions,
                'interaction_frequency': total_interactions / 30,  # per day average
                'sentiment_score': sentiment_analysis.get('confidence', 0.5)
            },
            'performance': {
                'average_quiz_score': round(avg_quiz_score, 2),
                'quiz_count': len(quiz_performance),
                'average_mastery': round(avg_mastery, 3),
                'mastery_distribution': mastery_distribution
            },
            'progress': {
                'learning_velocity': learning_velocity,
                'concepts_learned': len([m for m in concept_mastery.values() if m > 0.7]),
                'concepts_in_progress': len([m for m in concept_mastery.values() if 0.3 <= m <= 0.7]),
                'concepts_to_learn': len([m for m in concept_mastery.values() if m < 0.3])
            }
        }
    
    def _generate_ai_insights(self, user_id: str, metrics: Dict[str, Any]) -> str:
        """Generate AI-powered learning insights using Bedrock"""
        
        try:
            prompt = f"""
            Analyze the following learning metrics for a student and provide educational insights:
            
            Engagement Metrics:
            - Total interactions: {metrics['engagement']['total_interactions']}
            - Daily interaction frequency: {metrics['engagement']['interaction_frequency']:.2f}
            - Sentiment score: {metrics['engagement']['sentiment_score']:.2f}
            
            Performance Metrics:
            - Average quiz score: {metrics['performance']['average_quiz_score']}%
            - Number of quizzes taken: {metrics['performance']['quiz_count']}
            - Average concept mastery: {metrics['performance']['average_mastery']:.1%}
            
            Progress Metrics:
            - Concepts mastered: {metrics['progress']['concepts_learned']}
            - Concepts in progress: {metrics['progress']['concepts_in_progress']}
            - Concepts to learn: {metrics['progress']['concepts_to_learn']}
            
            Provide a concise analysis focusing on:
            1. Learning strengths and areas for improvement
            2. Engagement patterns and motivation level
            3. Specific recommendations for continued learning
            4. Potential challenges and how to address them
            
            Keep the response educational, encouraging, and actionable.
            """
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.bedrock_model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            logger.warning(f"AI insights generation failed: {str(e)}")
            return "Unable to generate AI insights at this time. Please check your learning metrics above for progress information."
    
    def _analyze_content_with_comprehend(self, content: str) -> Dict[str, Any]:
        """Analyze content using Amazon Comprehend"""
        
        try:
            if not content or len(content.strip()) < 10:
                return {'key_phrases': [], 'entities': [], 'sentiment': 'neutral'}
            
            # Limit content length for Comprehend
            content = content[:5000]
            
            # Extract key phrases
            key_phrases_response = self.comprehend.detect_key_phrases(
                Text=content,
                LanguageCode='en'
            )
            
            # Extract entities
            entities_response = self.comprehend.detect_entities(
                Text=content,
                LanguageCode='en'
            )
            
            # Analyze sentiment
            sentiment_response = self.comprehend.detect_sentiment(
                Text=content,
                LanguageCode='en'
            )
            
            return {
                'key_phrases': [phrase['Text'] for phrase in key_phrases_response['KeyPhrases'][:10]],
                'entities': [entity['Text'] for entity in entities_response['Entities'][:10]],
                'sentiment': sentiment_response['Sentiment'].lower(),
                'sentiment_confidence': sentiment_response['SentimentScore'][sentiment_response['Sentiment']]
            }
            
        except Exception as e:
            logger.warning(f"Content analysis failed: {str(e)}")
            return {'key_phrases': [], 'entities': [], 'sentiment': 'neutral'}
    
    def _extract_learning_concepts(self, content: str, analysis: Dict[str, Any]) -> List[str]:
        """Extract learning concepts from content and analysis"""
        
        concepts = []
        
        # Extract from key phrases
        key_phrases = analysis.get('key_phrases', [])
        for phrase in key_phrases:
            if len(phrase.split()) <= 3:  # Keep short, meaningful phrases
                concepts.append(phrase.lower())
        
        # Extract from entities
        entities = analysis.get('entities', [])
        for entity in entities:
            if len(entity.split()) <= 2:  # Keep short entities
                concepts.append(entity.lower())
        
        # Remove duplicates and limit
        concepts = list(set(concepts))[:10]
        
        return concepts
    
    def _calculate_engagement_score(self, interaction_type: str, content: str, analysis: Dict[str, Any]) -> float:
        """Calculate engagement score for an interaction"""
        
        base_score = 0.5
        
        # Adjust based on interaction type
        type_multipliers = {
            'chat': 1.0,
            'quiz': 1.2,
            'document_upload': 0.8,
            'voice_interview': 1.5
        }
        
        base_score *= type_multipliers.get(interaction_type, 1.0)
        
        # Adjust based on content length
        content_length = len(content.split())
        if content_length > 50:
            base_score += 0.2
        elif content_length > 20:
            base_score += 0.1
        
        # Adjust based on sentiment
        sentiment = analysis.get('sentiment', 'neutral')
        if sentiment == 'positive':
            base_score += 0.2
        elif sentiment == 'negative':
            base_score -= 0.1
        
        # Adjust based on key phrases (complexity indicator)
        key_phrases_count = len(analysis.get('key_phrases', []))
        if key_phrases_count > 5:
            base_score += 0.1
        
        return min(1.0, max(0.0, base_score))
    
    def _update_concept_mastery(self, user_id: str, concepts: List[str], 
                              engagement_score: float, difficulty: str) -> Dict[str, float]:
        """Update concept mastery based on interaction"""
        
        mastery_updates = {}
        
        # Get current mastery levels
        current_mastery = self._get_concept_mastery(user_id)
        
        # Calculate mastery increment based on engagement and difficulty
        difficulty_multipliers = {
            'easy': 0.05,
            'medium': 0.10,
            'hard': 0.15
        }
        
        base_increment = difficulty_multipliers.get(difficulty, 0.10) * engagement_score
        
        # Update mastery for each concept
        for concept in concepts:
            current_level = current_mastery.get(concept, 0.0)
            
            # Apply learning curve (diminishing returns)
            learning_rate = 1.0 - (current_level * 0.5)
            increment = base_increment * learning_rate
            
            new_level = min(1.0, current_level + increment)
            mastery_updates[concept] = round(new_level, 3)
        
        return mastery_updates
    
    def _calculate_mastery_distribution(self, concept_mastery: Dict[str, float]) -> Dict[str, int]:
        """Calculate distribution of mastery levels"""
        
        distribution = {
            'beginner': 0,      # 0.0 - 0.3
            'intermediate': 0,  # 0.3 - 0.7
            'advanced': 0       # 0.7 - 1.0
        }
        
        for mastery_level in concept_mastery.values():
            if mastery_level < 0.3:
                distribution['beginner'] += 1
            elif mastery_level < 0.7:
                distribution['intermediate'] += 1
            else:
                distribution['advanced'] += 1
        
        return distribution
    
    def _calculate_learning_velocity(self, chat_interactions: List, quiz_performance: List) -> float:
        """Calculate learning velocity (progress over time)"""
        
        # Simple velocity calculation based on recent activity
        recent_interactions = len([i for i in chat_interactions[-7:]])  # Last 7 interactions
        recent_quizzes = len([q for q in quiz_performance[-3:]])  # Last 3 quizzes
        
        velocity = (recent_interactions * 0.1) + (recent_quizzes * 0.3)
        return min(1.0, velocity)
    
    def _generate_learning_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Generate learning recommendations based on metrics"""
        
        recommendations = []
        
        # Engagement recommendations
        if metrics['engagement']['interaction_frequency'] < 1.0:
            recommendations.append("Try to engage with learning materials daily for better retention")
        
        # Performance recommendations
        if metrics['performance']['average_quiz_score'] < 70:
            recommendations.append("Focus on reviewing concepts before taking quizzes")
        
        # Progress recommendations
        if metrics['progress']['concepts_to_learn'] > metrics['progress']['concepts_learned']:
            recommendations.append("Break down complex topics into smaller, manageable concepts")
        
        if metrics['progress']['learning_velocity'] < 0.3:
            recommendations.append("Increase study frequency and vary learning activities")
        
        return recommendations[:5]  # Limit to top 5 recommendations


def lambda_handler(event, context):
    """Lambda entry point"""
    handler = LearningAnalyticsHandler()
    return handler.lambda_handler(event, context)