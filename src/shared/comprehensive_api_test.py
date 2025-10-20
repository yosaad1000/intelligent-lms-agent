"""
Comprehensive API testing script
Runs all API tests including validation, error scenarios, and performance tests
"""

import json
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from api_testing import APITester, create_test_data_generator
from api_documentation import APIDocumentationGenerator


class ComprehensiveAPITestRunner:
    """Run comprehensive API tests with detailed reporting"""
    
    def __init__(self, base_url: str, auth_token: str = None, output_dir: str = "test_results"):
        """
        Initialize test runner
        
        Args:
            base_url: Base URL for API testing
            auth_token: Authentication token
            output_dir: Directory for test results
        """
        self.base_url = base_url
        self.auth_token = auth_token
        self.output_dir = output_dir
        self.tester = APITester(base_url, auth_token)
        self.test_data = create_test_data_generator()
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all comprehensive API tests
        
        Returns:
            Complete test results summary
        """
        
        print(f"Starting comprehensive API tests for {self.base_url}")
        print(f"Results will be saved to {self.output_dir}/")
        print("-" * 60)
        
        results = {
            "test_run_info": {
                "start_time": datetime.utcnow().isoformat(),
                "base_url": self.base_url,
                "auth_provided": bool(self.auth_token)
            },
            "test_categories": {}
        }
        
        # Run test categories
        test_categories = [
            ("basic_functionality", self._test_basic_functionality),
            ("validation_errors", self._test_validation_errors),
            ("authentication", self._test_authentication),
            ("error_scenarios", self._test_error_scenarios),
            ("security_scenarios", self._test_security_scenarios),
            ("performance", self._test_performance),
            ("edge_cases", self._test_edge_cases)
        ]
        
        for category_name, test_function in test_categories:
            print(f"\nRunning {category_name.replace('_', ' ').title()} Tests...")
            try:
                category_results = test_function()
                results["test_categories"][category_name] = category_results
                
                passed = sum(1 for r in category_results["tests"] if r["success"])
                total = len(category_results["tests"])
                print(f"  {category_name}: {passed}/{total} passed")
                
            except Exception as e:
                print(f"  ERROR in {category_name}: {str(e)}")
                results["test_categories"][category_name] = {
                    "error": str(e),
                    "tests": []
                }
        
        # Calculate overall summary
        results["summary"] = self._calculate_summary(results["test_categories"])
        results["test_run_info"]["end_time"] = datetime.utcnow().isoformat()
        
        # Save results
        self._save_results(results)
        
        # Print summary
        self._print_summary(results["summary"])
        
        return results 
   
    def _test_basic_functionality(self) -> Dict[str, Any]:
        """Test basic API functionality"""
        
        tests = []
        
        # Health check
        result = self.tester.test_health_endpoint()
        tests.append({
            "name": "Health Check",
            "success": result.success,
            "status_code": result.status_code,
            "duration_ms": result.duration_ms,
            "error": result.error_message
        })
        
        # Chat functionality
        for message in self.test_data["chat_messages"][:3]:  # Test first 3 messages
            result = self.tester.test_chat_endpoint(message)
            tests.append({
                "name": f"Chat: {message[:30]}...",
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        # File upload functionality
        for file_data in self.test_data["file_data"][:2]:  # Test first 2 files
            result = self.tester.test_file_upload_endpoint(
                file_data["filename"], 
                file_data["file_size"]
            )
            tests.append({
                "name": f"File Upload: {file_data['filename']}",
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        # Get files
        result = self.tester.test_get_files_endpoint()
        tests.append({
            "name": "Get Files",
            "success": result.success,
            "status_code": result.status_code,
            "duration_ms": result.duration_ms,
            "error": result.error_message
        })
        
        return {
            "category": "Basic Functionality",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_validation_errors(self) -> Dict[str, Any]:
        """Test validation error scenarios"""
        
        tests = []
        
        # Run validation tests from APITester
        validation_results = self.tester.test_validation_errors()
        
        for result in validation_results:
            tests.append({
                "name": result.test_name,
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        return {
            "category": "Validation Errors",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_authentication(self) -> Dict[str, Any]:
        """Test authentication scenarios"""
        
        tests = []
        
        # Run authentication tests from APITester
        auth_results = self.tester.test_authentication_errors()
        
        for result in auth_results:
            tests.append({
                "name": result.test_name,
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        return {
            "category": "Authentication",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_error_scenarios(self) -> Dict[str, Any]:
        """Test error scenarios"""
        
        tests = []
        
        # Run error scenario tests from APITester
        error_results = self.tester.test_error_scenarios()
        
        for result in error_results:
            tests.append({
                "name": result.test_name,
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        return {
            "category": "Error Scenarios",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_security_scenarios(self) -> Dict[str, Any]:
        """Test security scenarios"""
        
        tests = []
        
        # Test SQL injection attempts
        sql_injections = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--"
        ]
        
        for injection in sql_injections:
            from api_testing import APIEndpoint
            endpoint = APIEndpoint("POST", "/api/chat", "SQL Injection Test", expected_status=200)
            result = self.tester.test_endpoint(endpoint, data={
                "message": injection,
                "user_id": "test-user"
            })
            
            tests.append({
                "name": f"SQL Injection: {injection[:20]}...",
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        # Test XSS attempts
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')"
        ]
        
        for payload in xss_payloads:
            from api_testing import APIEndpoint
            endpoint = APIEndpoint("POST", "/api/chat", "XSS Test", expected_status=200)
            result = self.tester.test_endpoint(endpoint, data={
                "message": payload,
                "user_id": "test-user"
            })
            
            tests.append({
                "name": f"XSS: {payload[:20]}...",
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        return {
            "category": "Security Scenarios",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_performance(self) -> Dict[str, Any]:
        """Test performance scenarios"""
        
        tests = []
        
        # Test chat endpoint performance
        from api_testing import APIEndpoint
        chat_endpoint = APIEndpoint("POST", "/api/chat", "Chat Performance Test")
        perf_results = self.tester.test_performance(
            chat_endpoint,
            data={"message": "Performance test message", "user_id": "test-user"},
            iterations=5
        )
        
        tests.append({
            "name": "Chat Performance",
            "success": perf_results["success_rate"] >= 80,  # 80% success rate threshold
            "avg_duration_ms": perf_results["avg_duration_ms"],
            "success_rate": perf_results["success_rate"],
            "iterations": perf_results["iterations"]
        })
        
        # Test health endpoint performance
        health_endpoint = APIEndpoint("GET", "/health", "Health Performance Test", auth_required=False)
        health_perf = self.tester.test_performance(
            health_endpoint,
            iterations=10
        )
        
        tests.append({
            "name": "Health Performance",
            "success": health_perf["avg_duration_ms"] < 1000,  # Under 1 second
            "avg_duration_ms": health_perf["avg_duration_ms"],
            "success_rate": health_perf["success_rate"],
            "iterations": health_perf["iterations"]
        })
        
        return {
            "category": "Performance",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _test_edge_cases(self) -> Dict[str, Any]:
        """Test edge cases"""
        
        tests = []
        
        # Test with Unicode characters
        unicode_messages = [
            "Hello 世界",  # Chinese
            "Здравствуй мир",  # Russian
            "مرحبا بالعالم",  # Arabic
            "🚀 Rocket emoji test",  # Emoji
        ]
        
        for message in unicode_messages:
            result = self.tester.test_chat_endpoint(message)
            tests.append({
                "name": f"Unicode: {message[:20]}...",
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        # Test boundary values
        boundary_tests = [
            # Minimum message length
            {"message": "a", "user_id": "test-user"},
            # Maximum allowed message length (just under limit)
            {"message": "x" * 4999, "user_id": "test-user"},
        ]
        
        for i, data in enumerate(boundary_tests):
            from api_testing import APIEndpoint
            endpoint = APIEndpoint("POST", "/api/chat", f"Boundary Test {i+1}")
            result = self.tester.test_endpoint(endpoint, data=data)
            
            tests.append({
                "name": f"Boundary Test {i+1}",
                "success": result.success,
                "status_code": result.status_code,
                "duration_ms": result.duration_ms,
                "error": result.error_message
            })
        
        return {
            "category": "Edge Cases",
            "tests": tests,
            "passed": sum(1 for t in tests if t["success"]),
            "total": len(tests)
        }
    
    def _calculate_summary(self, test_categories: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall test summary"""
        
        total_tests = 0
        total_passed = 0
        category_summaries = {}
        
        for category_name, category_data in test_categories.items():
            if "error" in category_data:
                category_summaries[category_name] = {
                    "status": "error",
                    "error": category_data["error"]
                }
                continue
            
            tests = category_data.get("tests", [])
            passed = sum(1 for t in tests if t.get("success", False))
            total = len(tests)
            
            total_tests += total
            total_passed += passed
            
            category_summaries[category_name] = {
                "passed": passed,
                "total": total,
                "success_rate": (passed / total * 100) if total > 0 else 0
            }
        
        return {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "overall_success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "categories": category_summaries
        }
    
    def _save_results(self, results: Dict[str, Any]) -> None:
        """Save test results to files"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results as JSON
        detailed_path = os.path.join(self.output_dir, f"api_test_results_{timestamp}.json")
        with open(detailed_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save summary as text
        summary_path = os.path.join(self.output_dir, f"api_test_summary_{timestamp}.txt")
        with open(summary_path, 'w') as f:
            f.write("API Test Summary\n")
            f.write("=" * 50 + "\n\n")
            
            summary = results["summary"]
            f.write(f"Overall Results: {summary['total_passed']}/{summary['total_tests']} passed ")
            f.write(f"({summary['overall_success_rate']:.1f}%)\n\n")
            
            f.write("Category Breakdown:\n")
            for category, data in summary["categories"].items():
                if "error" in data:
                    f.write(f"  {category}: ERROR - {data['error']}\n")
                else:
                    f.write(f"  {category}: {data['passed']}/{data['total']} ")
                    f.write(f"({data['success_rate']:.1f}%)\n")
        
        print(f"\nResults saved:")
        print(f"  Detailed: {detailed_path}")
        print(f"  Summary: {summary_path}")
    
    def _print_summary(self, summary: Dict[str, Any]) -> None:
        """Print test summary to console"""
        
        print("\n" + "=" * 60)
        print("API TEST SUMMARY")
        print("=" * 60)
        
        print(f"Overall Results: {summary['total_passed']}/{summary['total_tests']} passed ", end="")
        print(f"({summary['overall_success_rate']:.1f}%)")
        
        print("\nCategory Breakdown:")
        for category, data in summary["categories"].items():
            category_display = category.replace('_', ' ').title()
            if "error" in data:
                print(f"  {category_display:20} ERROR - {data['error']}")
            else:
                print(f"  {category_display:20} {data['passed']:3}/{data['total']:3} ", end="")
                print(f"({data['success_rate']:5.1f}%)")
        
        # Overall status
        if summary['overall_success_rate'] >= 90:
            status = "EXCELLENT"
        elif summary['overall_success_rate'] >= 80:
            status = "GOOD"
        elif summary['overall_success_rate'] >= 70:
            status = "ACCEPTABLE"
        else:
            status = "NEEDS IMPROVEMENT"
        
        print(f"\nOverall Status: {status}")
        print("=" * 60)


def main():
    """Main function for command-line usage"""
    
    parser = argparse.ArgumentParser(description="Run comprehensive API tests")
    parser.add_argument("--url", required=True, help="Base URL for API testing")
    parser.add_argument("--token", help="Authentication token")
    parser.add_argument("--output", default="test_results", help="Output directory for results")
    parser.add_argument("--generate-docs", action="store_true", help="Generate API documentation")
    
    args = parser.parse_args()
    
    # Generate documentation if requested
    if args.generate_docs:
        print("Generating API documentation...")
        doc_generator = APIDocumentationGenerator("docs")
        doc_files = doc_generator.generate_all_documentation()
        print("Documentation generated successfully!")
        return
    
    # Run comprehensive tests
    test_runner = ComprehensiveAPITestRunner(
        base_url=args.url,
        auth_token=args.token,
        output_dir=args.output
    )
    
    results = test_runner.run_all_tests()
    
    # Exit with appropriate code
    success_rate = results["summary"]["overall_success_rate"]
    exit_code = 0 if success_rate >= 80 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()