"""
Enhanced Quiz Generation Lambda Function with Multi-Language Support
Extends Bedrock Agent with advanced quiz generation and translation capabilities
"""

import json
import boto3
import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class EnhancedQuizGenerator:
    """Enhanced quiz generator with multi-language support"""
    
    def __init__(self):
        """Initialize AWS services"""
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        self.comprehend = boto3.client('comprehend')
        self.translate = boto3.client('translate')
        self.dynamodb = boto3.resource('dynamodb')
        
        # DynamoDB tables
        self.quizzes_table = self.dynamodb.Table('lms-quizzes')
        self.submissions_table = self.dynamodb.Table('lms-quiz-submissions')
        self.analytics_table = self.dynamodb.Table('lms-analytics')
        
        # Bedrock model configuration
        self.model_id = "amazon.nova-micro-v1:0"
    
    async def generate_quiz_with_translation(
        self,
        topic: str,
        difficulty: str = "intermediate",
        question_count: int = 5,
        target_language: str = "en",
        user_id: str = None,
        rag_context: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate quiz with multi-language support"""
        
        try:
            # Detect source language if content is provided
            source_language = await self._detect_language(topic)
            
            # Translate topic to English for processing if needed
            if source_language != "en":
                topic_en = await self._translate_text(topic, source_language, "en")
            else:
                topic_en = topic
            
            # Generate quiz in English first
            quiz_data = await self._generate_quiz_content(
                topic_en, difficulty, question_count, rag_context
            )
            
            # Translate quiz to target language if needed
            if target_language != "en":
                quiz_data = await self._translate_quiz(quiz_data, "en", target_language)
            
            # Store quiz in DynamoDB
            quiz_id = await self._store_quiz(
                user_id, quiz_data, topic, difficulty, source_language, target_language
            )
            
            return {
                "success": True,
                "quiz_id": quiz_id,
                "quiz": quiz_data,
                "metadata": {
                    "source_language": source_language,
                    "target_language": target_language,
                    "topic": topic,
                    "difficulty": difficulty,
                    "question_count": len(quiz_data.get("questions", [])),
                    "generated_at": datetime.utcnow().isoformat(),
                    "translation_used": source_language != target_language
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "QUIZ_GENERATION_FAILED"
            }
    
    async def _detect_language(self, text: str) -> str:
        """Detect language using Amazon Comprehend"""
        
        try:
            response = self.comprehend.detect_dominant_language(Text=text)
            
            if response['Languages']:
                detected_lang = response['Languages'][0]['LanguageCode']
                confidence = response['Languages'][0]['Score']
                
                # Only use detection if confidence is high
                if confidence > 0.8:
                    logger.info(f"Detected language: {detected_lang} (confidence: {confidence:.2f})")
                    return detected_lang
            
            return "en"  # Default to English
            
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return "en"
    
    async def _translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using Amazon Translate"""
        
        try:
            response = self.translate.translate_text(
                Text=text,
                SourceLanguageCode=source_lang,
                TargetLanguageCode=target_lang
            )
            
            translated_text = response['TranslatedText']
            logger.info(f"Translated text from {source_lang} to {target_lang}")
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return text  # Return original text if translation fails
    
    async def _generate_quiz_content(
        self,
        topic: str,
        difficulty: str,
        question_count: int,
        rag_context: List[Dict] = None
    ) -> Dict[str, Any]:
        """Generate quiz content using Bedrock Nova model"""
        
        # Build context from RAG if available
        context_text = ""
        if rag_context:
            context_text = "\n\n".join([
                f"Document: {doc.get('source', 'Unknown')}\n{doc.get('text', '')[:500]}"
                for doc in rag_context[:3]
            ])
        
        # Create quiz generation prompt
        prompt = f"""Generate an educational quiz about "{topic}" with the following specifications:

Difficulty Level: {difficulty}
Number of Questions: {question_count}

{f"Context from uploaded documents:\n{context_text}\n" if context_text else ""}

Requirements:
1. Create {question_count} multiple-choice questions
2. Each question should have 4 options (A, B, C, D)
3. Provide the correct answer for each question
4. Include a brief explanation for each correct answer
5. Questions should be appropriate for {difficulty} level
6. Focus on key concepts and practical understanding

Format the response as JSON with this structure:
{{
    "quiz_title": "Quiz about {topic}",
    "topic": "{topic}",
    "difficulty": "{difficulty}",
    "questions": [
        {{
            "question_number": 1,
            "question": "Question text here?",
            "options": {{
                "A": "Option A text",
                "B": "Option B text", 
                "C": "Option C text",
                "D": "Option D text"
            }},
            "correct_answer": "A",
            "explanation": "Explanation of why A is correct"
        }}
    ]
}}

Generate the quiz now:"""

        try:
            # Invoke Bedrock Nova model
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body['output']['message']['content'][0]['text']
            
            # Extract JSON from response
            try:
                # Find JSON in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    quiz_data = json.loads(json_str)
                    
                    # Validate quiz structure
                    if self._validate_quiz_structure(quiz_data):
                        return quiz_data
                    else:
                        raise ValueError("Invalid quiz structure")
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON response: {str(e)}")
                # Fallback: create structured quiz from text response
                return self._create_fallback_quiz(content, topic, difficulty)
            
        except Exception as e:
            logger.error(f"Error generating quiz content: {str(e)}")
            # Return a basic fallback quiz
            return self._create_basic_fallback_quiz(topic, difficulty, question_count)
    
    def _validate_quiz_structure(self, quiz_data: Dict) -> bool:
        """Validate quiz data structure"""
        
        required_fields = ['quiz_title', 'topic', 'difficulty', 'questions']
        
        if not all(field in quiz_data for field in required_fields):
            return False
        
        questions = quiz_data.get('questions', [])
        if not questions:
            return False
        
        for question in questions:
            required_q_fields = ['question', 'options', 'correct_answer']
            if not all(field in question for field in required_q_fields):
                return False
            
            options = question.get('options', {})
            if not all(opt in options for opt in ['A', 'B', 'C', 'D']):
                return False
        
        return True
    
    def _create_fallback_quiz(self, content: str, topic: str, difficulty: str) -> Dict[str, Any]:
        """Create a fallback quiz from unstructured content"""
        
        return {
            "quiz_title": f"Quiz about {topic}",
            "topic": topic,
            "difficulty": difficulty,
            "questions": [
                {
                    "question_number": 1,
                    "question": f"What is a key concept related to {topic}?",
                    "options": {
                        "A": "Option A (generated from AI response)",
                        "B": "Option B (generated from AI response)",
                        "C": "Option C (generated from AI response)",
                        "D": "Option D (generated from AI response)"
                    },
                    "correct_answer": "A",
                    "explanation": f"This question tests understanding of {topic} concepts."
                }
            ],
            "generation_note": "Fallback quiz generated due to parsing issues"
        }
    
    def _create_basic_fallback_quiz(self, topic: str, difficulty: str, question_count: int) -> Dict[str, Any]:
        """Create a basic fallback quiz when all else fails"""
        
        questions = []
        for i in range(min(question_count, 3)):  # Limit to 3 questions for fallback
            questions.append({
                "question_number": i + 1,
                "question": f"Question {i + 1} about {topic}?",
                "options": {
                    "A": f"Option A for {topic}",
                    "B": f"Option B for {topic}",
                    "C": f"Option C for {topic}",
                    "D": f"Option D for {topic}"
                },
                "correct_answer": "A",
                "explanation": f"This is a basic question about {topic}."
            })
        
        return {
            "quiz_title": f"Basic Quiz about {topic}",
            "topic": topic,
            "difficulty": difficulty,
            "questions": questions,
            "generation_note": "Basic fallback quiz due to generation errors"
        }
    
    async def _translate_quiz(self, quiz_data: Dict, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Translate entire quiz to target language"""
        
        try:
            translated_quiz = quiz_data.copy()
            
            # Translate quiz title
            translated_quiz["quiz_title"] = await self._translate_text(
                quiz_data["quiz_title"], source_lang, target_lang
            )
            
            # Translate questions
            translated_questions = []
            for question in quiz_data.get("questions", []):
                translated_question = question.copy()
                
                # Translate question text
                translated_question["question"] = await self._translate_text(
                    question["question"], source_lang, target_lang
                )
                
                # Translate options
                translated_options = {}
                for key, option_text in question.get("options", {}).items():
                    translated_options[key] = await self._translate_text(
                        option_text, source_lang, target_lang
                    )
                translated_question["options"] = translated_options
                
                # Translate explanation
                if "explanation" in question:
                    translated_question["explanation"] = await self._translate_text(
                        question["explanation"], source_lang, target_lang
                    )
                
                translated_questions.append(translated_question)
            
            translated_quiz["questions"] = translated_questions
            translated_quiz["translated_from"] = source_lang
            translated_quiz["translated_to"] = target_lang
            
            return translated_quiz
            
        except Exception as e:
            logger.error(f"Error translating quiz: {str(e)}")
            return quiz_data  # Return original if translation fails
    
    async def _store_quiz(
        self,
        user_id: str,
        quiz_data: Dict,
        original_topic: str,
        difficulty: str,
        source_language: str,
        target_language: str
    ) -> str:
        """Store quiz in DynamoDB with enhanced metadata"""
        
        quiz_id = str(uuid.uuid4())
        
        try:
            quiz_item = {
                'quiz_id': quiz_id,
                'user_id': user_id or 'anonymous',
                'quiz_title': quiz_data.get('quiz_title', f'Quiz about {original_topic}'),
                'topic': original_topic,
                'difficulty': difficulty,
                'questions': quiz_data.get('questions', []),
                'question_count': len(quiz_data.get('questions', [])),
                'source_language': source_language,
                'target_language': target_language,
                'translation_used': source_language != target_language,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'generated',
                'attempts': 0,
                'best_score': None,
                'generation_metadata': {
                    'model_used': self.model_id,
                    'enhanced_generator': True,
                    'multilingual_support': True,
                    'generation_timestamp': datetime.utcnow().isoformat()
                }
            }
            
            self.quizzes_table.put_item(Item=quiz_item)
            logger.info(f"Stored quiz {quiz_id} for user {user_id}")
            
            return quiz_id
            
        except Exception as e:
            logger.error(f"Error storing quiz: {str(e)}")
            raise
    
    async def submit_quiz_with_analytics(
        self,
        user_id: str,
        quiz_id: str,
        answers: Dict[str, str],
        time_taken: Optional[int] = None
    ) -> Dict[str, Any]:
        """Submit quiz answers with enhanced learning analytics"""
        
        try:
            # Get quiz data
            quiz_response = self.quizzes_table.get_item(Key={'quiz_id': quiz_id})
            
            if 'Item' not in quiz_response:
                raise ValueError(f"Quiz not found: {quiz_id}")
            
            quiz_data = quiz_response['Item']
            
            # Verify user owns this quiz
            if quiz_data['user_id'] != user_id and quiz_data['user_id'] != 'anonymous':
                raise ValueError("Unauthorized access to quiz")
            
            # Score the quiz
            scoring_result = await self._score_quiz_with_analytics(
                quiz_data, answers, time_taken
            )
            
            # Store submission
            submission_id = await self._store_submission(
                user_id, quiz_id, answers, scoring_result, time_taken
            )
            
            # Update quiz metadata
            await self._update_quiz_stats(quiz_id, scoring_result['score'])
            
            # Update learning analytics
            await self._update_learning_analytics(
                user_id, quiz_data, scoring_result
            )
            
            return {
                "success": True,
                "submission_id": submission_id,
                "score": scoring_result['score'],
                "correct_answers": scoring_result['correct_answers'],
                "total_questions": scoring_result['total_questions'],
                "detailed_results": scoring_result['detailed_results'],
                "analytics": scoring_result['analytics'],
                "time_taken": time_taken,
                "performance_insights": scoring_result['insights']
            }
            
        except Exception as e:
            logger.error(f"Error submitting quiz: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "QUIZ_SUBMISSION_FAILED"
            }
    
    async def _score_quiz_with_analytics(
        self,
        quiz_data: Dict,
        answers: Dict[str, str],
        time_taken: Optional[int]
    ) -> Dict[str, Any]:
        """Score quiz with detailed analytics"""
        
        questions = quiz_data['questions']
        total_questions = len(questions)
        correct_answers = 0
        detailed_results = []
        concept_performance = {}
        
        for i, question in enumerate(questions):
            question_num = str(i + 1)
            user_answer = answers.get(question_num, '').upper()
            correct_answer = question.get('correct_answer', '').upper()
            
            is_correct = user_answer == correct_answer
            if is_correct:
                correct_answers += 1
            
            # Extract concepts from question for analytics
            question_text = question.get('question', '')
            concepts = await self._extract_concepts(question_text)
            
            for concept in concepts:
                if concept not in concept_performance:
                    concept_performance[concept] = {'correct': 0, 'total': 0}
                concept_performance[concept]['total'] += 1
                if is_correct:
                    concept_performance[concept]['correct'] += 1
            
            detailed_results.append({
                'question_number': i + 1,
                'question': question_text,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question.get('explanation', ''),
                'concepts': concepts
            })
        
        # Calculate score and analytics
        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Performance insights
        insights = self._generate_performance_insights(
            score_percentage, concept_performance, time_taken, total_questions
        )
        
        return {
            'score': score_percentage,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'detailed_results': detailed_results,
            'analytics': {
                'concept_performance': concept_performance,
                'time_per_question': time_taken / total_questions if time_taken else None,
                'difficulty_level': quiz_data.get('difficulty', 'intermediate')
            },
            'insights': insights
        }
    
    async def _extract_concepts(self, question_text: str) -> List[str]:
        """Extract key concepts from question text using Comprehend"""
        
        try:
            response = self.comprehend.detect_key_phrases(
                Text=question_text,
                LanguageCode='en'
            )
            
            concepts = []
            for phrase in response['KeyPhrases']:
                if phrase['Score'] > 0.8:  # High confidence phrases only
                    concepts.append(phrase['Text'].lower())
            
            return concepts[:3]  # Limit to top 3 concepts
            
        except Exception as e:
            logger.warning(f"Concept extraction failed: {str(e)}")
            return []
    
    def _generate_performance_insights(
        self,
        score: float,
        concept_performance: Dict,
        time_taken: Optional[int],
        total_questions: int
    ) -> Dict[str, Any]:
        """Generate performance insights and recommendations"""
        
        insights = {
            'overall_performance': 'excellent' if score >= 90 else 'good' if score >= 70 else 'needs_improvement',
            'strengths': [],
            'areas_for_improvement': [],
            'recommendations': []
        }
        
        # Analyze concept performance
        for concept, performance in concept_performance.items():
            accuracy = performance['correct'] / performance['total']
            if accuracy >= 0.8:
                insights['strengths'].append(concept)
            elif accuracy < 0.5:
                insights['areas_for_improvement'].append(concept)
        
        # Time-based insights
        if time_taken:
            avg_time_per_question = time_taken / total_questions
            if avg_time_per_question < 30:  # Less than 30 seconds per question
                insights['recommendations'].append("Consider taking more time to read questions carefully")
            elif avg_time_per_question > 180:  # More than 3 minutes per question
                insights['recommendations'].append("Practice to improve response speed")
        
        # Score-based recommendations
        if score < 70:
            insights['recommendations'].append("Review the material and focus on weak areas")
        elif score >= 90:
            insights['recommendations'].append("Excellent work! Consider advancing to more challenging material")
        
        return insights
    
    async def _store_submission(
        self,
        user_id: str,
        quiz_id: str,
        answers: Dict,
        scoring_result: Dict,
        time_taken: Optional[int]
    ) -> str:
        """Store quiz submission with analytics"""
        
        submission_id = str(uuid.uuid4())
        
        submission_data = {
            'submission_id': submission_id,
            'quiz_id': quiz_id,
            'user_id': user_id,
            'answers': answers,
            'score': scoring_result['score'],
            'correct_answers': scoring_result['correct_answers'],
            'total_questions': scoring_result['total_questions'],
            'detailed_results': scoring_result['detailed_results'],
            'analytics': scoring_result['analytics'],
            'performance_insights': scoring_result['insights'],
            'time_taken': time_taken,
            'submitted_at': datetime.utcnow().isoformat(),
            'enhanced_analytics': True
        }
        
        self.submissions_table.put_item(Item=submission_data)
        return submission_id
    
    async def _update_quiz_stats(self, quiz_id: str, score: float) -> None:
        """Update quiz statistics"""
        
        try:
            # Get current quiz data
            response = self.quizzes_table.get_item(Key={'quiz_id': quiz_id})
            quiz_data = response.get('Item', {})
            
            current_attempts = quiz_data.get('attempts', 0) + 1
            best_score = quiz_data.get('best_score')
            
            if best_score is None or score > best_score:
                best_score = score
            
            # Update quiz metadata
            self.quizzes_table.update_item(
                Key={'quiz_id': quiz_id},
                UpdateExpression='SET attempts = :attempts, best_score = :best_score, last_attempt = :last_attempt',
                ExpressionAttributeValues={
                    ':attempts': current_attempts,
                    ':best_score': best_score,
                    ':last_attempt': datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating quiz stats: {str(e)}")
    
    async def _update_learning_analytics(
        self,
        user_id: str,
        quiz_data: Dict,
        scoring_result: Dict
    ) -> None:
        """Update user learning analytics"""
        
        try:
            analytics_id = f"{user_id}#{quiz_data.get('topic', 'general')}"
            
            # Get existing analytics
            try:
                response = self.analytics_table.get_item(Key={'analytics_id': analytics_id})
                analytics = response.get('Item', {})
            except:
                analytics = {}
            
            # Update analytics
            total_quizzes = analytics.get('total_quizzes', 0) + 1
            total_score = analytics.get('total_score', 0) + scoring_result['score']
            average_score = total_score / total_quizzes
            
            # Update concept mastery
            concept_mastery = analytics.get('concept_mastery', {})
            for concept, performance in scoring_result['analytics']['concept_performance'].items():
                if concept not in concept_mastery:
                    concept_mastery[concept] = {'attempts': 0, 'correct': 0}
                
                concept_mastery[concept]['attempts'] += performance['total']
                concept_mastery[concept]['correct'] += performance['correct']
            
            # Store updated analytics
            updated_analytics = {
                'analytics_id': analytics_id,
                'user_id': user_id,
                'topic': quiz_data.get('topic', 'general'),
                'total_quizzes': total_quizzes,
                'total_score': total_score,
                'average_score': average_score,
                'concept_mastery': concept_mastery,
                'last_updated': datetime.utcnow().isoformat(),
                'enhanced_analytics': True
            }
            
            self.analytics_table.put_item(Item=updated_analytics)
            
        except Exception as e:
            logger.error(f"Error updating learning analytics: {str(e)}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for enhanced quiz generation with multi-language support
    """
    
    try:
        # Parse Bedrock Agent request
        api_path = event.get('apiPath', '')
        request_body = event.get('requestBody', {})
        
        if isinstance(request_body, str):
            body = json.loads(request_body)
        else:
            body = request_body.get('content', {}) if request_body else {}
        
        # Initialize enhanced quiz generator
        quiz_generator = EnhancedQuizGenerator()
        
        # Route based on API path
        if api_path == '/generate-quiz':
            return await handle_quiz_generation(quiz_generator, body)
        elif api_path == '/submit-quiz':
            return await handle_quiz_submission(quiz_generator, body)
        else:
            return create_bedrock_response(400, {"error": "Invalid API path"})
        
    except Exception as e:
        logger.error(f"Error in enhanced quiz handler: {str(e)}")
        return create_bedrock_response(500, {"error": str(e)})


async def handle_quiz_generation(quiz_generator: EnhancedQuizGenerator, body: Dict) -> Dict:
    """Handle quiz generation request"""
    
    topic = body.get('topic', '').strip()
    difficulty = body.get('difficulty', 'intermediate')
    question_count = body.get('question_count', 5)
    target_language = body.get('target_language', 'en')
    user_id = body.get('user_id', 'anonymous')
    rag_context = body.get('rag_context', [])
    
    if not topic:
        return create_bedrock_response(400, {"error": "Topic is required"})
    
    # Validate parameters
    if difficulty not in ['beginner', 'intermediate', 'advanced']:
        difficulty = 'intermediate'
    
    if not isinstance(question_count, int) or question_count < 1 or question_count > 20:
        question_count = 5
    
    # Generate quiz
    result = await quiz_generator.generate_quiz_with_translation(
        topic=topic,
        difficulty=difficulty,
        question_count=question_count,
        target_language=target_language,
        user_id=user_id,
        rag_context=rag_context
    )
    
    return create_bedrock_response(200, result)


async def handle_quiz_submission(quiz_generator: EnhancedQuizGenerator, body: Dict) -> Dict:
    """Handle quiz submission request"""
    
    user_id = body.get('user_id', 'anonymous')
    quiz_id = body.get('quiz_id', '').strip()
    answers = body.get('answers', {})
    time_taken = body.get('time_taken')
    
    if not quiz_id or not answers:
        return create_bedrock_response(400, {"error": "Quiz ID and answers are required"})
    
    # Submit quiz
    result = await quiz_generator.submit_quiz_with_analytics(
        user_id=user_id,
        quiz_id=quiz_id,
        answers=answers,
        time_taken=time_taken
    )
    
    return create_bedrock_response(200, result)


def create_bedrock_response(status_code: int, body: Dict) -> Dict:
    """Create Bedrock Agent action group response"""
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'EnhancedQuizGenerator',
            'apiPath': '/generate-quiz',
            'httpMethod': 'POST',
            'httpStatusCode': status_code,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(body)
                }
            }
        }
    }