#!/usr/bin/env python3
"""
File Processor Microservice - Gradio Demo App

This app demonstrates the complete file processing workflow including:
- File upload and validation
- Text extraction from PDF, DOCX, and TXT files
- Content processing and concept extraction
- Metadata management and search
"""

import sys
import os
import logging
from pathlib import Path
import tempfile
import json

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

import gradio as gr
from file_processor.file_processor import FastFileProcessor
from shared.config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class FileProcessorApp:
    """Gradio app for file processing demonstration"""
    
    def __init__(self):
        """Initialize the file processor app"""
        try:
            self.processor = FastFileProcessor("demo_user")
            logger.info("File processor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize file processor: {e}")
            raise
    
    def process_file_upload(self, file):
        """Process uploaded file through complete workflow"""
        if not file:
            return "❌ No file selected", "", "", "", ""
        
        try:
            # Run complete workflow
            result = self.processor.process_file_complete_workflow(file.name)
            
            if result.success:
                # Get detailed information
                upload_data = result.data.get('upload_data', {})
                extraction_data = result.data.get('extraction_data', {})
                
                # Format success message
                success_msg = f"""✅ File processed successfully!
                
📄 **File Information:**
- File ID: {result.file_id}
- Original Size: {upload_data.get('file_size', 0)} bytes
- Processing Time: {result.data.get('processing_duration', 0):.2f} seconds

📝 **Text Extraction:**
- Method: {extraction_data.get('extraction_method', 'N/A')}
- Characters Extracted: {extraction_data.get('char_count', 0)}
- Words Extracted: {extraction_data.get('word_count', 0)}

🎯 **Status:**
- Upload: ✅ Complete
- Text Extraction: ✅ Complete
- Processing: ✅ Complete
- Ready for AI: ✅ Yes
"""
                
                # Get extracted text
                extracted_text = extraction_data.get('extracted_text', '')
                
                # Get content preview
                content_preview = extraction_data.get('content_preview', '')
                
                # Get concepts
                concepts = extraction_data.get('concepts', [])
                concepts_text = ', '.join(concepts) if concepts else 'No concepts extracted'
                
                # Get metadata
                metadata = self.processor.get_file_metadata(result.file_id)
                metadata_json = json.dumps(metadata, indent=2, default=str) if metadata else '{}'
                
                return success_msg, extracted_text, content_preview, concepts_text, metadata_json
                
            else:
                error_msg = f"❌ Processing failed: {result.error}"
                return error_msg, "", "", "", ""
                
        except Exception as e:
            error_msg = f"❌ Exception during processing: {str(e)}"
            logger.error(error_msg)
            return error_msg, "", "", "", ""
    
    def list_user_files(self):
        """List all files for the current user"""
        try:
            files = self.processor.list_user_files(limit=20)
            
            if not files:
                return "No files found for user"
            
            # Format file list
            file_list = []
            for i, file_info in enumerate(files, 1):
                filename = file_info.get('original_filename', 'Unknown')
                status = file_info.get('processing_status', 'Unknown')
                size = file_info.get('file_size', 0)
                upload_time = file_info.get('upload_timestamp', 'Unknown')
                
                file_list.append([
                    str(i),
                    filename,
                    status,
                    f"{size} bytes",
                    upload_time[:19] if len(upload_time) > 19 else upload_time
                ])
            
            return file_list
            
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return f"Error listing files: {e}"
    
    def search_files(self, search_term):
        """Search files by content or filename"""
        if not search_term.strip():
            return "Please enter a search term"
        
        try:
            results = self.processor.search_user_files(search_term.strip())
            
            if not results:
                return f"No files found matching '{search_term}'"
            
            # Format search results
            search_results = []
            for i, file_info in enumerate(results, 1):
                filename = file_info.get('original_filename', 'Unknown')
                preview = file_info.get('content_preview', '')[:100]
                concepts = ', '.join(file_info.get('extracted_concepts', [])[:5])
                
                search_results.append([
                    str(i),
                    filename,
                    preview + "..." if len(preview) == 100 else preview,
                    concepts
                ])
            
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"Search error: {e}"
    
    def get_user_statistics(self):
        """Get user file statistics"""
        try:
            stats = self.processor.get_user_file_statistics()
            
            if 'error' in stats:
                return f"Error getting statistics: {stats['error']}"
            
            # Format statistics
            stats_text = f"""📊 **File Statistics**

📁 **Storage:**
- Total Files: {stats.get('total_files', 0)}
- Total Size: {stats.get('total_size_mb', 0)} MB
- Average File Size: {stats.get('average_file_size', 0)} bytes

📈 **Activity:**
- Recent Uploads (24h): {stats.get('recent_uploads', 0)}

📋 **File Types:**"""
            
            file_types = stats.get('file_types', {})
            for ext, count in file_types.items():
                stats_text += f"\n- {ext or 'No extension'}: {count} files"
            
            stats_text += "\n\n🔄 **Processing Status:**"
            status_counts = stats.get('status_counts', {})
            for status, count in status_counts.items():
                stats_text += f"\n- {status.title()}: {count} files"
            
            return stats_text
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return f"Statistics error: {e}"
    
    def create_interface(self):
        """Create the Gradio interface"""
        
        with gr.Blocks(title="File Processor Microservice Demo", theme=gr.themes.Soft()) as app:
            gr.Markdown("""
            # 📁 File Processor Microservice Demo
            
            Upload and process PDF, DOCX, and TXT files with advanced text extraction and analysis.
            
            **Features:**
            - 🔄 Complete file processing workflow
            - 📄 Multi-format text extraction (PDF, DOCX, TXT)
            - 🧠 Intelligent content analysis and concept extraction
            - 🔍 File search and management
            - 📊 Processing statistics and analytics
            """)
            
            with gr.Tabs():
                # File Upload Tab
                with gr.Tab("📤 Upload & Process"):
                    gr.Markdown("### Upload a file to see the complete processing workflow")
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            file_input = gr.File(
                                label="Select File",
                                file_types=[".pdf", ".docx", ".txt"],
                                type="filepath"
                            )
                            process_btn = gr.Button("🚀 Process File", variant="primary", size="lg")
                        
                        with gr.Column(scale=2):
                            status_output = gr.Textbox(
                                label="Processing Status",
                                lines=12,
                                interactive=False,
                                placeholder="Upload a file and click 'Process File' to see the results..."
                            )
                    
                    gr.Markdown("### 📝 Extracted Content")
                    
                    with gr.Row():
                        with gr.Column():
                            content_preview = gr.Textbox(
                                label="Content Preview (First 500 characters)",
                                lines=8,
                                interactive=False,
                                placeholder="Content preview will appear here..."
                            )
                        
                        with gr.Column():
                            concepts_output = gr.Textbox(
                                label="Extracted Concepts",
                                lines=4,
                                interactive=False,
                                placeholder="Key concepts will appear here..."
                            )
                    
                    with gr.Accordion("🔍 Full Extracted Text", open=False):
                        full_text_output = gr.Textbox(
                            label="Complete Extracted Text",
                            lines=15,
                            interactive=False,
                            placeholder="Full extracted text will appear here..."
                        )
                    
                    with gr.Accordion("📋 File Metadata", open=False):
                        metadata_output = gr.Textbox(
                            label="File Metadata (JSON)",
                            lines=10,
                            interactive=False,
                            placeholder="File metadata will appear here..."
                        )
                
                # File Management Tab
                with gr.Tab("📚 File Management"):
                    gr.Markdown("### Manage and search your uploaded files")
                    
                    with gr.Row():
                        refresh_btn = gr.Button("🔄 Refresh File List", variant="secondary")
                        get_stats_btn = gr.Button("📊 Get Statistics", variant="secondary")
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            file_list = gr.Dataframe(
                                headers=["#", "Filename", "Status", "Size", "Upload Time"],
                                label="Your Files",
                                interactive=False,
                                wrap=True
                            )
                        
                        with gr.Column(scale=1):
                            stats_output = gr.Textbox(
                                label="File Statistics",
                                lines=15,
                                interactive=False,
                                placeholder="Click 'Get Statistics' to see your file stats..."
                            )
                
                # Search Tab
                with gr.Tab("🔍 Search Files"):
                    gr.Markdown("### Search files by content, filename, or concepts")
                    
                    with gr.Row():
                        search_input = gr.Textbox(
                            label="Search Term",
                            placeholder="Enter keywords to search for...",
                            scale=3
                        )
                        search_btn = gr.Button("🔍 Search", variant="primary", scale=1)
                    
                    search_results = gr.Dataframe(
                        headers=["#", "Filename", "Content Preview", "Concepts"],
                        label="Search Results",
                        interactive=False,
                        wrap=True
                    )
                
                # Help Tab
                with gr.Tab("❓ Help"):
                    gr.Markdown("""
                    ## 📖 How to Use This Demo
                    
                    ### 📤 Upload & Process
                    1. **Select a file**: Choose a PDF, DOCX, or TXT file (max 10MB)
                    2. **Click Process**: The system will upload, extract text, and analyze content
                    3. **View results**: See processing status, extracted text, and key concepts
                    
                    ### 📚 File Management
                    - **Refresh File List**: See all your uploaded files
                    - **Get Statistics**: View storage usage and file type distribution
                    
                    ### 🔍 Search Files
                    - Search by **filename**: Find files by name
                    - Search by **content**: Find files containing specific text
                    - Search by **concepts**: Find files with extracted keywords
                    
                    ### 🎯 Supported File Types
                    - **PDF**: Text extraction with table support
                    - **DOCX**: Complete document structure extraction
                    - **TXT**: Multi-encoding text files
                    
                    ### ⚡ Processing Features
                    - **Text Extraction**: Advanced multi-method extraction
                    - **Content Cleaning**: Normalization and optimization
                    - **Concept Extraction**: Automatic keyword identification
                    - **Metadata Management**: Complete file information tracking
                    
                    ### 🔧 Technical Details
                    - **Storage**: Files stored in AWS S3
                    - **Metadata**: Tracked in DynamoDB
                    - **Processing**: Real-time status updates
                    - **Search**: Content-based search capabilities
                    """)
            
            # Event handlers
            process_btn.click(
                fn=self.process_file_upload,
                inputs=[file_input],
                outputs=[status_output, full_text_output, content_preview, concepts_output, metadata_output]
            )
            
            refresh_btn.click(
                fn=self.list_user_files,
                outputs=[file_list]
            )
            
            get_stats_btn.click(
                fn=self.get_user_statistics,
                outputs=[stats_output]
            )
            
            search_btn.click(
                fn=self.search_files,
                inputs=[search_input],
                outputs=[search_results]
            )
            
            # Auto-refresh file list on startup
            app.load(
                fn=self.list_user_files,
                outputs=[file_list]
            )
        
        return app

def main():
    """Main function to run the Gradio app"""
    print("🚀 Starting File Processor Microservice Demo")
    print("=" * 60)
    
    # Check configuration
    print("📋 Checking configuration...")
    missing_config = config.validate_config()
    if missing_config:
        print(f"❌ Missing configuration: {', '.join(missing_config)}")
        print("Please set up your .env file with AWS credentials")
        return False
    else:
        print("✅ Configuration is complete")
    
    try:
        # Initialize app
        print("🔧 Initializing file processor...")
        app_instance = FileProcessorApp()
        print("✅ File processor initialized successfully")
        
        # Create interface
        print("🎨 Creating Gradio interface...")
        app = app_instance.create_interface()
        print("✅ Interface created successfully")
        
        # Launch app
        print("\n🌟 Launching File Processor Demo App...")
        print("📱 The app will open in your browser automatically")
        print("🔗 You can also access it at: http://localhost:7860")
        print("\n" + "=" * 60)
        
        app.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            quiet=False
        )
        
    except Exception as e:
        print(f"❌ Failed to start app: {e}")
        logger.error(f"App startup failed: {e}")
        return False

if __name__ == "__main__":
    main()