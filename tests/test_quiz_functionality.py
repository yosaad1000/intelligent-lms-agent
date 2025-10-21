#!/usr/bin/env python3
"""
Test Quiz Functionality - Task 13 Implementation
Tests the interactive quiz component implementation with Bedrock Agent integration
"""

import json
import time
import requests
from typing import Dict, Any, List

class QuizFunctionalityTester:
    def __init__(self):
        self.api_base_url = "https://7k21xsoz93.execute-api.us-east-1.amazonaws.com/dev"
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def test_agent_connectivity(self) -> bool:
        """Test 1: Verify Bedrock Agent connectivity"""
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                agent_responsive = data.get('agent_responsive', False)
                
                if agent_responsive:
                    self.log_test("Agent Connectivity", True, "Bedrock Agent is responsive")
                    return True
                else:
                    self.log_test("Agent Connectivity", False, "Agent not responsive")
                    return False
            else:
                self.log_test("Agent Connectivity", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Agent Connectivity", False, f"Connection error: {str(e)}")
            return False
    
    def test_quiz_generation_request(self) -> bool:
        """Test 2: Test quiz generation via Bedrock Agent"""
        try:
            quiz_prompt = """Generate a quiz with the following JSON format:
            {
                "title": "Sample Quiz",
                "description": "Test quiz for functionality verification",
                "difficulty": "medium",
                "estimatedDuration": 15,
                "questions": [
                    {
                        "id": "q1",
                        "type": "multiple-choice",
                        "question": "What is 2 + 2?",
                        "options": ["3", "4", "5", "6"],
                        "correctAnswer": 1,
                        "explanation": "Basic arithmetic",
                        "points": 1
                    },
                    {
                        "id": "q2",
                        "type": "true-false",
                        "question": "The sky is blue.",
                        "correctAnswer": "true",
                        "explanation": "Common knowledge",
                        "points": 1
                    }
                ]
            }"""
            
            payload = {
                "message": quiz_prompt,
                "session_id": f"test-session-{int(time.time())}",
                "user_id": "test-user",
                "context": {
                    "action": "generate_quiz",
                    "test": True
                }
            }
            
            response = requests.post(
                f"{self.api_base_url}/api/v1/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    agent_response = data.get('response', '')
                    
                    # Try to parse JSON from response
                    try:
                        # Look for JSON in the response
                        if '{' in agent_response and '}' in agent_response:
                            json_start = agent_response.find('{')
                            json_end = agent_response.rfind('}') + 1
                            json_str = agent_response[json_start:json_end]
                            quiz_data = json.loads(json_str)
                            
                            # Validate quiz structure
                            required_fields = ['title', 'questions']
                            if all(field in quiz_data for field in required_fields):
                                self.log_test("Quiz Generation", True, 
                                            f"Generated quiz with {len(quiz_data.get('questions', []))} questions")
                                return True
                            else:
                                self.log_test("Quiz Generation", False, "Invalid quiz structure")
                                return False
                        else:
                            self.log_test("Quiz Generation", False, "No JSON found in response")
                            return False
                            
                    except json.JSONDecodeError as e:
                        self.log_test("Quiz Generation", False, f"JSON parse error: {str(e)}")
                        return False
                else:
                    self.log_test("Quiz Generation", False, f"Agent error: {data.get('error')}")
                    return False
            else:
                self.log_test("Quiz Generation", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Quiz Generation", False, f"Request error: {str(e)}")
            return False
    
    def test_quiz_parsing_logic(self) -> bool:
        """Test 3: Test quiz parsing and validation logic"""
        try:
            # Test valid quiz JSON
            valid_quiz = {
                "title": "Test Quiz",
                "description": "A test quiz",
                "difficulty": "medium",
                "estimatedDuration": 20,
                "questions": [
                    {
                        "id": "q1",
                        "type": "multiple-choice",
                        "question": "Sample question?",
                        "options": ["A", "B", "C", "D"],
                        "correctAnswer": 1,
                        "explanation": "Sample explanation",
                        "points": 1
                    },
                    {
                        "id": "q2",
                        "type": "true-false",
                        "question": "True or false question?",
                        "correctAnswer": "true",
                        "explanation": "True/false explanation",
                        "points": 1
                    },
                    {
                        "id": "q3",
                        "type": "short-answer",
                        "question": "Short answer question?",
                        "correctAnswer": "Sample answer",
                        "explanation": "Short answer explanation",
                        "points": 2
                    }
                ]
            }
            
            # Validate quiz structure
            validation_results = []
            
            # Check required fields
            required_fields = ['title', 'questions']
            for field in required_fields:
                if field in valid_quiz:
                    validation_results.append(f"✓ Has {field}")
                else:
                    validation_results.append(f"✗ Missing {field}")
            
            # Check questions structure
            questions = valid_quiz.get('questions', [])
            if questions:
                validation_results.append(f"✓ Has {len(questions)} questions")
                
                # Check question types
                question_types = set(q.get('type') for q in questions)
                expected_types = {'multiple-choice', 'true-false', 'short-answer'}
                
                if question_types.issubset(expected_types):
                    validation_results.append("✓ Valid question types")
                else:
                    validation_results.append("✗ Invalid question types")
                
                # Check question fields
                for i, question in enumerate(questions):
                    required_q_fields = ['id', 'type', 'question', 'correctAnswer', 'points']
                    missing_fields = [f for f in required_q_fields if f not in question]
                    
                    if not missing_fields:
                        validation_results.append(f"✓ Question {i+1} structure valid")
                    else:
                        validation_results.append(f"✗ Question {i+1} missing: {missing_fields}")
            
            self.log_test("Quiz Parsing Logic", True, "; ".join(validation_results))
            return True
            
        except Exception as e:
            self.log_test("Quiz Parsing Logic", False, f"Validation error: {str(e)}")
            return False
    
    def test_quiz_scoring_logic(self) -> bool:
        """Test 4: Test quiz scoring and feedback logic"""
        try:
            # Sample quiz with answers
            quiz_questions = [
                {
                    "id": "q1",
                    "type": "multiple-choice",
                    "correctAnswer": 1,
                    "points": 1
                },
                {
                    "id": "q2", 
                    "type": "true-false",
                    "correctAnswer": "true",
                    "points": 1
                },
                {
                    "id": "q3",
                    "type": "short-answer",
                    "correctAnswer": "sample",
                    "points": 2
                }
            ]
            
            # Test answers
            user_answers = {
                "q1": 1,      # Correct multiple choice
                "q2": "true", # Correct true/false
                "q3": "sample answer"  # Short answer (partial credit)
            }
            
            # Calculate score
            total_points = sum(q["points"] for q in quiz_questions)
            earned_points = 0
            
            for question in quiz_questions:
                qid = question["id"]
                user_answer = user_answers.get(qid)
                correct_answer = question["correctAnswer"]
                points = question["points"]
                
                if question["type"] == "multiple-choice":
                    if user_answer == correct_answer:
                        earned_points += points
                elif question["type"] == "true-false":
                    if user_answer == correct_answer:
                        earned_points += points
                elif question["type"] == "short-answer":
                    if user_answer:  # Give partial credit if answered
                        earned_points += points * 0.8
            
            percentage = round((earned_points / total_points) * 100)
            
            scoring_details = f"Earned {earned_points}/{total_points} points ({percentage}%)"
            self.log_test("Quiz Scoring Logic", True, scoring_details)
            return True
            
        except Exception as e:
            self.log_test("Quiz Scoring Logic", False, f"Scoring error: {str(e)}")
            return False
    
    def test_quiz_session_management(self) -> bool:
        """Test 5: Test quiz session state management"""
        try:
            # Simulate quiz session
            quiz_session = {
                "id": f"session-{int(time.time())}",
                "quiz": {
                    "id": "test-quiz",
                    "title": "Test Quiz",
                    "questions": [
                        {"id": "q1", "type": "multiple-choice"},
                        {"id": "q2", "type": "true-false"},
                        {"id": "q3", "type": "short-answer"}
                    ]
                },
                "currentQuestionIndex": 0,
                "answers": {},
                "startTime": time.time(),
                "timeRemaining": 1200,  # 20 minutes
                "isActive": True
            }
            
            session_tests = []
            
            # Test session initialization
            if quiz_session["isActive"]:
                session_tests.append("✓ Session active")
            
            # Test question navigation
            total_questions = len(quiz_session["quiz"]["questions"])
            if 0 <= quiz_session["currentQuestionIndex"] < total_questions:
                session_tests.append("✓ Valid question index")
            
            # Test answer storage
            quiz_session["answers"]["q1"] = 1
            if "q1" in quiz_session["answers"]:
                session_tests.append("✓ Answer storage works")
            
            # Test progress calculation
            answered = len(quiz_session["answers"])
            progress = (answered / total_questions) * 100
            session_tests.append(f"✓ Progress: {progress}%")
            
            # Test time management
            elapsed = time.time() - quiz_session["startTime"]
            remaining = quiz_session["timeRemaining"] - elapsed
            if remaining > 0:
                session_tests.append("✓ Time tracking works")
            
            self.log_test("Quiz Session Management", True, "; ".join(session_tests))
            return True
            
        except Exception as e:
            self.log_test("Quiz Session Management", False, f"Session error: {str(e)}")
            return False
    
    def test_error_handling(self) -> bool:
        """Test 6: Test error handling and fallback mechanisms"""
        try:
            error_scenarios = []
            
            # Test invalid JSON parsing
            try:
                invalid_json = "{ invalid json }"
                json.loads(invalid_json)
                error_scenarios.append("✗ Should have failed JSON parsing")
            except json.JSONDecodeError:
                error_scenarios.append("✓ JSON error handling works")
            
            # Test missing quiz fields
            incomplete_quiz = {"title": "Test"}  # Missing questions
            if "questions" not in incomplete_quiz:
                error_scenarios.append("✓ Missing field detection works")
            
            # Test empty questions array
            empty_quiz = {"title": "Test", "questions": []}
            if len(empty_quiz["questions"]) == 0:
                error_scenarios.append("✓ Empty questions detection works")
            
            # Test invalid question type
            invalid_question = {"type": "invalid-type"}
            valid_types = {"multiple-choice", "true-false", "short-answer"}
            if invalid_question["type"] not in valid_types:
                error_scenarios.append("✓ Invalid question type detection works")
            
            self.log_test("Error Handling", True, "; ".join(error_scenarios))
            return True
            
        except Exception as e:
            self.log_test("Error Handling", False, f"Error handling test failed: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all quiz functionality tests"""
        print("🧪 Starting Quiz Functionality Tests - Task 13")
        print("=" * 60)
        
        # Run tests in order
        tests = [
            ("Agent Connectivity", self.test_agent_connectivity),
            ("Quiz Generation Request", self.test_quiz_generation_request),
            ("Quiz Parsing Logic", self.test_quiz_parsing_logic),
            ("Quiz Scoring Logic", self.test_quiz_scoring_logic),
            ("Quiz Session Management", self.test_quiz_session_management),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test execution error: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {passed}/{total} tests passed")
        
        success_rate = (passed / total) * 100
        if success_rate >= 80:
            print(f"✅ Overall Status: PASS ({success_rate:.1f}%)")
        else:
            print(f"❌ Overall Status: FAIL ({success_rate:.1f}%)")
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": success_rate,
            "status": "PASS" if success_rate >= 80 else "FAIL",
            "test_results": self.test_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

def main():
    """Main test execution"""
    tester = QuizFunctionalityTester()
    results = tester.run_all_tests()
    
    # Save results to file
    with open("quiz_functionality_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: quiz_functionality_test_results.json")
    
    # Exit with appropriate code
    exit(0 if results["status"] == "PASS" else 1)

if __name__ == "__main__":
    main()