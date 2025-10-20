"""
Multi-Language Translation Service
Provides comprehensive translation capabilities with round-trip validation
"""

import json
import boto3
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class TranslationService:
    """Advanced translation service with round-trip validation"""
    
    def __init__(self):
        """Initialize AWS services"""
        self.translate = boto3.client('translate')
        self.comprehend = boto3.client('comprehend')
        self.dynamodb = boto3.resource('dynamodb')
        
        # Translation history table
        self.translations_table = self.dynamodb.Table('lms-translations')
        
        # Supported languages
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'ru': 'Russian'
        }
    
    async def detect_and_translate(
        self,
        text: str,
        target_language: str,
        user_id: str = None,
        enable_round_trip: bool = True
    ) -> Dict[str, Any]:
        """Detect source language and translate with validation"""
        
        try:
            # Detect source language
            source_language = await self._detect_language_advanced(text)
            
            # Skip translation if already in target language
            if source_language == target_language:
                return {
                    "success": True,
                    "original_text": text,
                    "translated_text": text,
                    "source_language": source_language,
                    "target_language": target_language,
                    "translation_needed": False,
                    "confidence": 1.0
                }
            
            # Perform translation
            translated_text = await self._translate_text(text, source_language, target_language)
            
            # Round-trip validation if enabled
            round_trip_data = {}
            if enable_round_trip:
                round_trip_data = await self._perform_round_trip_validation(
                    text, translated_text, source_language, target_language
                )
            
            # Store translation history
            translation_id = await self._store_translation_history(
                user_id, text, translated_text, source_language, target_language, round_trip_data
            )
            
            return {
                "success": True,
                "translation_id": translation_id,
                "original_text": text,
                "translated_text": translated_text,
                "source_language": source_language,
                "target_language": target_language,
                "source_language_name": self.supported_languages.get(source_language, source_language),
                "target_language_name": self.supported_languages.get(target_language, target_language),
                "translation_needed": True,
                "round_trip_validation": round_trip_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in detect_and_translate: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "TRANSLATION_FAILED"
            }
    
    async def batch_translate(
        self,
        texts: List[str],
        target_language: str,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Translate multiple texts efficiently"""
        
        try:
            results = []
            
            for i, text in enumerate(texts):
                if not text.strip():
                    results.append({
                        "index": i,
                        "success": False,
                        "error": "Empty text"
                    })
                    continue
                
                # Translate individual text
                translation_result = await self.detect_and_translate(
                    text, target_language, user_id, enable_round_trip=False
                )
                
                results.append({
                    "index": i,
                    **translation_result
                })
            
            # Calculate batch statistics
            successful_translations = len([r for r in results if r.get("success", False)])
            
            return {
                "success": True,
                "batch_size": len(texts),
                "successful_translations": successful_translations,
                "failed_translations": len(texts) - successful_translations,
                "results": results,
                "target_language": target_language,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in batch_translate: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "BATCH_TRANSLATION_FAILED"
            }
    
    async def translate_educational_content(
        self,
        content: Dict[str, Any],
        target_language: str,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Translate structured educational content (quizzes, lessons, etc.)"""
        
        try:
            translated_content = content.copy()
            translation_log = []
            
            # Translate based on content type
            content_type = content.get('type', 'general')
            
            if content_type == 'quiz':
                translated_content = await self._translate_quiz_content(
                    content, target_language, translation_log
                )
            elif content_type == 'lesson':
                translated_content = await self._translate_lesson_content(
                    content, target_language, translation_log
                )
            else:
                # Generic content translation
                translated_content = await self._translate_generic_content(
                    content, target_language, translation_log
                )
            
            # Store educational content translation
            translation_id = await self._store_educational_translation(
                user_id, content, translated_content, target_language, translation_log
            )
            
            return {
                "success": True,
                "translation_id": translation_id,
                "original_content": content,
                "translated_content": translated_content,
                "target_language": target_language,
                "content_type": content_type,
                "translation_log": translation_log,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error translating educational content: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "EDUCATIONAL_TRANSLATION_FAILED"
            }
    
    async def _detect_language_advanced(self, text: str) -> str:
        """Advanced language detection with confidence scoring"""
        
        try:
            response = self.comprehend.detect_dominant_language(Text=text)
            
            if response['Languages']:
                # Get the most confident language
                languages = sorted(response['Languages'], key=lambda x: x['Score'], reverse=True)
                detected_lang = languages[0]['LanguageCode']
                confidence = languages[0]['Score']
                
                logger.info(f"Detected language: {detected_lang} (confidence: {confidence:.3f})")
                
                # Only use detection if confidence is reasonable
                if confidence > 0.7:
                    return detected_lang
                else:
                    logger.warning(f"Low confidence language detection: {confidence:.3f}")
            
            return "en"  # Default to English
            
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}")
            return "en"
    
    async def _translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using Amazon Translate"""
        
        try:
            # Handle unsupported language codes
            if source_lang not in self.supported_languages:
                source_lang = "en"
            if target_lang not in self.supported_languages:
                target_lang = "en"
            
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
    
    async def _perform_round_trip_validation(
        self,
        original_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str
    ) -> Dict[str, Any]:
        """Perform round-trip translation to validate quality"""
        
        try:
            # Translate back to original language
            back_translated = await self._translate_text(translated_text, target_lang, source_lang)
            
            # Calculate similarity (simple word overlap for now)
            similarity_score = self._calculate_text_similarity(original_text, back_translated)
            
            # Determine quality assessment
            if similarity_score > 0.8:
                quality = "excellent"
            elif similarity_score > 0.6:
                quality = "good"
            elif similarity_score > 0.4:
                quality = "fair"
            else:
                quality = "poor"
            
            return {
                "back_translated_text": back_translated,
                "similarity_score": similarity_score,
                "quality_assessment": quality,
                "validation_performed": True
            }
            
        except Exception as e:
            logger.warning(f"Round-trip validation failed: {str(e)}")
            return {
                "validation_performed": False,
                "error": str(e)
            }
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity based on word overlap"""
        
        try:
            # Simple word-based similarity
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 and not words2:
                return 1.0
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {str(e)}")
            return 0.0
    
    async def _translate_quiz_content(
        self,
        quiz_content: Dict,
        target_language: str,
        translation_log: List
    ) -> Dict[str, Any]:
        """Translate quiz-specific content"""
        
        translated_quiz = quiz_content.copy()
        
        # Translate quiz title
        if 'quiz_title' in quiz_content:
            source_lang = await self._detect_language_advanced(quiz_content['quiz_title'])
            translated_title = await self._translate_text(
                quiz_content['quiz_title'], source_lang, target_language
            )
            translated_quiz['quiz_title'] = translated_title
            translation_log.append(f"Translated quiz title from {source_lang}")
        
        # Translate questions
        if 'questions' in quiz_content:
            translated_questions = []
            
            for question in quiz_content['questions']:
                translated_question = question.copy()
                
                # Translate question text
                if 'question' in question:
                    source_lang = await self._detect_language_advanced(question['question'])
                    translated_question['question'] = await self._translate_text(
                        question['question'], source_lang, target_language
                    )
                
                # Translate options
                if 'options' in question:
                    translated_options = {}
                    for key, option_text in question['options'].items():
                        source_lang = await self._detect_language_advanced(option_text)
                        translated_options[key] = await self._translate_text(
                            option_text, source_lang, target_language
                        )
                    translated_question['options'] = translated_options
                
                # Translate explanation
                if 'explanation' in question:
                    source_lang = await self._detect_language_advanced(question['explanation'])
                    translated_question['explanation'] = await self._translate_text(
                        question['explanation'], source_lang, target_language
                    )
                
                translated_questions.append(translated_question)
            
            translated_quiz['questions'] = translated_questions
            translation_log.append(f"Translated {len(translated_questions)} questions")
        
        return translated_quiz
    
    async def _translate_lesson_content(
        self,
        lesson_content: Dict,
        target_language: str,
        translation_log: List
    ) -> Dict[str, Any]:
        """Translate lesson-specific content"""
        
        translated_lesson = lesson_content.copy()
        
        # Translate lesson title
        if 'title' in lesson_content:
            source_lang = await self._detect_language_advanced(lesson_content['title'])
            translated_lesson['title'] = await self._translate_text(
                lesson_content['title'], source_lang, target_language
            )
            translation_log.append(f"Translated lesson title from {source_lang}")
        
        # Translate lesson content/body
        if 'content' in lesson_content:
            source_lang = await self._detect_language_advanced(lesson_content['content'])
            translated_lesson['content'] = await self._translate_text(
                lesson_content['content'], source_lang, target_language
            )
            translation_log.append(f"Translated lesson content from {source_lang}")
        
        # Translate objectives
        if 'objectives' in lesson_content and isinstance(lesson_content['objectives'], list):
            translated_objectives = []
            for objective in lesson_content['objectives']:
                source_lang = await self._detect_language_advanced(objective)
                translated_objectives.append(
                    await self._translate_text(objective, source_lang, target_language)
                )
            translated_lesson['objectives'] = translated_objectives
            translation_log.append(f"Translated {len(translated_objectives)} objectives")
        
        return translated_lesson
    
    async def _translate_generic_content(
        self,
        content: Dict,
        target_language: str,
        translation_log: List
    ) -> Dict[str, Any]:
        """Translate generic content structure"""
        
        translated_content = {}
        
        for key, value in content.items():
            if isinstance(value, str) and value.strip():
                # Translate string values
                source_lang = await self._detect_language_advanced(value)
                translated_content[key] = await self._translate_text(
                    value, source_lang, target_language
                )
                translation_log.append(f"Translated field '{key}' from {source_lang}")
            elif isinstance(value, list):
                # Translate list items if they are strings
                translated_list = []
                for item in value:
                    if isinstance(item, str) and item.strip():
                        source_lang = await self._detect_language_advanced(item)
                        translated_list.append(
                            await self._translate_text(item, source_lang, target_language)
                        )
                    else:
                        translated_list.append(item)
                translated_content[key] = translated_list
            else:
                # Keep non-string values as-is
                translated_content[key] = value
        
        return translated_content
    
    async def _store_translation_history(
        self,
        user_id: str,
        original_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        round_trip_data: Dict
    ) -> str:
        """Store translation in history table"""
        
        try:
            translation_id = f"{user_id or 'anonymous'}#{int(datetime.utcnow().timestamp())}"
            
            translation_item = {
                'translation_id': translation_id,
                'user_id': user_id or 'anonymous',
                'original_text': original_text[:1000],  # Limit size
                'translated_text': translated_text[:1000],
                'source_language': source_lang,
                'target_language': target_lang,
                'round_trip_validation': round_trip_data,
                'translation_type': 'text',
                'created_at': datetime.utcnow().isoformat(),
                'ttl': int((datetime.utcnow().timestamp() + 86400 * 30))  # 30 days TTL
            }
            
            self.translations_table.put_item(Item=translation_item)
            return translation_id
            
        except Exception as e:
            logger.error(f"Error storing translation history: {str(e)}")
            return f"error_{int(datetime.utcnow().timestamp())}"
    
    async def _store_educational_translation(
        self,
        user_id: str,
        original_content: Dict,
        translated_content: Dict,
        target_language: str,
        translation_log: List
    ) -> str:
        """Store educational content translation"""
        
        try:
            translation_id = f"{user_id or 'anonymous'}#edu#{int(datetime.utcnow().timestamp())}"
            
            translation_item = {
                'translation_id': translation_id,
                'user_id': user_id or 'anonymous',
                'original_content': json.dumps(original_content)[:2000],  # Limit size
                'translated_content': json.dumps(translated_content)[:2000],
                'target_language': target_language,
                'translation_log': translation_log,
                'translation_type': 'educational_content',
                'content_type': original_content.get('type', 'general'),
                'created_at': datetime.utcnow().isoformat(),
                'ttl': int((datetime.utcnow().timestamp() + 86400 * 90))  # 90 days TTL
            }
            
            self.translations_table.put_item(Item=translation_item)
            return translation_id
            
        except Exception as e:
            logger.error(f"Error storing educational translation: {str(e)}")
            return f"error_edu_{int(datetime.utcnow().timestamp())}"
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return self.supported_languages.copy()
    
    async def get_translation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get user's translation history"""
        
        try:
            response = self.translations_table.query(
                IndexName='user-id-index',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Error getting translation history: {str(e)}")
            return []


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for translation service
    """
    
    try:
        # Parse Bedrock Agent request
        api_path = event.get('apiPath', '')
        request_body = event.get('requestBody', {})
        
        if isinstance(request_body, str):
            body = json.loads(request_body)
        else:
            body = request_body.get('content', {}) if request_body else {}
        
        # Initialize translation service
        translation_service = TranslationService()
        
        # Route based on API path
        if api_path == '/translate':
            return await handle_translation(translation_service, body)
        elif api_path == '/batch-translate':
            return await handle_batch_translation(translation_service, body)
        elif api_path == '/translate-educational':
            return await handle_educational_translation(translation_service, body)
        elif api_path == '/supported-languages':
            return handle_supported_languages(translation_service)
        else:
            return create_bedrock_response(400, {"error": "Invalid API path"})
        
    except Exception as e:
        logger.error(f"Error in translation handler: {str(e)}")
        return create_bedrock_response(500, {"error": str(e)})


async def handle_translation(translation_service: TranslationService, body: Dict) -> Dict:
    """Handle single text translation"""
    
    text = body.get('text', '').strip()
    target_language = body.get('target_language', 'en')
    user_id = body.get('user_id', 'anonymous')
    enable_round_trip = body.get('enable_round_trip', True)
    
    if not text:
        return create_bedrock_response(400, {"error": "Text is required"})
    
    result = await translation_service.detect_and_translate(
        text=text,
        target_language=target_language,
        user_id=user_id,
        enable_round_trip=enable_round_trip
    )
    
    return create_bedrock_response(200, result)


async def handle_batch_translation(translation_service: TranslationService, body: Dict) -> Dict:
    """Handle batch text translation"""
    
    texts = body.get('texts', [])
    target_language = body.get('target_language', 'en')
    user_id = body.get('user_id', 'anonymous')
    
    if not texts or not isinstance(texts, list):
        return create_bedrock_response(400, {"error": "Texts array is required"})
    
    result = await translation_service.batch_translate(
        texts=texts,
        target_language=target_language,
        user_id=user_id
    )
    
    return create_bedrock_response(200, result)


async def handle_educational_translation(translation_service: TranslationService, body: Dict) -> Dict:
    """Handle educational content translation"""
    
    content = body.get('content', {})
    target_language = body.get('target_language', 'en')
    user_id = body.get('user_id', 'anonymous')
    
    if not content or not isinstance(content, dict):
        return create_bedrock_response(400, {"error": "Content object is required"})
    
    result = await translation_service.translate_educational_content(
        content=content,
        target_language=target_language,
        user_id=user_id
    )
    
    return create_bedrock_response(200, result)


def handle_supported_languages(translation_service: TranslationService) -> Dict:
    """Handle supported languages request"""
    
    languages = translation_service.get_supported_languages()
    
    return create_bedrock_response(200, {
        "supported_languages": languages,
        "total_languages": len(languages)
    })


def create_bedrock_response(status_code: int, body: Dict) -> Dict:
    """Create Bedrock Agent action group response"""
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'TranslationService',
            'apiPath': '/translate',
            'httpMethod': 'POST',
            'httpStatusCode': status_code,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(body)
                }
            }
        }
    }