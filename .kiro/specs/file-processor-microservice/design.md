# File Processor Microservice Design

## Architecture Overview

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Gradio File    │───▶│  File Handler   │───▶│   AWS S3        │
│   Upload UI     │    │   & Processor   │    │   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Upload Status   │    │ Text Extractor  │    │ Bedrock KB      │
│   Tracking      │    │   (PDF/DOCX)    │    │   Indexing      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   DynamoDB      │
                    │   Metadata      │
                    └─────────────────┘
```

### Processing Pipeline
1. **Upload**: File → Gradio → Validation → S3 Storage
2. **Extract**: S3 Event → Text Extraction → Content Processing
3. **Index**: Processed Text → Bedrock Knowledge Base → Search Ready
4. **Track**: Status Updates → DynamoDB → User Notification

## Technical Design

### Core Classes
```python
class FastFileProcessor:
    """Main file processing handler"""
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.bedrock_agent = boto3.client('bedrock-agent')
        self.dynamodb = boto3.resource('dynamodb')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.kb_id = os.getenv('KNOWLEDGE_BASE_ID')
        
    def process_upload(self, file, user_id: str) -> ProcessResult
    def extract_text(self, file_path: str) -> str
    def index_content(self, content: str, metadata: dict) -> bool
    def get_processing_status(self, file_id: str) -> dict
    def list_user_files(self, user_id: str) -> List[dict]

class TextExtractor:
    """Handle different file format text extraction"""
    def extract_pdf(self, file_path: str) -> str
    def extract_docx(self, file_path: str) -> str
    def extract_txt(self, file_path: str) -> str
    def clean_text(self, raw_text: str) -> str

class KnowledgeBaseManager:
    """Manage Bedrock Knowledge Base operations"""
    def add_document(self, content: str, metadata: dict) -> str
    def update_document(self, doc_id: str, content: str) -> bool
    def delete_document(self, doc_id: str) -> bool
    def sync_data_source(self) -> bool

class FileMetadataManager:
    """Manage file metadata in DynamoDB"""
    def create_file_record(self, file_data: dict) -> str
    def update_status(self, file_id: str, status: str) -> bool
    def get_file_info(self, file_id: str) -> dict
    def list_user_files(self, user_id: str) -> List[dict]
```

### File Processing Workflow
```python
async def process_file_workflow(file_path: str, user_id: str):
    """Complete file processing workflow"""
    
    # 1. Validate file
    validation_result = validate_file(file_path)
    if not validation_result.valid:
        return ProcessResult(success=False, error=validation_result.error)
    
    # 2. Upload to S3
    s3_key = generate_s3_key(user_id, file_path)
    upload_result = upload_to_s3(file_path, s3_key)
    
    # 3. Extract text content
    text_content = extract_text_content(file_path)
    
    # 4. Process and clean text
    processed_content = clean_and_chunk_text(text_content)
    
    # 5. Index in Knowledge Base
    kb_result = index_in_knowledge_base(processed_content, {
        'user_id': user_id,
        'file_name': os.path.basename(file_path),
        's3_key': s3_key,
        'upload_time': datetime.now().isoformat()
    })
    
    # 6. Update metadata
    update_file_metadata(file_id, 'completed', kb_result.document_id)
    
    return ProcessResult(success=True, document_id=kb_result.document_id)
```

### S3 Bucket Structure
```
lms-files-bucket/
├── users/
│   ├── {user_id}/
│   │   ├── raw/
│   │   │   ├── {timestamp}_{filename}.pdf
│   │   │   └── {timestamp}_{filename}.docx
│   │   ├── processed/
│   │   │   ├── {timestamp}_extracted.txt
│   │   │   └── {timestamp}_chunks.json
│   │   └── metadata/
│   │       └── {file_id}_metadata.json
└── shared/
    └── sample_documents/
```

### DynamoDB Schema
```json
{
  "TableName": "lms-file-metadata",
  "KeySchema": [
    {
      "AttributeName": "file_id",
      "KeyType": "HASH"
    }
  ],
  "AttributeDefinitions": [
    {
      "AttributeName": "file_id",
      "AttributeType": "S"
    },
    {
      "AttributeName": "user_id",
      "AttributeType": "S"
    }
  ],
  "GlobalSecondaryIndexes": [
    {
      "IndexName": "user-id-index",
      "KeySchema": [
        {
          "AttributeName": "user_id",
          "KeyType": "HASH"
        }
      ]
    }
  ]
}
```

### File Metadata Structure
```json
{
  "file_id": "uuid-string",
  "user_id": "user-uuid",
  "original_filename": "thermodynamics_notes.pdf",
  "s3_key": "users/user123/raw/20241201_thermodynamics_notes.pdf",
  "file_size": 2048576,
  "file_type": "application/pdf",
  "upload_timestamp": "2024-12-01T10:30:00Z",
  "processing_status": "completed",
  "text_extraction_status": "success",
  "kb_indexing_status": "indexed",
  "kb_document_id": "kb-doc-uuid",
  "content_preview": "First 200 characters of extracted text...",
  "extracted_concepts": ["thermodynamics", "entropy", "energy"],
  "error_messages": [],
  "processing_duration": 15.5
}
```

## Gradio Interface Design

### File Upload Interface
```python
def create_file_interface():
    with gr.Blocks() as file_app:
        gr.Markdown("# 📁 File Upload & Processing")
        
        # Upload section
        with gr.Row():
            with gr.Column(scale=2):
                file_input = gr.File(
                    label="Upload Study Notes",
                    file_types=[".pdf", ".docx", ".txt"],
                    file_count="multiple"
                )
                upload_btn = gr.Button("🚀 Process Files", variant="primary")
                
            with gr.Column(scale=1):
                upload_status = gr.Textbox(
                    label="Processing Status",
                    lines=8,
                    interactive=False
                )
        
        # File management
        gr.Markdown("## 📚 Your Files")
        
        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh")
            delete_btn = gr.Button("🗑️ Delete Selected", variant="secondary")
        
        file_list = gr.DataFrame(
            headers=["Select", "Name", "Type", "Size", "Status", "Uploaded"],
            datatype=["bool", "str", "str", "str", "str", "str"],
            interactive=True
        )
        
        # Processing details
        with gr.Accordion("Processing Details", open=False):
            processing_log = gr.JSON(label="Detailed Processing Information")
    
    return file_app
```

## Text Processing Pipeline

### Text Extraction Strategy
```python
class AdvancedTextExtractor:
    """Enhanced text extraction with formatting preservation"""
    
    def extract_pdf_with_structure(self, file_path: str) -> dict:
        """Extract PDF with structure information"""
        import PyPDF2
        import pdfplumber
        
        # Use PyPDF2 for basic extraction
        basic_text = self._extract_with_pypdf2(file_path)
        
        # Use pdfplumber for better formatting
        structured_text = self._extract_with_pdfplumber(file_path)
        
        return {
            'raw_text': basic_text,
            'structured_text': structured_text,
            'sections': self._identify_sections(structured_text),
            'tables': self._extract_tables(file_path),
            'images': self._extract_image_text(file_path)
        }
    
    def chunk_text_intelligently(self, text: str, max_chunk_size: int = 1000) -> List[dict]:
        """Chunk text while preserving semantic meaning"""
        sentences = self._split_into_sentences(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) > max_chunk_size:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'size': len(current_chunk),
                        'concepts': self._extract_concepts(current_chunk)
                    })
                current_chunk = sentence
            else:
                current_chunk += " " + sentence
        
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'size': len(current_chunk),
                'concepts': self._extract_concepts(current_chunk)
            })
        
        return chunks
```

## Knowledge Base Integration

### Bedrock Knowledge Base Setup
```python
class BedrockKBIntegration:
    """Integrate with Bedrock Knowledge Base"""
    
    def setup_knowledge_base(self):
        """Set up Knowledge Base with proper configuration"""
        kb_config = {
            'name': 'lms-student-notes',
            'description': 'Student uploaded study materials',
            'roleArn': 'arn:aws:iam::account:role/BedrockKBRole',
            'knowledgeBaseConfiguration': {
                'type': 'VECTOR',
                'vectorKnowledgeBaseConfiguration': {
                    'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1'
                }
            },
            'storageConfiguration': {
                'type': 'OPENSEARCH_SERVERLESS',
                'opensearchServerlessConfiguration': {
                    'collectionArn': 'arn:aws:aoss:us-east-1:account:collection/lms-kb',
                    'vectorIndexName': 'lms-vector-index',
                    'fieldMapping': {
                        'vectorField': 'vector',
                        'textField': 'text',
                        'metadataField': 'metadata'
                    }
                }
            }
        }
        
        return self.bedrock_agent.create_knowledge_base(**kb_config)
    
    def add_document_to_kb(self, content: str, metadata: dict) -> str:
        """Add processed document to Knowledge Base"""
        
        # Create data source if not exists
        data_source_config = {
            'knowledgeBaseId': self.kb_id,
            'name': f"user-{metadata['user_id']}-documents",
            'dataSourceConfiguration': {
                'type': 'S3',
                's3Configuration': {
                    'bucketArn': f"arn:aws:s3:::{self.bucket_name}",
                    'inclusionPrefixes': [f"users/{metadata['user_id']}/processed/"]
                }
            }
        }
        
        # Upload processed content to S3 for KB ingestion
        processed_s3_key = f"users/{metadata['user_id']}/processed/{metadata['file_id']}.txt"
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=processed_s3_key,
            Body=content.encode('utf-8'),
            Metadata=metadata
        )
        
        # Trigger KB sync
        sync_response = self.bedrock_agent.start_ingestion_job(
            knowledgeBaseId=self.kb_id,
            dataSourceId=data_source_config['dataSourceId']
        )
        
        return sync_response['ingestionJob']['ingestionJobId']
```

## Error Handling & Recovery

### File Processing Errors
```python
class FileProcessingError(Exception):
    """Base file processing error"""
    pass

class UnsupportedFileTypeError(FileProcessingError):
    """File type not supported"""
    pass

class FileTooLargeError(FileProcessingError):
    """File exceeds size limit"""
    pass

class TextExtractionError(FileProcessingError):
    """Failed to extract text from file"""
    pass

class KnowledgeBaseError(FileProcessingError):
    """Failed to index in Knowledge Base"""
    pass

def handle_processing_error(error: Exception, file_id: str):
    """Handle and log processing errors"""
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': datetime.now().isoformat(),
        'file_id': file_id
    }
    
    # Update file status
    update_file_status(file_id, 'failed', error_info)
    
    # Log error for debugging
    logger.error(f"File processing failed: {error_info}")
    
    return error_info
```

## Performance Optimization

### Async Processing
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncFileProcessor:
    """Asynchronous file processing for better performance"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_multiple_files(self, files: List[str], user_id: str):
        """Process multiple files concurrently"""
        tasks = []
        for file_path in files:
            task = asyncio.create_task(
                self.process_single_file_async(file_path, user_id)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def process_single_file_async(self, file_path: str, user_id: str):
        """Process single file asynchronously"""
        loop = asyncio.get_event_loop()
        
        # Run CPU-intensive tasks in thread pool
        text_content = await loop.run_in_executor(
            self.executor, 
            self.extract_text, 
            file_path
        )
        
        # Process and index
        processed_content = await loop.run_in_executor(
            self.executor,
            self.process_text,
            text_content
        )
        
        # Index in Knowledge Base
        kb_result = await self.index_in_kb_async(processed_content, user_id)
        
        return kb_result
```

## Integration Points

### With Authentication Service
- Validate user tokens before file operations
- Use user ID for file organization and access control

### With AI Chat Service
- Provide indexed content for Knowledge Base queries
- Share file metadata for context-aware responses

### With Voice Interview Service
- Supply content for generating interview questions
- Provide topic-specific material for assessment

### With Quiz Generator Service
- Share processed content for question generation
- Provide concept extraction for targeted quizzes

## Testing Strategy

### Unit Tests
- Test text extraction for each file type
- Test S3 upload and download operations
- Test Knowledge Base integration
- Test metadata management

### Integration Tests
- Test complete file processing pipeline
- Test Knowledge Base query functionality
- Test error handling and recovery
- Test concurrent file processing

### Performance Tests
- Test with large files (up to 10MB)
- Test concurrent uploads (multiple users)
- Test Knowledge Base indexing speed
- Test text extraction performance