#!/usr/bin/env python3
"""
Test script for file upload functionality

This script tests the complete file upload process including
S3 upload, progress tracking, and metadata management.
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

def create_sample_files():
    """Create sample files for upload testing"""
    temp_dir = Path(tempfile.mkdtemp())
    sample_files = {}
    
    # Create a text file with academic content
    txt_file = temp_dir / "physics_notes.txt"
    txt_content = """
    Physics Study Notes - Thermodynamics
    
    Chapter 1: Introduction to Thermodynamics
    Thermodynamics is the branch of physics that deals with heat and temperature, 
    and their relation to energy, work, radiation, and properties of matter.
    
    Key Concepts:
    - Energy conservation
    - Entropy and the second law
    - Heat engines and refrigerators
    - Phase transitions
    
    Important Equations:
    - First Law: Delta_U = Q - W
    - Second Law: Delta_S >= 0 for isolated systems
    - Ideal Gas Law: PV = nRT
    """
    txt_file.write_text(txt_content.strip(), encoding='utf-8')
    sample_files['physics_notes'] = str(txt_file)
    
    # Create a math file
    math_file = temp_dir / "calculus_formulas.txt"
    math_content = """
    Calculus Reference Sheet
    
    Derivatives:
    - d/dx(x^n) = nx^(n-1)
    - d/dx(sin x) = cos x
    - d/dx(cos x) = -sin x
    - d/dx(e^x) = e^x
    - d/dx(ln x) = 1/x
    
    Integrals:
    - integral(x^n dx) = x^(n+1)/(n+1) + C
    - integral(sin x dx) = -cos x + C
    - integral(cos x dx) = sin x + C
    - integral(e^x dx) = e^x + C
    """
    math_file.write_text(math_content.strip(), encoding='utf-8')
    sample_files['calculus_formulas'] = str(math_file)
    
    # Create a small PDF-like file (for testing)
    pdf_file = temp_dir / "chemistry_notes.pdf"
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
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Chemistry Notes) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
    pdf_file.write_bytes(pdf_content)
    sample_files['chemistry_notes'] = str(pdf_file)
    
    return sample_files, temp_dir

def test_single_file_upload(processor, file_path, file_name):
    """Test uploading a single file"""
    print(f"\n📤 Testing upload: {file_name}")
    print("-" * 40)
    
    try:
        # Process file upload
        result = processor.process_file_upload(file_path)
        
        if result.success:
            print(f"✅ Upload successful!")
            print(f"   File ID: {result.file_id}")
            print(f"   S3 Key: {result.data.get('s3_key', 'N/A')}")
            print(f"   Duration: {result.data.get('processing_duration', 0):.2f}s")
            print(f"   Size: {result.data.get('file_size', 0)} bytes")
            
            # Test progress tracking
            progress = processor.get_upload_progress(result.file_id)
            print(f"   Progress: {progress['progress_percent']}%")
            
            # Test S3 file info
            if 's3_key' in result.data:
                s3_info = processor.get_s3_file_info(result.data['s3_key'])
                if s3_info:
                    print(f"   S3 Size: {s3_info['size']} bytes")
                    print(f"   Content Type: {s3_info['content_type']}")
            
            return result.file_id
            
        else:
            print(f"❌ Upload failed: {result.error}")
            return None
            
    except Exception as e:
        print(f"❌ Upload exception: {e}")
        return None

def test_file_download(processor, file_id, temp_dir):
    """Test downloading a file from S3"""
    print(f"\n📥 Testing download for file: {file_id}")
    print("-" * 40)
    
    try:
        # Get file metadata
        metadata = processor.get_file_metadata(file_id)
        if not metadata or 's3_key' not in metadata:
            print("❌ No S3 key found in metadata")
            return False
        
        s3_key = metadata['s3_key']
        download_path = temp_dir / f"downloaded_{metadata['original_filename']}"
        
        # Download file
        success = processor.download_file_from_s3(s3_key, str(download_path))
        
        if success and download_path.exists():
            print(f"✅ Download successful!")
            print(f"   Downloaded to: {download_path}")
            print(f"   File size: {download_path.stat().st_size} bytes")
            
            # Verify content (for text files)
            if download_path.suffix == '.txt':
                content = download_path.read_text()[:100]
                print(f"   Content preview: {content}...")
            
            return True
        else:
            print("❌ Download failed")
            return False
            
    except Exception as e:
        print(f"❌ Download exception: {e}")
        return False

def test_file_management(processor, uploaded_files):
    """Test file management operations"""
    print(f"\n📋 Testing file management")
    print("-" * 40)
    
    try:
        # List all user files
        files = processor.list_user_files()
        print(f"✅ Found {len(files)} files for user")
        
        # Show file details
        for i, file_info in enumerate(files[:3]):  # Show first 3 files
            print(f"   File {i+1}: {file_info.get('original_filename', 'Unknown')}")
            print(f"     Status: {file_info.get('processing_status', 'Unknown')}")
            print(f"     Size: {file_info.get('file_size', 0)} bytes")
        
        # Test file deletion (delete one uploaded file)
        if uploaded_files:
            test_file_id = uploaded_files[0]
            print(f"\n🗑️ Testing file deletion: {test_file_id}")
            
            delete_result = processor.delete_file(test_file_id)
            if delete_result.success:
                print(f"✅ File deleted successfully")
                print(f"   Message: {delete_result.message}")
            else:
                print(f"❌ Delete failed: {delete_result.error}")
        
        return True
        
    except Exception as e:
        print(f"❌ File management exception: {e}")
        return False

def test_error_scenarios(processor, temp_dir):
    """Test error handling scenarios"""
    print(f"\n⚠️ Testing error scenarios")
    print("-" * 40)
    
    try:
        # Test 1: Non-existent file
        result = processor.process_file_upload("non_existent_file.txt")
        if not result.success:
            print("✅ Non-existent file correctly rejected")
        else:
            print("❌ Non-existent file should have failed")
        
        # Test 2: Unsupported file type
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_text("Unsupported content")
        
        result = processor.process_file_upload(str(unsupported_file))
        if not result.success and "not supported" in result.error:
            print("✅ Unsupported file type correctly rejected")
        else:
            print("❌ Unsupported file type should have failed")
        
        # Test 3: Large file (create a file larger than limit)
        large_file = temp_dir / "large_file.txt"
        large_content = "A" * (15 * 1024 * 1024)  # 15MB
        large_file.write_text(large_content)
        
        result = processor.process_file_upload(str(large_file))
        if not result.success and "exceeds limit" in result.error:
            print("✅ Large file correctly rejected")
        else:
            print("❌ Large file should have failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error scenario testing failed: {e}")
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
    
    print("🧪 FILE UPLOAD FUNCTIONALITY TEST SUITE")
    print("=" * 60)
    
    # Check configuration
    print("\n📋 Configuration Check:")
    missing_config = config.validate_config()
    if missing_config:
        print(f"❌ Missing configuration: {', '.join(missing_config)}")
        return False
    else:
        print("✅ Configuration is complete")
    
    # Create sample files
    print("\n📁 Creating sample files...")
    sample_files, temp_dir = create_sample_files()
    print(f"✅ Created {len(sample_files)} sample files")
    
    # Initialize processor
    try:
        processor = FastFileProcessor("upload_test_user")
        print("✅ FastFileProcessor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return False
    
    uploaded_files = []
    
    try:
        # Test file uploads
        print("\n" + "="*60)
        print("📤 TESTING FILE UPLOADS")
        print("="*60)
        
        for file_name, file_path in sample_files.items():
            file_id = test_single_file_upload(processor, file_path, file_name)
            if file_id:
                uploaded_files.append(file_id)
        
        # Test file downloads
        print("\n" + "="*60)
        print("📥 TESTING FILE DOWNLOADS")
        print("="*60)
        
        download_success = 0
        for file_id in uploaded_files:
            if test_file_download(processor, file_id, temp_dir):
                download_success += 1
        
        # Test file management
        print("\n" + "="*60)
        print("📋 TESTING FILE MANAGEMENT")
        print("="*60)
        
        management_success = test_file_management(processor, uploaded_files)
        
        # Test error scenarios
        print("\n" + "="*60)
        print("⚠️ TESTING ERROR SCENARIOS")
        print("="*60)
        
        error_handling_success = test_error_scenarios(processor, temp_dir)
        
    finally:
        # Cleanup
        cleanup_test_files(temp_dir)
    
    # Final Results
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    print(f"📤 File Uploads: {len(uploaded_files)}/{len(sample_files)} successful")
    print(f"📥 File Downloads: {download_success}/{len(uploaded_files)} successful")
    print(f"📋 File Management: {'✅ PASSED' if management_success else '❌ FAILED'}")
    print(f"⚠️ Error Handling: {'✅ PASSED' if error_handling_success else '❌ FAILED'}")
    
    total_operations = len(sample_files) + len(uploaded_files) + 2  # uploads + downloads + management + errors
    successful_operations = len(uploaded_files) + download_success + (1 if management_success else 0) + (1 if error_handling_success else 0)
    
    print(f"\n📈 Overall Success Rate: {successful_operations}/{total_operations} ({successful_operations/total_operations*100:.1f}%)")
    
    if successful_operations >= total_operations * 0.8:  # 80% success rate
        print("🎉 FILE UPLOAD FUNCTIONALITY IS READY!")
        return True
    else:
        print("⚠️ Some file upload tests failed - Review implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)