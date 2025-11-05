#!/usr/bin/env python3
"""
Test script for FastFileProcessor class

This script tests the core file processing functionality including
initialization, validation, metadata management, and error handling.
"""

import sys
import os
import tempfile
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from file_processor.file_processor import FastFileProcessor, ProcessResult
from file_processor.file_processor import FileProcessingError, UnsupportedFileTypeError, FileTooLargeError
from shared.config import config

def create_test_files():
    """Create temporary test files for validation testing"""
    test_files = {}
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create a small text file
    txt_file = temp_dir / "test_document.txt"
    txt_file.write_text("This is a test document for file processing validation.")
    test_files['txt'] = str(txt_file)
    
    # Create a fake PDF file (just for extension testing)
    pdf_file = temp_dir / "test_document.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF")
    test_files['pdf'] = str(pdf_file)
    
    # Create a fake DOCX file (just for extension testing)
    docx_file = temp_dir / "test_document.docx"
    docx_file.write_bytes(b"PK\x03\x04")  # ZIP file signature (DOCX is a ZIP)
    test_files['docx'] = str(docx_file)
    
    # Create an unsupported file type
    unsupported_file = temp_dir / "test_document.xyz"
    unsupported_file.write_text("This is an unsupported file type.")
    test_files['unsupported'] = str(unsupported_file)
    
    # Create a large file (for size testing)
    large_file = temp_dir / "large_document.txt"
    large_content = "A" * (15 * 1024 * 1024)  # 15MB file
    large_file.write_text(large_content)
    test_files['large'] = str(large_file)
    
    return test_files, temp_dir

def test_processor_initialization():
    """Test FastFileProcessor initialization"""
    print("\n🔧 Testing FastFileProcessor Initialization")
    print("-" * 50)
    
    try:
        # Test with default user
        processor1 = FastFileProcessor()
        print("✅ Default initialization successful")
        
        # Test with custom user
        processor2 = FastFileProcessor("custom_user")
        print("✅ Custom user initialization successful")
        
        # Verify configuration
        assert processor2.user_id == "custom_user"
        assert processor2.bucket_name == config.S3_BUCKET_NAME
        assert processor2.metadata_table_name == config.FILE_METADATA_TABLE
        print("✅ Configuration validation passed")
        
        return processor1
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return None

def test_file_validation(processor, test_files):
    """Test file validation functionality"""
    print("\n📋 Testing File Validation")
    print("-" * 50)
    
    validation_results = {}
    
    # Test valid files
    for file_type in ['txt', 'pdf', 'docx']:
        try:
            result = processor.validate_file(test_files[file_type])
            validation_results[file_type] = result
            print(f"✅ {file_type.upper()} validation: PASSED")
            print(f"   Size: {result['file_size']} bytes")
            print(f"   Extension: {result['file_extension']}")
            print(f"   MIME: {result['mime_type']}")
            
        except Exception as e:
            print(f"❌ {file_type.upper()} validation: FAILED - {e}")
            validation_results[file_type] = None
    
    # Test unsupported file type
    try:
        processor.validate_file(test_files['unsupported'])
        print("❌ Unsupported file validation: Should have failed")
    except UnsupportedFileTypeError:
        print("✅ Unsupported file validation: Correctly rejected")
    except Exception as e:
        print(f"❌ Unsupported file validation: Unexpected error - {e}")
    
    # Test large file
    try:
        processor.validate_file(test_files['large'])
        print("❌ Large file validation: Should have failed")
    except FileTooLargeError:
        print("✅ Large file validation: Correctly rejected")
    except Exception as e:
        print(f"❌ Large file validation: Unexpected error - {e}")
    
    # Test non-existent file
    try:
        processor.validate_file("non_existent_file.txt")
        print("❌ Non-existent file validation: Should have failed")
    except FileProcessingError:
        print("✅ Non-existent file validation: Correctly rejected")
    except Exception as e:
        print(f"❌ Non-existent file validation: Unexpected error - {e}")
    
    return validation_results

def test_metadata_operations(processor):
    """Test metadata creation and management"""
    print("\n🗄️  Testing Metadata Operations")
    print("-" * 50)
    
    try:
        # Test file ID generation
        file_id1 = processor.generate_file_id()
        file_id2 = processor.generate_file_id()
        assert file_id1 != file_id2
        print("✅ File ID generation: Unique IDs created")
        
        # Test S3 key generation
        s3_key = processor.generate_s3_key(file_id1, "test_document.pdf")
        assert "users/" in s3_key
        assert processor.user_id in s3_key
        assert "test_document.pdf" in s3_key
        print(f"✅ S3 key generation: {s3_key}")
        
        # Test metadata creation
        validation_result = {
            'file_name': 'test_document.pdf',
            'file_size': 1024,
            'mime_type': 'application/pdf',
            'file_extension': '.pdf'
        }
        
        metadata = processor.create_file_metadata(file_id1, "test_path", validation_result)
        assert metadata['file_id'] == file_id1
        assert metadata['user_id'] == processor.user_id
        assert metadata['processing_status'] == 'uploaded'
        print("✅ Metadata creation: Structure validated")
        
        # Test metadata saving (if DynamoDB is available)
        try:
            success = processor.save_metadata(metadata)
            if success:
                print("✅ Metadata saving: Successfully saved to DynamoDB")
                
                # Test metadata retrieval
                retrieved = processor.get_file_metadata(file_id1)
                if retrieved:
                    print("✅ Metadata retrieval: Successfully retrieved from DynamoDB")
                    
                    # Test status update
                    update_success = processor.update_file_status(
                        file_id1, 
                        'processing_status', 
                        'processing'
                    )
                    if update_success:
                        print("✅ Status update: Successfully updated in DynamoDB")
                    
                    # Test file deletion
                    delete_result = processor.delete_file(file_id1)
                    if delete_result.success:
                        print("✅ File deletion: Successfully deleted from DynamoDB")
                else:
                    print("⚠️ Metadata retrieval: Failed to retrieve")
            else:
                print("⚠️ Metadata saving: Failed to save to DynamoDB")
                
        except Exception as e:
            print(f"⚠️ DynamoDB operations: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Metadata operations failed: {e}")
        return False

def test_file_listing(processor):
    """Test file listing functionality"""
    print("\n📚 Testing File Listing")
    print("-" * 50)
    
    try:
        files = processor.list_user_files()
        print(f"✅ File listing: Found {len(files)} files for user '{processor.user_id}'")
        
        if files:
            print("📋 Sample file metadata:")
            sample_file = files[0]
            for key, value in sample_file.items():
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ File listing failed: {e}")
        return False

def test_error_handling(processor):
    """Test error handling functionality"""
    print("\n⚠️  Testing Error Handling")
    print("-" * 50)
    
    try:
        # Test error handling
        test_file_id = processor.generate_file_id()
        test_error = Exception("Test error for demonstration")
        
        processor.handle_error(test_file_id, test_error)
        print("✅ Error handling: Error logged and status updated")
        
        # Test processing status retrieval for non-existent file
        status = processor.get_processing_status("non_existent_file_id")
        assert 'error' in status
        print("✅ Status retrieval: Correctly handles non-existent files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
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
    
    print("🧪 FASTFILEPROCESSOR COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # Check configuration
    print("\n📋 Configuration Check:")
    missing_config = config.validate_config()
    if missing_config:
        print(f"❌ Missing configuration: {', '.join(missing_config)}")
        print("Please set up your .env file with AWS credentials")
        return False
    else:
        print("✅ Configuration is complete")
    
    # Create test files
    print("\n📁 Creating test files...")
    test_files, temp_dir = create_test_files()
    print(f"✅ Created {len(test_files)} test files")
    
    # Track test results
    test_results = {
        'initialization': False,
        'validation': False,
        'metadata': False,
        'listing': False,
        'error_handling': False
    }
    
    try:
        # Test 1: Initialization
        processor = test_processor_initialization()
        if processor:
            test_results['initialization'] = True
        else:
            print("❌ Cannot proceed without successful initialization")
            return False
        
        # Test 2: File Validation
        validation_results = test_file_validation(processor, test_files)
        if validation_results:
            test_results['validation'] = True
        
        # Test 3: Metadata Operations
        if test_metadata_operations(processor):
            test_results['metadata'] = True
        
        # Test 4: File Listing
        if test_file_listing(processor):
            test_results['listing'] = True
        
        # Test 5: Error Handling
        if test_error_handling(processor):
            test_results['error_handling'] = True
        
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
    
    print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - FastFileProcessor is ready!")
        return True
    else:
        print("⚠️ Some tests failed - Review implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)