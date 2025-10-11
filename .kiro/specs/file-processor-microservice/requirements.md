# File Processor Microservice - MVP Requirements

## Overview
**Priority: HIGH (Build Second)**  
Fast file upload and processing using Gradio + S3 + Bedrock Knowledge Base for immediate AI integration.

## Core User Stories

### US-FILE-001: Quick File Upload
**As a** student  
**I want to** upload my study notes easily  
**So that** the AI can help me with questions

#### Acceptance Criteria (EARS Format)
1. WHEN a student selects a file THEN the system SHALL accept PDF, DOCX, TXT formats
2. WHEN file is uploaded THEN the system SHALL store it in S3 with user-specific path
3. WHEN upload completes THEN the system SHALL show success confirmation
4. IF file is too large (>10MB) THEN the system SHALL reject with clear error message

### US-FILE-002: Fast Text Processing
**As a** system  
**I need to** extract text and index quickly  
**So that** students can ask questions immediately

#### Acceptance Criteria
1. WHEN file is uploaded THEN the system SHALL extract text content automatically
2. WHEN text is extracted THEN the system SHALL chunk content for optimal indexing
3. WHEN processing completes THEN the system SHALL add content to Bedrock Knowledge Base
4. WHEN indexing is done THEN the system SHALL update file status to "Ready for AI"

## Technical Implementation (Fast Build)

### Technology Stack
- **Frontend**: Gradio file upload component
- **Storage**: AWS S3 with simple folder structure
- **Processing**: Python text extraction libraries
- **AI Integration**: Bedrock Knowledge Base direct integration

### MVP Implementation
```python
import gradio as gr
import boto3
import PyPDF2
import docx
import os
from datetime import datetime

class FastFileProcessor:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.bucket_name = 'lms-files-bucket'
        self.kb_id = 'your-knowledge-base-id'
    
    def process_upload(self, file, user_id="demo_user"):
        if not file:
            return "❌ No file selected"
        
        try:
            # 1. Upload to S3
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_key = f"users/{user_id}/notes/{timestamp}_{os.path.basename(file.name)}"
            
            self.s3.upload_file(file.name, self.bucket_name, s3_key)
            
            # 2. Extract text
            text_content = self._extract_text(file.name)
            
            # 3. Save extracted text for Knowledge Base
            text_s3_key = f"users/{user_id}/processed/{timestamp}_extracted.txt"
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=text_s3_key,
                Body=text_content.encode('utf-8')
            )
            
            # 4. Trigger Knowledge Base sync (simplified)
            # In production, this would trigger KB data source sync
            
            return f"✅ File processed successfully!\n📄 Original: {s3_key}\n📝 Text: {text_s3_key}\n🤖 Ready for AI questions!"
            
        except Exception as e:
            return f"❌ Processing failed: {str(e)}"
    
    def _extract_text(self, file_path):
        """Fast text extraction"""
        try:
            if file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_path.endswith('.pdf'):
                text = ""
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                return text
            
            elif file_path.endswith('.docx'):
                doc = docx.Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            
            else:
                return "Unsupported file format"
                
        except Exception as e:
            return f"Text extraction error: {str(e)}"
    
    def list_user_files(self, user_id="demo_user"):
        """List uploaded files for user"""
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"users/{user_id}/notes/"
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'name': os.path.basename(obj['Key']),
                        'size': obj['Size'],
                        'modified': obj['LastModified'].strftime("%Y-%m-%d %H:%M")
                    })
            
            return files
        except Exception as e:
            return [{"error": str(e)}]

# Gradio Interface
def create_file_interface():
    processor = FastFileProcessor()
    
    with gr.Blocks() as file_app:
        gr.Markdown("# 📁 File Upload & Processing")
        
        with gr.Row():
            with gr.Column():
                file_input = gr.File(
                    label="Upload Study Notes",
                    file_types=[".pdf", ".docx", ".txt"]
                )
                upload_btn = gr.Button("🚀 Process File", variant="primary")
                
            with gr.Column():
                status_output = gr.Textbox(
                    label="Processing Status",
                    lines=5,
                    interactive=False
                )
        
        # File list
        gr.Markdown("## 📚 Your Uploaded Files")
        file_list = gr.DataFrame(
            headers=["Name", "Size", "Modified"],
            label="Files"
        )
        refresh_btn = gr.Button("🔄 Refresh List")
        
        # Event handlers
        upload_btn.click(
            fn=processor.process_upload,
            inputs=[file_input],
            outputs=[status_output]
        )
        
        refresh_btn.click(
            fn=processor.list_user_files,
            outputs=[file_list]
        )
    
    return file_app
```

## Testing Strategy
1. **Unit Test**: Test text extraction with sample files
2. **Integration Test**: Upload → S3 → Knowledge Base flow
3. **Manual Test**: Upload different file types via Gradio
4. **Performance Test**: Upload 10MB files, measure processing time

## Dependencies
- Authentication service (for user identification)

## Delivery Timeline
- **Day 1**: Basic upload and S3 integration
- **Day 2**: Text extraction and Knowledge Base integration
- **Day 3**: Testing and optimization