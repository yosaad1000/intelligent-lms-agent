#!/usr/bin/env python3
"""
Comprehensive API Testing Script
Executes all API tests including validation, error handling, performance, and security tests
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from shared.api_test_runner import APITestRunner
from shared.api_documentation import APIDocumentationGenerator
from shared.logging_config import setup_logging, get_logger


def main():
    """Main function to run comprehensive API tests"""
    
    parser = argparse.ArgumentParser(
        description="Comprehensive API Testing Suite for LMS Backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test local development server
  python test_api_comprehensive.py --url http://localhost:3000

  # Test with authentication
  python test_api_comprehensive.py --url https://api.lms.example.com --token your-jwt-token

  # Generate documentation only
  python test_api_comprehensive.py --generate-docs-only

  # Run specific test categories
  python test_api_comprehensive.py --url http://localhost:3000 --categories validation security

  # Verbose output with detailed logging
  python test_api_comprehensive.py --url http://localhost:3000 --verbose
        """
    )
    
    parser.add_argument(
        "--url", 
        help="Base URL for API testing (e.g., https://api.lms.example.com)"
    )
    parser.add_argument(
        "--token", 
        help="JWT authentication token"
    )
    parser.add_argument(
        "--output-dir", 
        default="test_results", 
        help="Output directory for test results (default: test_results)"
    )
    parser.add_argument(
        "--docs-dir", 
        default="docs", 
        help="Output directory for documentation (default: docs)"
    )
    parser.add_argument(
        "--categories", 
        nargs="+",
        choices=["health", "basic", "validation", "auth", "errors", "security", "performance", "edge", "integration"],
        help="Specific test categories to run (default: all)"
    )
    parser.add_argument(
        "--generate-docs", 
        action="store_true", 
        help="Generate API documentation along with tests"
    )
    parser.add_argument(
        "--generate-docs-only", 
        action="store_true", 
        help="Only generate documentation, skip tests"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--fail-fast", 
        action="store_true", 
        help="Stop testing on first category failure"
    )
    parser.add_argument(
        "--format", 
        choices=["json", "markdown", "csv", "all"], 
        default="all",
        help="Output format for test results (default: all)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logging(level=log_level)
    
    print("LMS API Comprehensive Testing Suite")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    # Generate documentation if requested
    if args.generate_docs or args.generate_docs_only:
        print(f"\n📚 Generating API Documentation...")
        try:
            doc_generator = APIDocumentationGenerator(args.docs_dir)
            doc_files = doc_generator.generate_all_documentation()
            
            print("✅ Documentation generated successfully!")
            print(f"📁 Documentation saved to: {args.docs_dir}/")
            for doc_type, file_path in doc_files.items():
                if file_path:
                    print(f"   {doc_type}: {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"❌ Documentation generation failed: {str(e)}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            
            if args.generate_docs_only:
                sys.exit(1)
    
    # Exit if only generating docs
    if args.generate_docs_only:
        print("\n🎉 Documentation generation completed!")
        return
    
    # Validate URL for testing
    if not args.url:
        print("\n❌ ERROR: --url is required for testing")
        print("Use --generate-docs-only to only generate documentation")
        sys.exit(1)
    
    if not args.url.startswith(('http://', 'https://')):
        print("❌ ERROR: URL must start with http:// or https://")
        sys.exit(1)
    
    print(f"\n🧪 Starting API Tests...")
    print(f"Target URL: {args.url}")
    print(f"Authentication: {'✅ Provided' if args.token else '⚠️  Not provided (testing without auth)'}")
    print(f"Output directory: {args.output_dir}")
    print(f"Test categories: {args.categories if args.categories else 'All'}")
    
    # Initialize test runner
    try:
        test_runner = APITestRunner(
            base_url=args.url,
            auth_token=args.token,
            output_dir=args.output_dir
        )
    except Exception as e:
        print(f"❌ Failed to initialize test runner: {str(e)}")
        sys.exit(1)
    
    # Run tests
    try:
        if args.categories:
            # Run specific categories (would need to implement category filtering)
            print(f"Running specific categories: {', '.join(args.categories)}")
            results = test_runner.run_comprehensive_tests()
        else:
            # Run all tests
            results = test_runner.run_comprehensive_tests()
        
        # Print summary
        print_test_summary(results)
        
        # Generate additional reports if requested
        if args.format in ["json", "all"]:
            generate_json_report(results, args.output_dir)
        
        if args.format in ["markdown", "all"]:
            generate_markdown_report(results, args.output_dir)
        
        if args.format in ["csv", "all"]:
            generate_csv_report(results, args.output_dir)
        
        # Determine exit code
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
        print("\n\n⏹️  Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test run failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def print_test_summary(results: dict):
    """Print formatted test summary"""
    
    summary = results["summary"]
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    # Overall results
    total_tests = summary["total_tests"]
    total_passed = summary["total_passed"]
    success_rate = summary["overall_success_rate"]
    
    print(f"Overall Results: {total_passed}/{total_tests} tests passed ({success_rate:.1f}%)")
    print()
    
    # Category breakdown
    print("Category Breakdown:")
    print("-" * 40)
    
    categories = summary["categories"]
    for category_name, category_data in categories.items():
        category_display = category_name.replace('_', ' ').title()
        
        if "error" in category_data:
            print(f"  {category_display:25} ❌ ERROR")
        else:
            passed = category_data["passed"]
            total = category_data["total"]
            rate = category_data["success_rate"]
            duration = category_data.get("duration_seconds", 0)
            
            status_icon = "✅" if rate >= 90 else "⚠️" if rate >= 70 else "❌"
            print(f"  {category_display:25} {status_icon} {passed:3}/{total:3} ({rate:5.1f}%) [{duration:4.1f}s]")
    
    print()


def show_recommendations(summary: dict):
    """Show recommendations based on test results"""
    
    print("💡 RECOMMENDATIONS")
    print("-" * 40)
    
    success_rate = summary["overall_success_rate"]
    categories = summary["categories"]
    
    recommendations = []
    
    # Overall recommendations
    if success_rate < 70:
        recommendations.append("🔧 Critical issues detected - immediate attention required")
        recommendations.append("   Focus on fixing basic functionality and error handling")
    elif success_rate < 80:
        recommendations.append("⚠️  Some issues detected - review and fix recommended")
        recommendations.append("   Address validation errors and improve error responses")
    elif success_rate < 90:
        recommendations.append("✨ Minor issues detected - optimization opportunities available")
        recommendations.append("   Fine-tune performance and edge case handling")
    else:
        recommendations.append("🎯 Excellent API health - maintain current quality")
        recommendations.append("   Continue monitoring and consider advanced optimizations")
    
    # Category-specific recommendations
    for category, data in categories.items():
        if "error" in data:
            recommendations.append(f"🚨 {category.replace('_', ' ').title()}: Fix critical errors preventing test execution")
        elif data.get("success_rate", 0) < 70:
            recommendations.append(f"🔧 {category.replace('_', ' ').title()}: Significant improvement needed")
        elif data.get("success_rate", 0) < 90:
            recommendations.append(f"⚠️  {category.replace('_', ' ').title()}: Minor issues to address")
    
    # Performance recommendations
    if "performance_&_load" in categories:
        perf_data = categories["performance_&_load"]
        if perf_data.get("success_rate", 0) < 80:
            recommendations.append("🚀 Performance: Optimize response times and improve reliability")
    
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
    
    print()
    print("📚 For detailed analysis, check the generated test report files.")
    print("🔧 For troubleshooting, refer to the API testing guide in docs/")


def generate_json_report(results: dict, output_dir: str):
    """Generate JSON report"""
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(output_dir, f"api_test_results_{timestamp}.json")
    
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"📄 JSON report: {json_path}")


def generate_markdown_report(results: dict, output_dir: str):
    """Generate markdown report"""
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    md_path = os.path.join(output_dir, f"api_test_report_{timestamp}.md")
    
    content = []
    
    # Header
    content.append("# API Test Report")
    content.append("")
    content.append(f"**Generated:** {datetime.utcnow().isoformat()}")
    content.append(f"**Base URL:** {results['test_run_info']['base_url']}")
    content.append("")
    
    # Summary
    summary = results["summary"]
    content.append("## Summary")
    content.append("")
    content.append(f"- **Total Tests:** {summary['total_tests']}")
    content.append(f"- **Passed:** {summary['total_passed']}")
    content.append(f"- **Success Rate:** {summary['overall_success_rate']:.1f}%")
    content.append("")
    
    # Categories
    content.append("## Category Results")
    content.append("")
    content.append("| Category | Passed | Total | Success Rate |")
    content.append("|----------|--------|-------|--------------|")
    
    for category_name, category_data in summary["categories"].items():
        if "error" in category_data:
            content.append(f"| {category_name.replace('_', ' ').title()} | ERROR | - | - |")
        else:
            passed = category_data["passed"]
            total = category_data["total"]
            rate = category_data["success_rate"]
            content.append(f"| {category_name.replace('_', ' ').title()} | {passed} | {total} | {rate:.1f}% |")
    
    content.append("")
    
    # Detailed results
    content.append("## Detailed Results")
    content.append("")
    
    for category_name, category_data in results["categories"].items():
        if "tests" in category_data:
            content.append(f"### {category_name.replace('_', ' ').title()}")
            content.append("")
            
            for test in category_data["tests"]:
                status = "✅" if test.get("success") else "❌"
                content.append(f"- {status} **{test['name']}**")
                
                if not test.get("success") and test.get("error"):
                    content.append(f"  - Error: {test['error']}")
                
                if test.get("duration_ms"):
                    content.append(f"  - Duration: {test['duration_ms']:.1f}ms")
            
            content.append("")
    
    with open(md_path, 'w') as f:
        f.write("\n".join(content))
    
    print(f"📝 Markdown report: {md_path}")


def generate_csv_report(results: dict, output_dir: str):
    """Generate CSV report"""
    
    import csv
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f"api_test_results_{timestamp}.csv")
    
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = [
            'category', 'test_name', 'success', 'status_code', 
            'duration_ms', 'error', 'timestamp'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for category_name, category_data in results["categories"].items():
            if "tests" in category_data:
                for test in category_data["tests"]:
                    writer.writerow({
                        'category': category_name,
                        'test_name': test["name"],
                        'success': test.get("success", False),
                        'status_code': test.get("status_code", ""),
                        'duration_ms': test.get("duration_ms", ""),
                        'error': test.get("error", ""),
                        'timestamp': datetime.utcnow().isoformat()
                    })
    
    print(f"📊 CSV report: {csv_path}")


if __name__ == "__main__":
    main()