# Voice Interview Microservice - MVP Requirements

## Overview
**Priority: HIGH (Build Fifth - Demo Differentiator)**  
Voice-based interview system using Amazon Transcribe + Bedrock Agent for testing student knowledge through spoken responses.

## Core User Stories

### US-VOICE-001: Voice Interview Session
**As a** student  
**I want to** participate in voice-based interviews about my study topics  
**So that** I can practice explaining concepts verbally and get AI feedback

#### Acceptance Criteria (EARS Format)
1. WHEN a student starts voice interview THEN the system SHALL provide recording interface with clear instructions
2. WHEN student records response THEN the system SHALL capture audio and display recording status
3. WHEN recording stops THEN the system SHALL upload audio to S3 for processing
4. WHEN audio is uploaded THEN the system SHALL initiate Amazon Transcribe processing
5. IF recording fails THEN the system SHALL allow re-recording with error explanation

### US-VOICE-002: Intelligent Response Analysis
**As a** student  
**I want to** get detailed feedback on my spoken explanations  
**So that** I can improve my verbal communication and understanding

#### Acceptance Criteria
1. WHEN transcription completes THEN the system SHALL analyze response using Bedrock Agent
2. WHEN analysis is done THEN the system SHALL evaluate content accuracy and clarity
3. WHEN evaluation completes THEN the system SHALL provide detailed feedback with scores
4. WHEN feedback is ready THEN the system SHALL suggest improvements and strengths
5. IF transcription is unclear THEN the system SHALL request clearer re-recording

### US-VOICE-003: Adaptive Interview Questions
**As a** student  
**I want to** receive follow-up questions based on my responses  
**So that** the interview adapts to my knowledge level

#### Acceptance Criteria
1. WHEN student gives good answer THEN the system SHALL ask more challenging follow-up questions
2. WHEN student struggles THEN the system SHALL provide hints and simpler questions
3. WHEN interview progresses THEN the system SHALL track concept mastery in real-time
4. WHEN interview ends THEN the system SHALL provide comprehensive performance summary

## Technical Implementation (Fast Build)

### Technology Stack
- **Frontend**: Gradio Audio component for recording
- **Speech Processing**: Amazon Transcribe for speech-to-text
- **AI Analysis**: Bedrock Agent for response evaluation
- **Storage**: S3 for audio files, DynamoDB for interview sessions
- **Real-time**: WebSocket for live feedback (optional for MVP)

### MVP Implementation
```python
import gradio as gr
import boto3
import json
import uuid
import time
from datetime import datetime
import os

class VoiceInterviewAgent:
    def __init__(self):
        self.transcribe = boto3.client('transcribe')
        self.s3 = boto3.client('s3')
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        self.dynamodb = boto3.resource('dynamodb')
        
        # Configuration
        self.bucket_name = 'lms-voice-interviews'
        self.agent_id = 'your-bedrock-agent-id'
        self.table_name = 'voice-interview-sessions'
        
        # Interview questions by difficulty
        self.interview_questions = {
            "beginner": [
                "Can you explain what thermodynamics is in simple terms?",
                "What happens when you heat up water?",
                "Why do ice cubes melt?"
            ],
            "intermediate": [
                "Explain the first law of thermodynamics and give an example",
                "How does entropy relate to energy transformations?",
                "Describe the difference between heat and temperature"
            ],
            "advanced": [
                "Analyze the thermodynamic efficiency of a heat engine",
                "Explain how the second law of thermodynamics applies to biological systems",
                "Discuss the relationship between entropy and information theory"
            ]
        }
    
    def start_interview_session(self, topic="general", difficulty="intermediate", user_id="demo_user"):
        """Start a new voice interview session"""
        try:
            session_id = str(uuid.uuid4())
            
            # Create session record
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'topic': topic,
                'difficulty': difficulty,
                'start_time': datetime.now().isoformat(),
                'status': 'active',
                'current_question': 0,
                'responses': []
            }
            
            # Store in DynamoDB (simplified for MVP)
            # In production, use actual DynamoDB table
            
            # Get first question
            questions = self.interview_questions.get(difficulty, self.interview_questions["intermediate"])
            first_question = questions[0] if questions else "Tell me about your understanding of this topic."
            
            return {
                'session_id': session_id,
                'question': first_question,
                'status': 'ready',
                'instructions': f"🎤 Voice Interview Started!\n\n**Topic**: {topic}\n**Difficulty**: {difficulty.title()}\n\n**Question 1**: {first_question}\n\nClick 'Start Recording' and explain your answer clearly."
            }
            
        except Exception as e:
            return {
                'error': f"Failed to start interview: {str(e)}",
                'status': 'error'
            }
    
    def process_voice_response(self, audio_file, session_id, question, user_id="demo_user"):
        """Process recorded voice response"""
        if not audio_file:
            return {
                'error': 'No audio file provided',
                'status': 'error'
            }
        
        try:
            # 1. Upload audio to S3
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_key = f"interviews/{user_id}/{session_id}/{timestamp}_response.wav"
            
            self.s3.upload_file(audio_file, self.bucket_name, audio_key)
            
            # 2. Transcribe audio
            transcription = self._transcribe_audio(audio_key, session_id)
            
            if transcription.get('error'):
                return transcription
            
            # 3. Analyze response with Bedrock Agent
            analysis = self._analyze_response_with_ai(
                transcription['text'], 
                question, 
                session_id,
                user_id
            )
            
            # 4. Generate next question or conclude interview
            next_question = self._get_next_question(analysis, session_id)
            
            return {
                'transcription': transcription['text'],
                'analysis': analysis,
                'next_question': next_question,
                'status': 'completed'
            }
            
        except Exception as e:
            return {
                'error': f"Processing failed: {str(e)}",
                'status': 'error'
            }
    
    def _transcribe_audio(self, audio_s3_key, session_id):
        """Transcribe audio using Amazon Transcribe"""
        try:
            job_name = f"interview-{session_id}-{int(time.time())}"
            
            # Start transcription job
            self.transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={
                    'MediaFileUri': f's3://{self.bucket_name}/{audio_s3_key}'
                },
                MediaFormat='wav',
                LanguageCode='en-US'
            )
            
            # Wait for completion (simplified for MVP)
            # In production, use async processing
            max_wait = 60  # seconds
            wait_time = 0
            
            while wait_time < max_wait:
                response = self.transcribe.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                if status == 'COMPLETED':
                    # Get transcript
                    transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    # For MVP, return simulated transcription
                    return {
                        'text': "This is a simulated transcription of the student's response about thermodynamics concepts...",
                        'confidence': 0.95,
                        'job_name': job_name
                    }
                elif status == 'FAILED':
                    return {'error': 'Transcription failed'}
                
                time.sleep(2)
                wait_time += 2
            
            return {'error': 'Transcription timeout'}
            
        except Exception as e:
            return {'error': f'Transcription error: {str(e)}'}
    
    def _analyze_response_with_ai(self, transcription, question, session_id, user_id):
        """Analyze student response using Bedrock Agent"""
        try:
            analysis_prompt = f"""
            Analyze this student's voice response to an interview question:
            
            Question: {question}
            Student Response: {transcription}
            
            Provide analysis in this format:
            - Content Accuracy (0-100): How correct is the information?
            - Clarity (0-100): How clear and well-structured is the explanation?
            - Completeness (0-100): How thoroughly did they answer?
            - Key Concepts Identified: List main concepts mentioned
            - Strengths: What did they do well?
            - Areas for Improvement: What could be better?
            - Overall Score (0-100): Combined assessment
            - Suggested Follow-up: What to ask next?
            """
            
            # Call Bedrock Agent (simplified for MVP)
            # In production, use actual agent call
            
            # Simulated analysis for MVP
            analysis = {
                'content_accuracy': 85,
                'clarity': 78,
                'completeness': 82,
                'overall_score': 82,
                'concepts_identified': ['thermodynamics', 'energy conservation', 'heat transfer'],
                'strengths': [
                    'Good understanding of basic concepts',
                    'Clear pronunciation and pace',
                    'Used relevant examples'
                ],
                'improvements': [
                    'Could explain the mathematical relationships',
                    'Add more real-world applications',
                    'Define technical terms more precisely'
                ],
                'suggested_followup': 'Can you explain how this concept applies in everyday life?'
            }
            
            return analysis
            
        except Exception as e:
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _get_next_question(self, analysis, session_id):
        """Generate next interview question based on performance"""
        try:
            overall_score = analysis.get('overall_score', 0)
            
            if overall_score >= 80:
                # Student doing well, ask harder question
                return {
                    'question': analysis.get('suggested_followup', 'Can you elaborate on that concept?'),
                    'difficulty': 'increased',
                    'reasoning': 'Great answer! Let\'s explore this deeper.'
                }
            elif overall_score >= 60:
                # Student okay, continue at same level
                return {
                    'question': 'Can you give me a specific example of this concept?',
                    'difficulty': 'same',
                    'reasoning': 'Good explanation. Can you provide an example?'
                }
            else:
                # Student struggling, provide easier question or hint
                return {
                    'question': 'Let me ask this in a simpler way: What do you think happens to energy in this process?',
                    'difficulty': 'decreased',
                    'reasoning': 'Let\'s break this down into simpler parts.'
                }
                
        except Exception as e:
            return {
                'question': 'Thank you for your response. Can you tell me more about this topic?',
                'difficulty': 'same',
                'reasoning': 'Continue the discussion.'
            }
    
    def get_interview_summary(self, session_id, user_id="demo_user"):
        """Get comprehensive interview performance summary"""
        try:
            # In production, retrieve from DynamoDB
            # For MVP, return sample summary
            
            summary = {
                'session_id': session_id,
                'total_questions': 3,
                'average_score': 82,
                'time_spent': '8 minutes',
                'concepts_covered': ['thermodynamics', 'energy conservation', 'entropy'],
                'performance_trend': 'improving',
                'strengths': [
                    'Strong foundational understanding',
                    'Good verbal communication skills',
                    'Appropriate use of examples'
                ],
                'recommendations': [
                    'Practice explaining mathematical relationships',
                    'Study more advanced applications',
                    'Work on technical vocabulary'
                ],
                'next_steps': [
                    'Review advanced thermodynamics concepts',
                    'Practice with more complex scenarios',
                    'Take a quiz on related topics'
                ]
            }
            
            return summary
            
        except Exception as e:
            return {'error': f'Failed to generate summary: {str(e)}'}

# Gradio Interface
def create_voice_interview_interface():
    voice_agent = VoiceInterviewAgent()
    
    with gr.Blocks() as voice_app:
        gr.Markdown("# 🎤 Voice Interview Assistant")
        gr.Markdown("Practice explaining concepts verbally and get AI-powered feedback!")
        
        # Session state
        session_state = gr.State({})
        
        # Interview setup
        with gr.Row():
            topic_input = gr.Textbox(
                label="Interview Topic",
                value="Thermodynamics",
                placeholder="Enter the subject you want to practice"
            )
            difficulty_select = gr.Dropdown(
                choices=["beginner", "intermediate", "advanced"],
                value="intermediate",
                label="Difficulty Level"
            )
            start_btn = gr.Button("🚀 Start Interview", variant="primary")
        
        # Interview status
        interview_status = gr.Textbox(
            label="Interview Status",
            lines=4,
            interactive=False,
            placeholder="Click 'Start Interview' to begin..."
        )
        
        # Voice recording section
        with gr.Column(visible=False) as recording_section:
            current_question = gr.Textbox(
                label="Current Question",
                lines=2,
                interactive=False
            )
            
            audio_input = gr.Audio(
                label="Record Your Answer",
                type="filepath"
            )
            
            submit_response_btn = gr.Button("📤 Submit Response", variant="primary")
        
        # Response analysis
        with gr.Column(visible=False) as analysis_section:
            gr.Markdown("### 📊 Response Analysis")
            
            transcription_display = gr.Textbox(
                label="What You Said",
                lines=3,
                interactive=False
            )
            
            analysis_display = gr.JSON(
                label="Detailed Feedback"
            )
            
            next_question_display = gr.Textbox(
                label="Next Question",
                lines=2,
                interactive=False
            )
            
            continue_btn = gr.Button("Continue Interview", variant="secondary")
            finish_btn = gr.Button("Finish Interview", variant="outline")
        
        # Interview summary
        summary_display = gr.JSON(
            label="Interview Summary",
            visible=False
        )
        
        # Event handlers
        def start_interview(topic, difficulty):
            result = voice_agent.start_interview_session(topic, difficulty)
            
            if 'error' in result:
                return result['error'], gr.update(visible=False), gr.update(visible=False), result
            
            return (
                result['instructions'],
                gr.update(visible=True),
                gr.update(visible=False),
                result
            )
        
        def process_response(audio_file, session_data):
            if not session_data or not audio_file:
                return "Please record your response first.", gr.update(visible=False), "", {}, ""
            
            result = voice_agent.process_voice_response(
                audio_file,
                session_data.get('session_id'),
                session_data.get('question')
            )
            
            if 'error' in result:
                return result['error'], gr.update(visible=False), "", {}, ""
            
            return (
                "Response processed successfully!",
                gr.update(visible=True),
                result['transcription'],
                result['analysis'],
                result['next_question']['question']
            )
        
        def finish_interview(session_data):
            if not session_data:
                return {}
            
            summary = voice_agent.get_interview_summary(session_data.get('session_id'))
            return summary
        
        # Wire up events
        start_btn.click(
            fn=start_interview,
            inputs=[topic_input, difficulty_select],
            outputs=[interview_status, recording_section, analysis_section, session_state]
        )
        
        submit_response_btn.click(
            fn=process_response,
            inputs=[audio_input, session_state],
            outputs=[interview_status, analysis_section, transcription_display, analysis_display, next_question_display]
        )
        
        finish_btn.click(
            fn=finish_interview,
            inputs=[session_state],
            outputs=[summary_display]
        )
    
    return voice_app

# Example usage
if __name__ == "__main__":
    app = create_voice_interview_interface()
    app.launch(server_port=7861, share=False)
```

## Testing Strategy
1. **Unit Test**: Test transcription and analysis with sample audio
2. **Integration Test**: Complete interview flow from recording to feedback
3. **Manual Test**: Conduct actual voice interviews via Gradio
4. **Performance Test**: Test with different audio qualities and lengths

## Dependencies
- Authentication service (for user identification)
- File Processor service (for topic-specific questions from uploaded content)
- AI Chat service (shares Bedrock Agent configuration)

## Delivery Timeline
- **Day 3**: Basic audio recording and transcription
- **Day 4**: AI analysis and feedback system
- **Day 5**: Adaptive questioning and interview flow
- **Day 6**: Integration testing and demo preparation

## Demo Value
- **Unique Feature**: Voice interviews differentiate from typical chatbots
- **AI Sophistication**: Shows advanced Bedrock Agent capabilities
- **Real-time Processing**: Demonstrates AWS Transcribe integration
- **Adaptive Intelligence**: Questions adapt based on student performance