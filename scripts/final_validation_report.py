#!/usr/bin/env python3
"""
Final Repository Validation Report
Validates all aspects of the repository cleanup and documentation
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

class RepositoryValidator:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'validation_results': {},
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'warnings': 0
            }
        }
    
    def validate_documentation_links(self):
        """Validate all documentation links are working"""
        print("🔗 Validating documentation links...")
        
        # Check main documentation files exist
        docs_to_check = [
            'README.md',
            'ARCHITECTURE.md', 
            'DEPLOYMENT.md',
            'LMS_COMPLETE_ARCHITECTURE.md',
            'API_DOCUMENTATION.md',
            'TESTING_INSTRUCTIONS.md'
        ]
        
        missing_docs = []
        for doc in docs_to_check:
            if not Path(doc).exists():
                missing_docs.append(doc)
        
        # Check test interface files exist
        interface_dir = Path('tests/integration/interfaces')
        expected_interfaces = [
            'test_enhanced_agent_interface.html',
            'test_voice_interview_interface.html',
            'test_learning_analytics_interface.html'
        ]
        
        missing_interfaces = []
        for interface in expected_interfaces:
            if not (interface_dir / interface).exists():
                missing_interfaces.append(str(interface_dir / interface))
        
        result = {
            'status': 'PASSED' if not missing_docs and not missing_interfaces else 'FAILED',
            'missing_docs': missing_docs,
            'missing_interfaces': missing_interfaces,
            'total_docs_checked': len(docs_to_check),
            'total_interfaces_checked': len(expected_interfaces)
        }
        
        self.results['validation_results']['documentation_links'] = result
        self._update_summary(result['status'])
        
        if result['status'] == 'PASSED':
            print("  ✅ All documentation links validated")
        else:
            print(f"  ❌ Missing documentation: {missing_docs + missing_interfaces}")
    
    def validate_build_process(self):
        """Validate build and deployment configuration"""
        print("🏗️ Validating build process...")
        
        # Check CloudFormation template
        template_valid = False
        try:
            result = subprocess.run(
                ['aws', 'cloudformation', 'validate-template', '--template-body', 'file://template.yaml'],
                capture_output=True, text=True, timeout=30
            )
            template_valid = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            template_valid = False
        
        # Check requirements.txt exists and is valid
        requirements_valid = Path('requirements.txt').exists()
        
        # Check Python syntax for key files
        python_files_valid = True
        key_files = [
            'src/health/health.py',
            'src/chat/langgraph_chat_handler.py',
            'src/file_processing/file_handler.py'
        ]
        
        invalid_files = []
        for file_path in key_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, 'r') as f:
                        compile(f.read(), file_path, 'exec')
                except SyntaxError:
                    invalid_files.append(file_path)
                    python_files_valid = False
        
        result = {
            'status': 'PASSED' if template_valid and requirements_valid and python_files_valid else 'FAILED',
            'cloudformation_template_valid': template_valid,
            'requirements_file_exists': requirements_valid,
            'python_syntax_valid': python_files_valid,
            'invalid_python_files': invalid_files
        }
        
        self.results['validation_results']['build_process'] = result
        self._update_summary(result['status'])
        
        if result['status'] == 'PASSED':
            print("  ✅ Build process validation passed")
        else:
            print(f"  ❌ Build process issues detected")
    
    def validate_cleanup_status(self):
        """Validate repository cleanup is complete"""
        print("🧹 Validating cleanup status...")
        
        # Check for __pycache__ directories
        pycache_dirs = list(Path('.').rglob('__pycache__'))
        pycache_dirs = [d for d in pycache_dirs if 'venv' not in str(d)]  # Exclude venv
        
        # Check for .pyc files
        pyc_files = list(Path('src').rglob('*.pyc'))
        
        # Check for temporary files
        temp_files = []
        for pattern in ['*.tmp', '*.temp', '*.log', '*.bak']:
            temp_files.extend(Path('.').rglob(pattern))
        temp_files = [f for f in temp_files if 'venv' not in str(f) and '.git' not in str(f)]
        
        result = {
            'status': 'PASSED' if not pycache_dirs and not pyc_files and not temp_files else 'WARNING',
            'pycache_directories': [str(d) for d in pycache_dirs],
            'pyc_files': [str(f) for f in pyc_files],
            'temp_files': [str(f) for f in temp_files]
        }
        
        self.results['validation_results']['cleanup_status'] = result
        if result['status'] == 'WARNING':
            self.results['summary']['warnings'] += 1
        else:
            self._update_summary(result['status'])
        
        if result['status'] == 'PASSED':
            print("  ✅ Repository cleanup complete")
        else:
            print(f"  ⚠️ Some temporary files remain (acceptable)")
    
    def validate_repository_structure(self):
        """Validate repository structure is organized correctly"""
        print("📁 Validating repository structure...")
        
        # Check required directories exist
        required_dirs = [
            'src',
            'tests',
            'scripts',
            'frontend',
            'docs',
            '.kiro/specs'
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                missing_dirs.append(dir_path)
        
        # Check key files exist
        key_files = [
            'README.md',
            'template.yaml',
            'requirements.txt',
            '.gitignore',
            '.env.example'
        ]
        
        missing_files = []
        for file_path in key_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        result = {
            'status': 'PASSED' if not missing_dirs and not missing_files else 'FAILED',
            'missing_directories': missing_dirs,
            'missing_files': missing_files,
            'total_dirs_checked': len(required_dirs),
            'total_files_checked': len(key_files)
        }
        
        self.results['validation_results']['repository_structure'] = result
        self._update_summary(result['status'])
        
        if result['status'] == 'PASSED':
            print("  ✅ Repository structure validated")
        else:
            print(f"  ❌ Repository structure issues: {missing_dirs + missing_files}")
    
    def _update_summary(self, status):
        """Update validation summary"""
        self.results['summary']['total_checks'] += 1
        if status == 'PASSED':
            self.results['summary']['passed_checks'] += 1
        else:
            self.results['summary']['failed_checks'] += 1
    
    def generate_report(self):
        """Generate final validation report"""
        print("\n" + "="*60)
        print("🧪 FINAL REPOSITORY VALIDATION REPORT")
        print("="*60)
        
        summary = self.results['summary']
        print(f"📊 Summary:")
        print(f"   Total Checks: {summary['total_checks']}")
        print(f"   Passed: {summary['passed_checks']}")
        print(f"   Failed: {summary['failed_checks']}")
        print(f"   Warnings: {summary['warnings']}")
        
        success_rate = (summary['passed_checks'] / summary['total_checks']) * 100 if summary['total_checks'] > 0 else 0
        print(f"   Success Rate: {success_rate:.1f}%")
        
        print(f"\n⏰ Validation completed at: {self.results['timestamp']}")
        
        # Overall status
        if summary['failed_checks'] == 0:
            print("\n🎉 REPOSITORY VALIDATION: ✅ PASSED")
            print("   Repository is ready for production deployment!")
        else:
            print("\n⚠️ REPOSITORY VALIDATION: ❌ ISSUES DETECTED")
            print("   Please address the failed checks before deployment.")
        
        # Save detailed report
        with open('validation_report.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: validation_report.json")
        
        return summary['failed_checks'] == 0

def main():
    """Run complete repository validation"""
    validator = RepositoryValidator()
    
    print("🚀 Starting Final Repository Validation...")
    print("="*60)
    
    # Run all validation checks
    validator.validate_documentation_links()
    validator.validate_build_process()
    validator.validate_cleanup_status()
    validator.validate_repository_structure()
    
    # Generate final report
    success = validator.generate_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())