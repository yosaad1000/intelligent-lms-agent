# Quiz Generator Microservice - MVP Requirements

## Overview
**Priority: MEDIUM (Build Fourth)**  
Generate personalized quizzes from uploaded content using Bedrock Agent + Gradio for interactive testing.

## Core User Stories

### US-QUIZ-001: Generate Quiz from Notes
**As a** student  
**I want to** generate quizzes from my uploaded notes  
**So that** I can test my understanding

#### Acceptance Criteria (EARS Format)
1. WHEN a student requests a quiz THEN the system SHALL generate questions from their uploaded content
2. WHEN quiz is generated THEN the system SHALL provide multiple-choice questions with 4 options
3. WHEN questions are displayed THEN the system SHALL show clear question text and answer choices
4. WHEN student selects answers THEN the system SHALL track responses for scoring

### US-QUIZ-002: Instant Feedback
**As a** student  
**I want to** get immediate feedback on my answers  
**So that** I can learn from my mistakes

#### Acceptance Criteria
1. WHEN student submits quiz THEN the system SHALL calculate score immediately
2. WHEN scoring is complete THEN the system SHALL show correct/incorrect answers
3. WHEN answer is wrong THEN the system SHALL provide explanation of correct answer
4. WHEN quiz is finished THEN the system SHALL display overall performance summary

## Technical Implementation (Fast Build)

### Technology Stack
- **Frontend**: Gradio interactive components (Radio, Button, HTML)
- **AI Engine**: Bedrock Agent for question generation
- **Content Source**: Student's Knowledge Base content
- **Scoring**: Simple Python logic for immediate feedback

### MVP Implementation
```python
import gradio as gr
import boto3
import json
import random
from datetime import datetime

class FastQuizGenerator:
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent-runtime')
        self.bedrock_runtime = boto3.client('bedrock-runtime')
        self.agent_id = 'your-bedrock-agent-id'
        
    def generate_quiz(self, topic="", difficulty="medium", num_questions=5, user_id="demo_user"):
        """Generate quiz using Bedrock Agent"""
        try:
            # Prepare prompt for quiz generation
            quiz_prompt = self._create_quiz_prompt(topic, difficulty, num_questions, user_id)
            
            # Call Bedrock Agent or direct LLM for quiz generation
            response = self._call_bedrock_for_quiz(quiz_prompt)
            
            # Parse response into structured quiz format
            quiz_data = self._parse_quiz_response(response)
            
            return quiz_data
            
        except Exception as e:
            return {
                "error": f"Failed to generate quiz: {str(e)}",
                "questions": []
            }
    
    def _create_quiz_prompt(self, topic, difficulty, num_questions, user_id):
        """Create prompt for quiz generation"""
        base_prompt = f"""
        Generate a {difficulty} level quiz with {num_questions} multiple choice questions.
        Topic focus: {topic if topic else "general content from uploaded materials"}
        
        Format each question as JSON:
        {{
            "question": "Question text here?",
            "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": 0,
            "explanation": "Why this answer is correct"
        }}
        
        Make questions relevant to the student's uploaded study materials.
        Ensure questions test understanding, not just memorization.
        """
        return base_prompt
    
    def _call_bedrock_for_quiz(self, prompt):
        """Call Bedrock to generate quiz content"""
        try:
            # For MVP, use direct Bedrock Runtime call
            # In production, this would use the Bedrock Agent
            
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
            
            response = self.bedrock_runtime.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            # Fallback to sample quiz for MVP
            return self._get_sample_quiz()
    
    def _parse_quiz_response(self, response_text):
        """Parse AI response into quiz structure"""
        try:
            # For MVP, return structured sample quiz
            # In production, parse the actual AI response
            return self._get_sample_quiz_structured()
        except:
            return self._get_sample_quiz_structured()
    
    def _get_sample_quiz_structured(self):
        """Sample quiz for MVP testing"""
        return {
            "questions": [
                {
                    "id": 1,
                    "question": "What is the main principle of thermodynamics?",
                    "options": [
                        "A) Energy cannot be created or destroyed",
                        "B) Heat always flows from cold to hot",
                        "C) Entropy always decreases",
                        "D) Work is always 100% efficient"
                    ],
                    "correct_answer": 0,
                    "explanation": "The first law of thermodynamics states that energy cannot be created or destroyed, only transformed from one form to another."
                },
                {
                    "id": 2,
                    "question": "Which of the following best describes entropy?",
                    "options": [
                        "A) A measure of energy",
                        "B) A measure of disorder",
                        "C) A measure of temperature",
                        "D) A measure of pressure"
                    ],
                    "correct_answer": 1,
                    "explanation": "Entropy is a measure of disorder or randomness in a system. It tends to increase in isolated systems."
                }
            ]
        }
    
    def calculate_score(self, quiz_data, user_answers):
        """Calculate quiz score and provide feedback"""
        if not quiz_data or "questions" not in quiz_data:
            return {"error": "Invalid quiz data"}
        
        questions = quiz_data["questions"]
        total_questions = len(questions)
        correct_answers = 0
        detailed_results = []
        
        for i, question in enumerate(questions):
            user_answer = user_answers.get(f"q_{i}", -1)
            correct_answer = question["correct_answer"]
            is_correct = user_answer == correct_answer
            
            if is_correct:
                correct_answers += 1
            
            detailed_results.append({
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question["explanation"],
                "options": question["options"]
            })
        
        score_percentage = (correct_answers / total_questions) * 100
        
        return {
            "score": score_percentage,
            "correct": correct_answers,
            "total": total_questions,
            "results": detailed_results,
            "performance": self._get_performance_message(score_percentage)
        }
    
    def _get_performance_message(self, score):
        """Get encouraging performance message"""
        if score >= 90:
            return "🎉 Excellent! You have a strong understanding of the material!"
        elif score >= 80:
            return "👍 Great job! You're doing well with most concepts."
        elif score >= 70:
            return "📚 Good effort! Review the explanations to improve further."
        elif score >= 60:
            return "💪 Keep studying! Focus on the areas you missed."
        else:
            return "📖 More practice needed. Review your notes and try again!"

# Gradio Interface
def create_quiz_interface():
    quiz_gen = FastQuizGenerator()
    
    with gr.Blocks() as quiz_app:
        gr.Markdown("# 📝 Interactive Quiz Generator")
        gr.Markdown("Generate personalized quizzes from your uploaded study materials!")
        
        # Quiz generation controls
        with gr.Row():
            topic_input = gr.Textbox(
                label="Topic (optional)",
                placeholder="Leave blank for general quiz from all your notes"
            )
            difficulty_select = gr.Dropdown(
                choices=["easy", "medium", "hard"],
                value="medium",
                label="Difficulty Level"
            )
            num_questions = gr.Slider(
                minimum=3,
                maximum=10,
                value=5,
                step=1,
                label="Number of Questions"
            )
        
        generate_btn = gr.Button("🎯 Generate Quiz", variant="primary", size="lg")
        
        # Quiz display area
        quiz_container = gr.HTML(visible=False)
        
        # Quiz state management
        quiz_state = gr.State({})
        user_answers = gr.State({})
        
        # Results area
        results_container = gr.HTML(visible=False)
        
        def display_quiz(topic, difficulty, num_questions):
            """Generate and display quiz"""
            quiz_data = quiz_gen.generate_quiz(topic, difficulty, int(num_questions))
            
            if "error" in quiz_data:
                return quiz_data["error"], quiz_data, {}, gr.update(visible=False), gr.update(visible=False)
            
            # Generate HTML for interactive quiz
            quiz_html = self._generate_quiz_html(quiz_data)
            
            return quiz_html, quiz_data, {}, gr.update(visible=True), gr.update(visible=False)
        
        def _generate_quiz_html(self, quiz_data):
            """Generate HTML for quiz display"""
            html = "<div style='padding: 20px;'>"
            html += "<h3>📋 Your Personalized Quiz</h3>"
            
            for i, question in enumerate(quiz_data["questions"]):
                html += f"<div style='margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px;'>"
                html += f"<p><strong>Question {i+1}:</strong> {question['question']}</p>"
                
                for j, option in enumerate(question["options"]):
                    html += f"<label style='display: block; margin: 5px 0; cursor: pointer;'>"
                    html += f"<input type='radio' name='q_{i}' value='{j}' onchange='updateAnswer({i}, {j})'> {option}"
                    html += "</label>"
                
                html += "</div>"
            
            html += "<button onclick='submitQuiz()' style='background: #007bff; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-top: 20px;'>Submit Quiz 📤</button>"
            html += "</div>"
            
            # Add JavaScript for answer tracking
            html += """
            <script>
            let userAnswers = {};
            function updateAnswer(questionId, answerId) {
                userAnswers['q_' + questionId] = answerId;
            }
            function submitQuiz() {
                // This would trigger the scoring function
                alert('Quiz submitted! Calculating score...');
            }
            </script>
            """
            
            return html
        
        # Event handlers
        generate_btn.click(
            fn=display_quiz,
            inputs=[topic_input, difficulty_select, num_questions],
            outputs=[quiz_container, quiz_state, user_answers, quiz_container, results_container]
        )
    
    return quiz_app
```

## Testing Strategy
1. **Unit Test**: Test quiz generation with different topics and difficulties
2. **Integration Test**: Generate quiz from actual uploaded content
3. **Manual Test**: Take quizzes via Gradio interface
4. **Scoring Test**: Verify correct calculation of scores and feedback

## Dependencies
- File Processor service (for content to generate questions from)
- AI Chat service (shares Bedrock Agent configuration)

## Delivery Timeline
- **Day 1**: Basic quiz generation structure
- **Day 2**: Gradio interface for quiz taking
- **Day 3**: Scoring and feedback system
- **Day 4**: Integration with uploaded content and testing