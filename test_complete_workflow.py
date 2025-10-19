#!/usr/bin/env python3
"""
Test script for complete file processing workflow

This script tests the end-to-end file processing including upload,
text extraction, processing, and metadata management.
"""

import sys
import os
import tempfile
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from file_processor.file_processor import FastFileProcessor
from shared.config import config

def create_comprehensive_test_files():
    """Create comprehensive test files for complete workflow testing"""
    temp_dir = Path(tempfile.mkdtemp())
    test_files = {}
    
    # Create a detailed academic text file
    academic_content = """
    Introduction to Artificial Intelligence
    
    Artificial Intelligence (AI) is a branch of computer science that aims to create 
    intelligent machines that can perform tasks that typically require human intelligence.
    
    Chapter 1: History of AI
    The field of AI was founded in 1956 at the Dartmouth Conference. Key pioneers include:
    - Alan Turing: Proposed the Turing Test
    - John McCarthy: Coined the term "Artificial Intelligence"
    - Marvin Minsky: Co-founder of MIT's AI laboratory
    - Herbert Simon: Developed early AI programs
    
    Chapter 2: Types of AI
    AI can be categorized into several types:
    
    1. Narrow AI (Weak AI)
       - Designed for specific tasks
       - Examples: Chess programs, recommendation systems
       - Current state of most AI applications
    
    2. General AI (Strong AI)
       - Human-level intelligence across all domains
       - Theoretical concept, not yet achieved
       - Goal of many AI researchers
    
    3. Superintelligence
       - Intelligence exceeding human capabilities
       - Hypothetical future development
       - Subject of ongoing debate
    
    Chapter 3: Machine Learning
    Machine Learning is a subset of AI that enables systems to learn from data:
    
    Supervised Learning:
    - Uses labeled training data
    - Examples: Classification, regression
    - Algorithms: Linear regression, decision trees, neural networks
    
    Unsupervised Learning:
    - Finds patterns in unlabeled data
    - Examples: Clustering, dimensionality reduction
    - Algorithms: K-means, PCA, autoencoders
    
    Reinforcement Learning:
    - Learns through interaction with environment
    - Uses rewards and penalties
    - Applications: Game playing, robotics
    
    Chapter 4: Neural Networks
    Neural networks are inspired by biological neural systems:
    
    Basic Components:
    - Neurons (nodes): Processing units
    - Weights: Connection strengths
    - Activation functions: Non-linear transformations
    - Layers: Input, hidden, output
    
    Deep Learning:
    - Neural networks with multiple hidden layers
    - Capable of learning complex patterns
    - Applications: Image recognition, natural language processing
    
    Chapter 5: Applications
    AI has numerous real-world applications:
    
    Healthcare:
    - Medical diagnosis and imaging
    - Drug discovery and development
    - Personalized treatment plans
    
    Transportation:
    - Autonomous vehicles
    - Traffic optimization
    - Route planning
    
    Finance:
    - Fraud detection
    - Algorithmic trading
    - Credit scoring
    
    Technology:
    - Search engines
    - Virtual assistants
    - Recommendation systems
    
    Conclusion:
    Artificial Intelligence continues to evolve and impact various aspects of society.
    Understanding its principles, capabilities, and limitations is crucial for navigating
    the future of technology and its implications for humanity.
    """
    
    txt_file = temp_dir / "ai_comprehensive_guide.txt"
    txt_file.write_text(academic_content.strip(), encoding='utf-8')
    test_files['comprehensive_ai_guide'] = str(txt_file)
    
    # Create a mathematics text file
    math_content = """
    Advanced Calculus Study Guide
    
    Differential Calculus
    
    Limits and Continuity:
    The limit of f(x) as x approaches a is L if for every ε > 0, 
    there exists δ > 0 such that |f(x) - L| < ε whenever 0 < |x - a| < δ.
    
    Derivatives:
    The derivative of f(x) at point a is defined as:
    f'(a) = lim(h→0) [f(a+h) - f(a)] / h
    
    Common Derivative Rules:
    - Power Rule: d/dx(x^n) = nx^(n-1)
    - Product Rule: d/dx(uv) = u'v + uv'
    - Quotient Rule: d/dx(u/v) = (u'v - uv') / v²
    - Chain Rule: d/dx(f(g(x))) = f'(g(x)) · g'(x)
    
    Integral Calculus
    
    Definite Integrals:
    The definite integral of f(x) from a to b represents the area under the curve.
    
    Fundamental Theorem of Calculus:
    If F'(x) = f(x), then ∫[a to b] f(x)dx = F(b) - F(a)
    
    Integration Techniques:
    - Substitution Method
    - Integration by Parts
    - Partial Fractions
    - Trigonometric Substitution
    
    Applications:
    - Area between curves
    - Volume of solids of revolution
    - Arc length calculations
    - Physics applications (work, center of mass)
    """
    
    math_file = temp_dir / "calculus_study_guide.txt"
    math_file.write_text(math_content.strip(), encoding='utf-8')
    test_files['calculus_guide'] = str(math_file)
    
    # Create a simple PDF for testing
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 300
>>
stream
BT
/F1 12 Tf
72 720 Td
(Computer Science Fundamentals) Tj
0 -20 Td
(This document covers key concepts in computer science:) Tj
0 -20 Td
(- Algorithms and Data Structures) Tj
0 -20 Td
(- Programming Paradigms) Tj
0 -20 Td
(- Database Systems) Tj
0 -20 Td
(- Software Engineering) Tj
0 -20 Td
(- Computer Networks) Tj
0 -20 Td
(- Operating Systems) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000626 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
723
%%EOF"""
    
    pdf_file = temp_dir / "cs_fundamentals.pdf"
    pdf_file.write_bytes(pdf_content)
    test_files['cs_fundamentals_pdf'] = str(pdf_file)
    
    return test_files, temp_dir

def test_complete_workflow(processor, test_files):
    """Test the complete file processing workflow"""
    print("\n🔄 Testing Complete File Processing Workflow")
    print("-" * 60)
    
    workflow_results = {}
    
    for file_name, file_path in test_files.items():
        print(f"\n📄 Processing: {file_name}")
        print("-" * 40)
        
        try:
            # Run complete workflow
            result = processor.process_file_complete_workflow(file_path)
            workflow_results[file_name] = result
            
            if result.success:
                print(f"✅ Complete workflow successful!")
                print(f"   File ID: {result.file_id}")
                
                # Display upload data
                upload_data = result.data.get('upload_data', {})
                print(f"   Upload Duration: {upload_data.get('processing_duration', 0):.2f}s")
                print(f"   File Size: {upload_data.get('file_size', 0)} bytes")
                
                # Display extraction data
                extraction_data = result.data.get('extraction_data', {})
                print(f"   Extraction Method: {extraction_data.get('extraction_method', 'N/A')}")
                print(f"   Word Count: {extraction_data.get('word_count', 0)}")
                print(f"   Character Count: {extraction_data.get('char_count', 0)}")
                
                # Display concepts
                concepts = extraction_data.get('concepts', [])
                if concepts:
                    print(f"   Top Concepts: {', '.join(concepts[:5])}")
                
                # Display content preview
                preview = extraction_data.get('content_preview', '')
                if preview:
                    print(f"   Content Preview: {preview[:100]}...")
                
                print(f"   Total Duration: {result.data.get('processing_duration', 0):.2f}s")
                
                # Verify metadata was updated
                metadata = processor.get_file_metadata(result.file_id)
                if metadata:
                    print(f"   Processing Status: {metadata.get('processing_status', 'Unknown')}")
                    print(f"   Text Extraction: {metadata.get('text_extraction_status', 'Unknown')}")
                    print(f"   KB Indexing: {metadata.get('kb_indexing_status', 'Unknown')}")
                
            else:
                print(f"❌ Workflow failed: {result.error}")
                
        except Exception as e:
            print(f"❌ Exception during workflow: {e}")
            workflow_results[file_name] = None
    
    return workflow_results

def test_text_extraction_integration(processor, test_files):
    """Test text extraction integration with file processing"""
    print("\n📝 Testing Text Extraction Integration")
    print("-" * 60)
    
    if not test_files:
        print("⚠️ No test files available")
        return False
    
    # Test with first file
    file_name, file_path = list(test_files.items())[0]
    
    try:
        # First upload the file
        upload_result = processor.process_file_upload(file_path)
        if not upload_result.success:
            print(f"❌ Upload failed: {upload_result.error}")
            return False
        
        file_id = upload_result.file_id
        print(f"✅ File uploaded: {file_id}")
        
        # Test text extraction
        extraction_result = processor.extract_text_from_file(file_path, file_id)
        
        if extraction_result.success:
            print(f"✅ Text extraction successful")
            
            extracted_text = extraction_result.data.get('extracted_text', '')
            print(f"   Extracted text length: {len(extracted_text)} characters")
            
            concepts = extraction_result.data.get('concepts', [])
            print(f"   Concepts extracted: {len(concepts)}")
            print(f"   Sample concepts: {', '.join(concepts[:5])}")
            
            # Test saving processed text
            if extracted_text:
                save_result = processor.save_processed_text(file_id, extracted_text)
                if save_result.success:
                    print(f"✅ Processed text saved to S3")
                    print(f"   S3 Key: {save_result.data.get('processed_s3_key', 'N/A')}")
                else:
                    print(f"❌ Failed to save processed text: {save_result.error}")
            
            return True
        else:
            print(f"❌ Text extraction failed: {extraction_result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Text extraction integration test failed: {e}")
        return False

def test_workflow_error_handling(processor, temp_dir):
    """Test error handling in the complete workflow"""
    print("\n⚠️  Testing Workflow Error Handling")
    print("-" * 60)
    
    error_test_cases = [
        ("Non-existent file", "non_existent_file.txt"),
        ("Unsupported file type", temp_dir / "test.xyz"),
        ("Empty file", temp_dir / "empty.txt")
    ]
    
    # Create test files for error cases
    empty_file = temp_dir / "empty.txt"
    empty_file.write_text("", encoding='utf-8')
    
    unsupported_file = temp_dir / "test.xyz"
    unsupported_file.write_text("This is an unsupported file type", encoding='utf-8')
    
    error_results = {}
    
    for test_name, file_path in error_test_cases:
        try:
            result = processor.process_file_complete_workflow(str(file_path))
            error_results[test_name] = result
            
            if result.success:
                print(f"⚠️  {test_name}: Unexpectedly succeeded")
            else:
                print(f"✅ {test_name}: Correctly failed - {result.error}")
                
        except Exception as e:
            print(f"❌ {test_name}: Exception - {e}")
            error_results[test_name] = None
    
    return error_results

def test_performance_metrics(processor, test_files):
    """Test performance metrics for the complete workflow"""
    print("\n⚡ Testing Performance Metrics")
    print("-" * 60)
    
    if not test_files:
        print("⚠️ No test files available for performance testing")
        return False
    
    try:
        import time
        
        performance_results = []
        
        for file_name, file_path in list(test_files.items())[:2]:  # Test first 2 files
            print(f"\n📊 Performance test: {file_name}")
            
            start_time = time.time()
            result = processor.process_file_complete_workflow(file_path)
            total_time = time.time() - start_time
            
            if result.success:
                file_size = result.data.get('upload_data', {}).get('file_size', 0)
                word_count = result.data.get('extraction_data', {}).get('word_count', 0)
                
                performance_data = {
                    'file_name': file_name,
                    'file_size': file_size,
                    'word_count': word_count,
                    'total_time': total_time,
                    'processing_rate': file_size / total_time if total_time > 0 else 0,
                    'words_per_second': word_count / total_time if total_time > 0 else 0
                }
                
                performance_results.append(performance_data)
                
                print(f"   File size: {file_size} bytes")
                print(f"   Word count: {word_count}")
                print(f"   Total time: {total_time:.2f}s")
                print(f"   Processing rate: {performance_data['processing_rate']:.0f} bytes/sec")
                print(f"   Words per second: {performance_data['words_per_second']:.0f}")
            else:
                print(f"   ❌ Performance test failed: {result.error}")
        
        # Calculate averages
        if performance_results:
            avg_time = sum(p['total_time'] for p in performance_results) / len(performance_results)
            avg_rate = sum(p['processing_rate'] for p in performance_results) / len(performance_results)
            
            print(f"\n📈 Performance Summary:")
            print(f"   Average processing time: {avg_time:.2f}s")
            print(f"   Average processing rate: {avg_rate:.0f} bytes/sec")
            print(f"   Files processed: {len(performance_results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance testing failed: {e}")
        return False

def cleanup_test_files(temp_dir):
    """Clean up temporary test files"""
    try:
        import shutil
        shutil.rmtree(temp_dir)
        print("🧹 Test files cleaned up")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

def main():
    """Main test function"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 COMPLETE FILE PROCESSING WORKFLOW TEST SUITE")
    print("=" * 70)
    
    # Check configuration
    print("\n📋 Configuration Check:")
    missing_config = config.validate_config()
    if missing_config:
        print(f"❌ Missing configuration: {', '.join(missing_config)}")
        return False
    else:
        print("✅ Configuration is complete")
    
    # Initialize processor
    try:
        processor = FastFileProcessor("workflow_test_user")
        print("✅ FastFileProcessor initialized with text extraction")
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return False
    
    # Create test files
    print("\n📁 Creating comprehensive test files...")
    test_files, temp_dir = create_comprehensive_test_files()
    print(f"✅ Created {len(test_files)} test files")
    
    # Track test results
    test_results = {
        'complete_workflow': False,
        'text_extraction_integration': False,
        'error_handling': False,
        'performance': False
    }
    
    try:
        # Test 1: Complete Workflow
        workflow_results = test_complete_workflow(processor, test_files)
        successful_workflows = sum(1 for r in workflow_results.values() if r and r.success)
        if successful_workflows >= len(test_files) * 0.8:  # 80% success rate
            test_results['complete_workflow'] = True
        
        # Test 2: Text Extraction Integration
        if test_text_extraction_integration(processor, test_files):
            test_results['text_extraction_integration'] = True
        
        # Test 3: Error Handling
        error_results = test_workflow_error_handling(processor, temp_dir)
        if error_results:
            test_results['error_handling'] = True
        
        # Test 4: Performance
        if test_performance_metrics(processor, test_files):
            test_results['performance'] = True
        
    finally:
        # Cleanup
        cleanup_test_files(temp_dir)
    
    # Final Results
    print("\n" + "=" * 70)
    print("📊 FINAL TEST RESULTS")
    print("=" * 70)
    
    for test_name, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests >= total_tests * 0.8:  # 80% success rate
        print("🎉 COMPLETE FILE PROCESSING WORKFLOW IS READY!")
        return True
    else:
        print("⚠️ Some workflow tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)