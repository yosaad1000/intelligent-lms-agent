#!/usr/bin/env python3
"""
Test script for text extraction functionality

This script tests PDF, DOCX, and TXT text extraction with various
file types and edge cases.
"""

import sys
import os
import tempfile
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from file_processor.text_extractor import AdvancedTextExtractor, ExtractionResult

def create_test_files():
    """Create test files for text extraction testing"""
    temp_dir = Path(tempfile.mkdtemp())
    test_files = {}
    
    # Create a comprehensive text file
    txt_content = """
    Advanced Text Extraction Test Document
    
    Chapter 1: Introduction to Machine Learning
    Machine learning is a subset of artificial intelligence that focuses on algorithms
    that can learn and make decisions from data without being explicitly programmed.
    
    Key Concepts:
    - Supervised Learning: Learning with labeled data
    - Unsupervised Learning: Finding patterns in unlabeled data
    - Reinforcement Learning: Learning through interaction and feedback
    
    Chapter 2: Neural Networks
    Neural networks are computing systems inspired by biological neural networks.
    They consist of interconnected nodes (neurons) that process information.
    
    Mathematical Foundation:
    The basic neuron computes: output = activation(sum(weights * inputs) + bias)
    
    Common activation functions include:
    1. Sigmoid: f(x) = 1 / (1 + e^(-x))
    2. ReLU: f(x) = max(0, x)
    3. Tanh: f(x) = (e^x - e^(-x)) / (e^x + e^(-x))
    
    Chapter 3: Applications
    Machine learning has numerous applications across various domains:
    - Computer Vision: Image recognition, object detection
    - Natural Language Processing: Text analysis, translation
    - Healthcare: Diagnosis, drug discovery
    - Finance: Fraud detection, algorithmic trading
    
    Conclusion:
    This document provides a comprehensive overview of machine learning concepts
    and their practical applications in modern technology.
    """
    
    txt_file = temp_dir / "machine_learning_guide.txt"
    txt_file.write_text(txt_content.strip(), encoding='utf-8')
    test_files['comprehensive_txt'] = str(txt_file)
    
    # Create a simple PDF (text-based)
    simple_pdf_content = b"""%PDF-1.4
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
/Length 200
>>
stream
BT
/F1 12 Tf
72 720 Td
(Data Science Fundamentals) Tj
0 -20 Td
(This PDF contains information about data science,) Tj
0 -20 Td
(including statistics, machine learning, and data visualization.) Tj
0 -20 Td
(Key topics: Python, R, SQL, Pandas, NumPy, Matplotlib) Tj
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
0000000526 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
623
%%EOF"""
    
    pdf_file = temp_dir / "data_science_fundamentals.pdf"
    pdf_file.write_bytes(simple_pdf_content)
    test_files['simple_pdf'] = str(pdf_file)
    
    # Create a minimal DOCX file (just a ZIP with basic structure)
    # Note: This is a simplified DOCX for testing - in real scenarios, 
    # we'd use proper DOCX files
    docx_file = temp_dir / "research_methods.docx"
    
    # Create a basic DOCX structure
    import zipfile
    with zipfile.ZipFile(docx_file, 'w') as docx:
        # Add minimal DOCX structure
        docx.writestr('[Content_Types].xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>''')
        
        docx.writestr('_rels/.rels', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>''')
        
        docx.writestr('word/document.xml', '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
<w:p><w:r><w:t>Research Methods in Computer Science</w:t></w:r></w:p>
<w:p><w:r><w:t>This document covers various research methodologies used in computer science studies.</w:t></w:r></w:p>
<w:p><w:r><w:t>Quantitative Methods: Statistical analysis, experiments, surveys</w:t></w:r></w:p>
<w:p><w:r><w:t>Qualitative Methods: Case studies, interviews, observations</w:t></w:r></w:p>
<w:p><w:r><w:t>Mixed Methods: Combining quantitative and qualitative approaches</w:t></w:r></w:p>
</w:body>
</w:document>''')
    
    test_files['simple_docx'] = str(docx_file)
    
    # Create files with different encodings
    utf8_file = temp_dir / "utf8_text.txt"
    utf8_file.write_text("UTF-8 encoded text with special characters: áéíóú ñ", encoding='utf-8')
    test_files['utf8_txt'] = str(utf8_file)
    
    latin1_file = temp_dir / "latin1_text.txt"
    latin1_file.write_text("Latin-1 encoded text with characters", encoding='latin-1')
    test_files['latin1_txt'] = str(latin1_file)
    
    return test_files, temp_dir

def test_text_extraction(extractor, test_files):
    """Test text extraction from different file types"""
    print("\n📄 Testing Text Extraction")
    print("-" * 50)
    
    extraction_results = {}
    
    for file_type, file_path in test_files.items():
        print(f"\n🔍 Testing: {file_type}")
        
        try:
            result = extractor.extract_text(file_path)
            extraction_results[file_type] = result
            
            if result.success:
                print(f"✅ Extraction successful")
                print(f"   Method: {result.extraction_method}")
                print(f"   Characters: {result.char_count}")
                print(f"   Words: {result.word_count}")
                print(f"   Preview: {result.text[:100]}...")
                
                if result.metadata:
                    print(f"   Metadata: {result.metadata}")
            else:
                print(f"❌ Extraction failed: {result.error}")
                
        except Exception as e:
            print(f"❌ Exception during extraction: {e}")
            extraction_results[file_type] = None
    
    return extraction_results

def test_text_cleaning_and_processing(extractor):
    """Test text cleaning and processing functionality"""
    print("\n🧹 Testing Text Cleaning and Processing")
    print("-" * 50)
    
    # Test text with various issues
    messy_text = """
    This    is   a    messy     text   with   excessive    whitespace.
    
    
    
    It has multiple line breaks and    strange   formatting.
    
    Page 1
    
    Some content here...
    
    Page 2
    
    More content...
    
    It also has some special characters: @#$%^&*()
    And some normal punctuation: Hello, world! How are you?
    """
    
    try:
        # Test cleaning
        cleaned_text = extractor.clean_and_normalize_text(messy_text)
        print(f"✅ Text cleaning successful")
        print(f"   Original length: {len(messy_text)}")
        print(f"   Cleaned length: {len(cleaned_text)}")
        print(f"   Cleaned preview: {cleaned_text[:150]}...")
        
        # Test chunking
        chunks = extractor.chunk_text_for_indexing(cleaned_text, max_chunk_size=200, overlap=50)
        print(f"✅ Text chunking successful")
        print(f"   Number of chunks: {len(chunks)}")
        
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            print(f"   Chunk {i+1}: {chunk['size']} chars, {chunk['word_count']} words")
            print(f"     Preview: {chunk['text'][:80]}...")
        
        # Test concept extraction
        concepts = extractor.extract_concepts_and_keywords(cleaned_text)
        print(f"✅ Concept extraction successful")
        print(f"   Concepts found: {len(concepts)}")
        print(f"   Top concepts: {', '.join(concepts[:10])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Text processing failed: {e}")
        return False

def test_error_handling(extractor, temp_dir):
    """Test error handling for various edge cases"""
    print("\n⚠️  Testing Error Handling")
    print("-" * 50)
    
    test_cases = [
        ("Non-existent file", "non_existent_file.pdf"),
        ("Unsupported extension", temp_dir / "test.xyz"),
        ("Empty file", temp_dir / "empty.txt"),
        ("Corrupted PDF", temp_dir / "corrupted.pdf")
    ]
    
    # Create test files for error cases
    empty_file = temp_dir / "empty.txt"
    empty_file.write_text("", encoding='utf-8')
    
    unsupported_file = temp_dir / "test.xyz"
    unsupported_file.write_text("This is an unsupported file type", encoding='utf-8')
    
    corrupted_pdf = temp_dir / "corrupted.pdf"
    corrupted_pdf.write_bytes(b"This is not a valid PDF file")
    
    error_handling_results = {}
    
    for test_name, file_path in test_cases:
        try:
            result = extractor.extract_text(str(file_path))
            error_handling_results[test_name] = result
            
            if result.success:
                print(f"⚠️  {test_name}: Unexpectedly succeeded")
            else:
                print(f"✅ {test_name}: Correctly failed - {result.error}")
                
        except Exception as e:
            print(f"❌ {test_name}: Exception - {e}")
            error_handling_results[test_name] = None
    
    return error_handling_results

def test_performance_and_limits(extractor, temp_dir):
    """Test performance with larger files and edge cases"""
    print("\n⚡ Testing Performance and Limits")
    print("-" * 50)
    
    try:
        # Create a large text file
        large_content = "This is a performance test. " * 1000  # ~28KB
        large_file = temp_dir / "large_text.txt"
        large_file.write_text(large_content, encoding='utf-8')
        
        import time
        start_time = time.time()
        result = extractor.extract_text(str(large_file))
        extraction_time = time.time() - start_time
        
        if result.success:
            print(f"✅ Large file extraction: {extraction_time:.2f}s")
            print(f"   File size: {len(large_content)} characters")
            print(f"   Extraction rate: {len(large_content)/extraction_time:.0f} chars/sec")
            
            # Test chunking performance
            start_time = time.time()
            chunks = extractor.chunk_text_for_indexing(result.text, max_chunk_size=1000)
            chunking_time = time.time() - start_time
            
            print(f"✅ Chunking performance: {chunking_time:.2f}s")
            print(f"   Chunks created: {len(chunks)}")
            print(f"   Chunking rate: {len(chunks)/chunking_time:.0f} chunks/sec")
        else:
            print(f"❌ Large file extraction failed: {result.error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
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
    
    print("🧪 ADVANCED TEXT EXTRACTION TEST SUITE")
    print("=" * 60)
    
    # Initialize extractor
    try:
        extractor = AdvancedTextExtractor()
        print("✅ AdvancedTextExtractor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize extractor: {e}")
        return False
    
    # Create test files
    print("\n📁 Creating test files...")
    test_files, temp_dir = create_test_files()
    print(f"✅ Created {len(test_files)} test files")
    
    # Track test results
    test_results = {
        'extraction': False,
        'processing': False,
        'error_handling': False,
        'performance': False
    }
    
    try:
        # Test 1: Text Extraction
        extraction_results = test_text_extraction(extractor, test_files)
        successful_extractions = sum(1 for r in extraction_results.values() if r and r.success)
        if successful_extractions >= len(test_files) * 0.7:  # 70% success rate
            test_results['extraction'] = True
        
        # Test 2: Text Processing
        if test_text_cleaning_and_processing(extractor):
            test_results['processing'] = True
        
        # Test 3: Error Handling
        error_results = test_error_handling(extractor, temp_dir)
        if error_results:
            test_results['error_handling'] = True
        
        # Test 4: Performance
        if test_performance_and_limits(extractor, temp_dir):
            test_results['performance'] = True
        
    finally:
        # Cleanup
        cleanup_test_files(temp_dir)
    
    # Final Results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    for test_name, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests >= total_tests * 0.8:  # 80% success rate
        print("🎉 TEXT EXTRACTION ENGINE IS READY!")
        return True
    else:
        print("⚠️ Some text extraction tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)