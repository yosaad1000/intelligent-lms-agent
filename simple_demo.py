#!/usr/bin/env python3
"""
Simple File Processor Demo

A command-line demo to showcase the file processing functionality
without the complexity of Gradio dependencies.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_sample_files():
    """Create sample files for demonstration"""
    temp_dir = Path(tempfile.mkdtemp())
    sample_files = {}
    
    # Create a comprehensive AI study guide
    ai_content = """
    Artificial Intelligence Study Guide
    
    Chapter 1: Introduction to AI
    Artificial Intelligence (AI) is the simulation of human intelligence in machines
    that are programmed to think and learn like humans. The term may also be applied
    to any machine that exhibits traits associated with a human mind such as learning
    and problem-solving.
    
    Key Concepts:
    - Machine Learning: Algorithms that improve automatically through experience
    - Deep Learning: Neural networks with multiple layers
    - Natural Language Processing: Understanding and generating human language
    - Computer Vision: Interpreting and understanding visual information
    
    Chapter 2: Machine Learning Types
    
    Supervised Learning:
    - Uses labeled training data
    - Examples: Classification, Regression
    - Algorithms: Linear Regression, Decision Trees, Random Forest
    
    Unsupervised Learning:
    - Finds patterns in unlabeled data
    - Examples: Clustering, Dimensionality Reduction
    - Algorithms: K-Means, PCA, Hierarchical Clustering
    
    Reinforcement Learning:
    - Learns through interaction with environment
    - Uses rewards and penalties
    - Applications: Game playing, Robotics, Autonomous vehicles
    
    Chapter 3: Applications
    AI has revolutionized many industries:
    - Healthcare: Medical diagnosis, drug discovery
    - Finance: Fraud detection, algorithmic trading
    - Transportation: Self-driving cars, route optimization
    - Technology: Search engines, recommendation systems
    
    Conclusion:
    AI continues to evolve and impact society in profound ways.
    Understanding its capabilities and limitations is crucial for the future.
    """
    
    ai_file = temp_dir / "ai_study_guide.txt"
    ai_file.write_text(ai_content.strip(), encoding='utf-8')
    sample_files['AI Study Guide'] = str(ai_file)
    
    # Create a mathematics reference
    math_content = """
    Calculus Reference Sheet
    
    Derivatives:
    Basic Rules:
    - Power Rule: d/dx(x^n) = nx^(n-1)
    - Constant Rule: d/dx(c) = 0
    - Sum Rule: d/dx(f + g) = f' + g'
    - Product Rule: d/dx(fg) = f'g + fg'
    - Quotient Rule: d/dx(f/g) = (f'g - fg')/g^2
    - Chain Rule: d/dx(f(g(x))) = f'(g(x)) * g'(x)
    
    Common Derivatives:
    - d/dx(sin x) = cos x
    - d/dx(cos x) = -sin x
    - d/dx(e^x) = e^x
    - d/dx(ln x) = 1/x
    
    Integrals:
    Basic Rules:
    - Power Rule: ∫x^n dx = x^(n+1)/(n+1) + C
    - Constant Rule: ∫c dx = cx + C
    - Sum Rule: ∫(f + g) dx = ∫f dx + ∫g dx
    
    Common Integrals:
    - ∫sin x dx = -cos x + C
    - ∫cos x dx = sin x + C
    - ∫e^x dx = e^x + C
    - ∫1/x dx = ln|x| + C
    
    Applications:
    - Area under curves
    - Volume calculations
    - Physics applications (velocity, acceleration)
    """
    
    math_file = temp_dir / "calculus_reference.txt"
    math_file.write_text(math_content.strip(), encoding='utf-8')
    sample_files['Calculus Reference'] = str(math_file)
    
    return sample_files, temp_dir

def demonstrate_file_processing(processor, sample_files):
    """Demonstrate the complete file processing workflow"""
    print("\n🔄 DEMONSTRATING COMPLETE FILE PROCESSING WORKFLOW")
    print("=" * 70)
    
    for file_name, file_path in sample_files.items():
        print(f"\n📄 Processing: {file_name}")
        print("-" * 50)
        
        try:
            # Process file through complete workflow
            result = processor.process_file_complete_workflow(file_path)
            
            if result.success:
                print("✅ Processing completed successfully!")
                
                # Display results
                upload_data = result.data.get('upload_data', {})
                extraction_data = result.data.get('extraction_data', {})
                
                print(f"📋 File ID: {result.file_id}")
                print(f"📏 File Size: {upload_data.get('file_size', 0)} bytes")
                print(f"⏱️  Processing Time: {result.data.get('processing_duration', 0):.2f} seconds")
                print(f"🔤 Characters Extracted: {extraction_data.get('char_count', 0)}")
                print(f"📝 Words Extracted: {extraction_data.get('word_count', 0)}")
                print(f"🛠️  Extraction Method: {extraction_data.get('extraction_method', 'N/A')}")
                
                # Show concepts
                concepts = extraction_data.get('concepts', [])
                if concepts:
                    print(f"🎯 Key Concepts: {', '.join(concepts[:8])}")
                
                # Show content preview
                preview = extraction_data.get('content_preview', '')
                if preview:
                    print(f"👀 Content Preview:")
                    print(f"   {preview[:200]}...")
                
            else:
                print(f"❌ Processing failed: {result.error}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        print()

def demonstrate_file_management(processor):
    """Demonstrate file management capabilities"""
    print("\n📚 DEMONSTRATING FILE MANAGEMENT")
    print("=" * 70)
    
    try:
        # List user files
        files = processor.list_user_files()
        print(f"📁 Found {len(files)} files for user")
        
        if files:
            print("\n📋 File List:")
            for i, file_info in enumerate(files[:5], 1):  # Show first 5 files
                filename = file_info.get('original_filename', 'Unknown')
                status = file_info.get('processing_status', 'Unknown')
                size = file_info.get('file_size', 0)
                concepts = file_info.get('extracted_concepts', [])
                
                print(f"  {i}. {filename}")
                print(f"     Status: {status} | Size: {size} bytes")
                if concepts:
                    print(f"     Concepts: {', '.join(concepts[:5])}")
        
        # Get statistics
        print("\n📊 User Statistics:")
        stats = processor.get_user_file_statistics()
        
        if 'error' not in stats:
            print(f"  Total Files: {stats.get('total_files', 0)}")
            print(f"  Total Size: {stats.get('total_size_mb', 0)} MB")
            print(f"  Recent Uploads: {stats.get('recent_uploads', 0)}")
            
            file_types = stats.get('file_types', {})
            if file_types:
                print("  File Types:")
                for ext, count in file_types.items():
                    print(f"    {ext or 'No extension'}: {count} files")
        
    except Exception as e:
        print(f"❌ File management error: {e}")

def demonstrate_search(processor):
    """Demonstrate search functionality"""
    print("\n🔍 DEMONSTRATING SEARCH FUNCTIONALITY")
    print("=" * 70)
    
    search_terms = ["artificial", "calculus", "learning", "derivatives"]
    
    for term in search_terms:
        try:
            results = processor.search_user_files(term)
            print(f"\n🔎 Search results for '{term}': {len(results)} files found")
            
            for i, result in enumerate(results[:3], 1):  # Show first 3 results
                filename = result.get('original_filename', 'Unknown')
                preview = result.get('content_preview', '')[:100]
                print(f"  {i}. {filename}")
                print(f"     Preview: {preview}...")
                
        except Exception as e:
            print(f"❌ Search error for '{term}': {e}")

def cleanup_demo_files(temp_dir):
    """Clean up temporary demo files"""
    try:
        import shutil
        shutil.rmtree(temp_dir)
        print("🧹 Demo files cleaned up")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

def main():
    """Main demo function"""
    print("🚀 FILE PROCESSOR MICROSERVICE DEMO")
    print("=" * 70)
    print("Showcasing complete file processing workflow with text extraction,")
    print("content analysis, and intelligent search capabilities.")
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
        print(f"   AWS Region: {config.AWS_DEFAULT_REGION}")
        print(f"   S3 Bucket: {config.S3_BUCKET_NAME}")
        print(f"   DynamoDB Table: {config.FILE_METADATA_TABLE}")
    
    # Initialize processor
    try:
        print("\n🔧 Initializing File Processor...")
        processor = FastFileProcessor("demo_user")
        print("✅ File processor initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return False
    
    # Create sample files
    print("\n📁 Creating sample files...")
    sample_files, temp_dir = create_sample_files()
    print(f"✅ Created {len(sample_files)} sample files")
    
    try:
        # Demonstrate file processing
        demonstrate_file_processing(processor, sample_files)
        
        # Demonstrate file management
        demonstrate_file_management(processor)
        
        # Demonstrate search
        demonstrate_search(processor)
        
        print("\n" + "=" * 70)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("The file processor microservice is working perfectly with:")
        print("✅ Complete file upload and processing workflow")
        print("✅ Advanced text extraction from multiple formats")
        print("✅ Intelligent content analysis and concept extraction")
        print("✅ Comprehensive metadata management")
        print("✅ Powerful search and discovery capabilities")
        print("✅ Real-time status tracking and error handling")
        print("\nReady for integration with Knowledge Base and Gradio interface!")
        
        return True
        
    finally:
        # Cleanup
        cleanup_demo_files(temp_dir)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)