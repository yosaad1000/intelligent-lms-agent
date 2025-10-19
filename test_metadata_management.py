#!/usr/bin/env python3
"""
Test script for file metadata management functionality

This script tests advanced metadata operations including search,
statistics, content preview updates, and status filtering.
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

def setup_test_files(processor):
    """Upload some test files for metadata testing"""
    print("\n📁 Setting up test files for metadata testing...")
    
    temp_dir = Path(tempfile.mkdtemp())
    uploaded_files = []
    
    # Create diverse test files
    test_files = [
        ("physics_thermodynamics.txt", "Thermodynamics study notes covering heat engines, entropy, and energy conservation."),
        ("math_calculus.txt", "Calculus reference with derivatives, integrals, and limit theorems."),
        ("chemistry_organic.txt", "Organic chemistry notes on molecular structures and reactions."),
        ("biology_genetics.txt", "Genetics fundamentals including DNA, RNA, and heredity principles."),
        ("computer_science.txt", "Programming concepts covering algorithms, data structures, and complexity analysis.")
    ]
    
    for filename, content in test_files:
        # Create file
        file_path = temp_dir / filename
        file_path.write_text(content, encoding='utf-8')
        
        # Upload file
        result = processor.process_file_upload(str(file_path))
        if result.success:
            uploaded_files.append(result.file_id)
            print(f"✅ Uploaded: {filename}")
            
            # Update content preview and concepts for some files
            if "physics" in filename:
                processor.update_file_content_preview(
                    result.file_id,
                    content,
                    ["thermodynamics", "heat", "entropy", "energy"]
                )
            elif "math" in filename:
                processor.update_file_content_preview(
                    result.file_id,
                    content,
                    ["calculus", "derivatives", "integrals", "limits"]
                )
            elif "chemistry" in filename:
                processor.update_file_content_preview(
                    result.file_id,
                    content,
                    ["chemistry", "organic", "molecules", "reactions"]
                )
        else:
            print(f"❌ Failed to upload: {filename}")
    
    return uploaded_files, temp_dir

def test_file_listing_and_search(processor):
    """Test file listing and search functionality"""
    print("\n📋 Testing File Listing and Search")
    print("-" * 50)
    
    try:
        # Test basic file listing
        all_files = processor.list_user_files()
        print(f"✅ Listed {len(all_files)} files for user")
        
        # Test search functionality
        search_tests = [
            ("physics", "physics-related files"),
            ("calculus", "math-related files"),
            ("chemistry", "chemistry-related files"),
            ("thermodynamics", "concept-based search"),
            ("nonexistent", "non-matching search")
        ]
        
        for search_term, description in search_tests:
            results = processor.search_user_files(search_term)
            print(f"✅ Search '{search_term}' ({description}): {len(results)} results")
            
            if results:
                for result in results[:2]:  # Show first 2 results
                    print(f"   - {result.get('original_filename', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ File listing/search test failed: {e}")
        return False

def test_status_filtering(processor, uploaded_files):
    """Test filtering files by status"""
    print("\n📊 Testing Status Filtering")
    print("-" * 50)
    
    try:
        # Test different status filters
        status_tests = ['uploaded', 'processing', 'completed', 'failed']
        
        for status in status_tests:
            files = processor.get_files_by_status(status)
            print(f"✅ Files with status '{status}': {len(files)}")
        
        # Update some files to different statuses for testing
        if len(uploaded_files) >= 2:
            # Update one file to processing
            processor.update_file_status(uploaded_files[0], 'processing_status', 'processing')
            
            # Update another to completed
            processor.update_file_status(uploaded_files[1], 'processing_status', 'completed')
            
            print("✅ Updated file statuses for testing")
            
            # Test filtering again
            processing_files = processor.get_files_by_status('processing')
            completed_files = processor.get_files_by_status('completed')
            
            print(f"✅ Processing files after update: {len(processing_files)}")
            print(f"✅ Completed files after update: {len(completed_files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Status filtering test failed: {e}")
        return False

def test_file_statistics(processor):
    """Test file statistics functionality"""
    print("\n📈 Testing File Statistics")
    print("-" * 50)
    
    try:
        stats = processor.get_user_file_statistics()
        
        if 'error' in stats:
            print(f"❌ Statistics error: {stats['error']}")
            return False
        
        print(f"✅ Total files: {stats.get('total_files', 0)}")
        print(f"✅ Total size: {stats.get('total_size_mb', 0)} MB")
        print(f"✅ Average file size: {stats.get('average_file_size', 0)} bytes")
        print(f"✅ Recent uploads (24h): {stats.get('recent_uploads', 0)}")
        
        # File type distribution
        file_types = stats.get('file_types', {})
        print(f"✅ File types:")
        for ext, count in file_types.items():
            print(f"   {ext or 'no extension'}: {count} files")
        
        # Status distribution
        status_counts = stats.get('status_counts', {})
        print(f"✅ Status distribution:")
        for status, count in status_counts.items():
            print(f"   {status}: {count} files")
        
        return True
        
    except Exception as e:
        print(f"❌ File statistics test failed: {e}")
        return False

def test_content_preview_updates(processor, uploaded_files):
    """Test content preview and concept updates"""
    print("\n📝 Testing Content Preview Updates")
    print("-" * 50)
    
    try:
        if not uploaded_files:
            print("⚠️ No uploaded files to test content updates")
            return True
        
        test_file_id = uploaded_files[0]
        
        # Test content preview update
        test_preview = "This is a test content preview for metadata management testing."
        test_concepts = ["testing", "metadata", "management", "preview"]
        
        success = processor.update_file_content_preview(
            test_file_id,
            test_preview,
            test_concepts
        )
        
        if success:
            print("✅ Content preview updated successfully")
            
            # Verify the update
            metadata = processor.get_file_metadata(test_file_id)
            if metadata:
                updated_preview = metadata.get('content_preview', '')
                updated_concepts = metadata.get('extracted_concepts', [])
                
                print(f"✅ Preview length: {len(updated_preview)} characters")
                print(f"✅ Concepts count: {len(updated_concepts)}")
                print(f"   Concepts: {', '.join(updated_concepts[:5])}")
                
                # Test search with new concepts
                search_results = processor.search_user_files("testing")
                if search_results:
                    print("✅ Search finds updated content")
                else:
                    print("⚠️ Search didn't find updated content")
            else:
                print("❌ Failed to retrieve updated metadata")
                return False
        else:
            print("❌ Content preview update failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Content preview update test failed: {e}")
        return False

def test_progress_tracking(processor, uploaded_files):
    """Test upload progress tracking"""
    print("\n⏳ Testing Progress Tracking")
    print("-" * 50)
    
    try:
        if not uploaded_files:
            print("⚠️ No uploaded files to test progress tracking")
            return True
        
        # Test progress for existing files
        for i, file_id in enumerate(uploaded_files[:3]):
            progress = processor.get_upload_progress(file_id)
            
            if 'error' in progress:
                print(f"❌ Progress error for file {i+1}: {progress['error']}")
            else:
                print(f"✅ File {i+1} progress:")
                print(f"   Filename: {progress.get('filename', 'Unknown')}")
                print(f"   Status: {progress.get('status', 'Unknown')}")
                print(f"   Progress: {progress.get('progress_percent', 0)}%")
                print(f"   Size: {progress.get('file_size', 0)} bytes")
        
        # Test progress for non-existent file
        fake_progress = processor.get_upload_progress("non-existent-file-id")
        if 'error' in fake_progress:
            print("✅ Non-existent file progress correctly returns error")
        else:
            print("❌ Non-existent file should return error")
        
        return True
        
    except Exception as e:
        print(f"❌ Progress tracking test failed: {e}")
        return False

def test_metadata_retrieval(processor, uploaded_files):
    """Test detailed metadata retrieval"""
    print("\n🔍 Testing Metadata Retrieval")
    print("-" * 50)
    
    try:
        if not uploaded_files:
            print("⚠️ No uploaded files to test metadata retrieval")
            return True
        
        test_file_id = uploaded_files[0]
        
        # Test detailed metadata retrieval
        metadata = processor.get_file_metadata(test_file_id)
        
        if metadata:
            print("✅ Metadata retrieved successfully")
            print(f"   File ID: {metadata.get('file_id', 'Unknown')}")
            print(f"   Filename: {metadata.get('original_filename', 'Unknown')}")
            print(f"   Size: {metadata.get('file_size', 0)} bytes")
            print(f"   Type: {metadata.get('file_type', 'Unknown')}")
            print(f"   Status: {metadata.get('processing_status', 'Unknown')}")
            print(f"   Upload time: {metadata.get('upload_timestamp', 'Unknown')}")
            
            # Test processing status retrieval
            status = processor.get_processing_status(test_file_id)
            print(f"✅ Processing status: {status.get('processing_status', 'Unknown')}")
        else:
            print("❌ Failed to retrieve metadata")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Metadata retrieval test failed: {e}")
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
    
    print("🧪 FILE METADATA MANAGEMENT TEST SUITE")
    print("=" * 60)
    
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
        processor = FastFileProcessor("metadata_test_user")
        print("✅ FastFileProcessor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return False
    
    uploaded_files = []
    temp_dir = None
    
    # Track test results
    test_results = {
        'setup': False,
        'listing_search': False,
        'status_filtering': False,
        'statistics': False,
        'content_updates': False,
        'progress_tracking': False,
        'metadata_retrieval': False
    }
    
    try:
        # Setup test files
        uploaded_files, temp_dir = setup_test_files(processor)
        if uploaded_files:
            test_results['setup'] = True
            print(f"✅ Setup complete: {len(uploaded_files)} files uploaded")
        
        # Run tests
        if test_file_listing_and_search(processor):
            test_results['listing_search'] = True
        
        if test_status_filtering(processor, uploaded_files):
            test_results['status_filtering'] = True
        
        if test_file_statistics(processor):
            test_results['statistics'] = True
        
        if test_content_preview_updates(processor, uploaded_files):
            test_results['content_updates'] = True
        
        if test_progress_tracking(processor, uploaded_files):
            test_results['progress_tracking'] = True
        
        if test_metadata_retrieval(processor, uploaded_files):
            test_results['metadata_retrieval'] = True
        
    finally:
        # Cleanup
        if temp_dir:
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
        print("🎉 METADATA MANAGEMENT IS READY!")
        return True
    else:
        print("⚠️ Some metadata management tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)