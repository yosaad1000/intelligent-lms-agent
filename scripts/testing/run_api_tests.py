#!/usr/bin/env python3
"""
Run comprehensive API tests
Executes all API tests including validation, error scenarios, and performance tests
"""

import os
import sys
import argparse
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from shared.comprehensive_api_test import ComprehensiveAPITestRunner


def main():
    """Run comprehensive API tests"""
    
    parser = argparse.ArgumentParser(description="Run comprehensive API tests")
    parser.add_argument("--url", required=True, help="Base URL for API testing (e.g., https://api.lms.example.com)")
    parser.add_argument("--token", help="Authentication token (JWT)")
    parser.add_argument("--output-dir", default="test_results", help="Output directory for test results")
    parser.add_argument("--categories", nargs="+", 
                       choices=["basic", "validation", "auth", "errors", "security", "performance", "edge"],
                       help="Test categories to run (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    
    args = parser.parse_args()
    
    print("LMS API Comprehensive Test Runner")
    print("=" * 50)
    print(f"Target URL: {args.url}")
    print(f"Authentication: {'Provided' if args.token else 'Not provided (testing without auth)'}")
    print(f"Output directory: {args.output_dir}")
    print(f"Test categories: {args.categories if args.categories else 'All'}")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print()
    
    # Validate URL format
    if not args.url.startswith(('http://', 'https://')):
        print("ERROR: URL must start with http:// or https://")
        sys.exit(1)
    
    # Initialize test runner
    try:
        test_runner = ComprehensiveAPITestRunner(
            base_url=args.url,
            auth_token=args.token,
            output_dir=args.output_dir
        )
    except Exception as e:
        print(f"ERROR: Failed to initialize test runner: {str(e)}")
        sys.exit(1)
    
    # Run tests
    try:
        if args.categories:
            # Run specific categories
            results = run_specific_categories(test_runner, args.categories, args.verbose, args.fail_fast)
        else:
            # Run all tests
            results = test_runner.run_all_tests()
        
        # Determine exit code based on results
        success_rate = results["summary"]["overall_success_rate"]
        
        if success_rate >= 90:
            print(f"\n🎉 EXCELLENT: {success_rate:.1f}% success rate")
            exit_code = 0
        elif success_rate >= 80:
            print(f"\n✅ GOOD: {success_rate:.1f}% success rate")
            exit_code = 0
        elif success_rate >= 70:
            print(f"\n⚠️  ACCEPTABLE: {success_rate:.1f}% success rate")
            exit_code = 0
        else:
            print(f"\n❌ NEEDS IMPROVEMENT: {success_rate:.1f}% success rate")
            exit_code = 1
        
        # Show recommendations
        show_recommendations(results["summary"])
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: Test run failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def run_specific_categories(test_runner, categories, verbose, fail_fast):
    """Run specific test categories"""
    
    category_map = {
        "basic": test_runner._test_basic_functionality,
        "validation": test_runner._test_validation_errors,
        "auth": test_runner._test_authentication,
        "errors": test_runner._test_error_scenarios,
        "security": test_runner._test_security_scenarios,
        "performance": test_runner._test_performance,
        "edge": test_runner._test_edge_cases
    }
    
    results = {
        "test_run_info": {
            "start_time": datetime.utcnow().isoformat(),
            "base_url": test_runner.base_url,
            "auth_provided": bool(test_runner.auth_token),
            "categories_requested": categories
        },
        "test_categories": {}
    }
    
    for category in categories:
        if category not in category_map:
            print(f"WARNING: Unknown category '{category}', skipping...")
            continue
        
        print(f"\nRunning {category.title()} Tests...")
        
        try:
            category_results = category_map[category]()
            results["test_categories"][category] = category_results
            
            passed = sum(1 for r in category_results["tests"] if r["success"])
            total = len(category_results["tests"])
            print(f"  {category}: {passed}/{total} passed")
            
            if fail_fast and passed < total:
                print(f"FAIL-FAST: Stopping due to failures in {category} category")
                break
                
        except Exception as e:
            print(f"  ERROR in {category}: {str(e)}")
            results["test_categories"][category] = {
                "error": str(e),
                "tests": []
            }
            
            if fail_fast:
                print(f"FAIL-FAST: Stopping due to error in {category} category")
                break
    
    # Calculate summary
    results["summary"] = test_runner._calculate_summary(results["test_categories"])
    results["test_run_info"]["end_time"] = datetime.utcnow().isoformat()
    
    # Save results
    test_runner._save_results(results)
    
    return results


def show_recommendations(summary):
    """Show recommendations based on test results"""
    
    print("\n" + "=" * 50)
    print("RECOMMENDATIONS")
    print("=" * 50)
    
    success_rate = summary["overall_success_rate"]
    categories = summary["categories"]
    
    recommendations = []
    
    # Overall recommendations
    if success_rate < 70:
        recommendations.append("🔧 Critical issues detected - immediate attention required")
    elif success_rate < 80:
        recommendations.append("⚠️  Some issues detected - review and fix recommended")
    elif success_rate < 90:
        recommendations.append("✨ Minor issues detected - optimization opportunities available")
    else:
        recommendations.append("🎯 Excellent API health - maintain current quality")
    
    # Category-specific recommendations
    for category, data in categories.items():
        if "error" in data:
            recommendations.append(f"🚨 {category.replace('_', ' ').title()}: Fix critical errors")
        elif data.get("success_rate", 0) < 70:
            recommendations.append(f"🔧 {category.replace('_', ' ').title()}: Needs significant improvement")
        elif data.get("success_rate", 0) < 90:
            recommendations.append(f"⚠️  {category.replace('_', ' ').title()}: Minor issues to address")
    
    # Performance recommendations
    if "performance" in categories:
        perf_data = categories["performance"]
        if perf_data.get("success_rate", 0) < 80:
            recommendations.append("🚀 Performance: Optimize response times and reliability")
    
    # Security recommendations
    if "security_scenarios" in categories:
        sec_data = categories["security_scenarios"]
        if sec_data.get("success_rate", 0) < 100:
            recommendations.append("🔒 Security: Review and strengthen security measures")
    
    # Show recommendations
    if recommendations:
        for rec in recommendations:
            print(f"  {rec}")
    else:
        print("  🎉 No specific recommendations - API is performing excellently!")
    
    print("\n📚 For detailed analysis, check the generated test report files.")
    print("🔧 For troubleshooting, refer to the API testing guide.")


if __name__ == "__main__":
    main()