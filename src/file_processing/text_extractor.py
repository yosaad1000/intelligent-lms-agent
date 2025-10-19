"""
Text extraction utilities for different file types
Supports PDF, DOCX, and TXT files for RAG processing
"""

import io
import logging
from typing import Optional, Dict, Any
import mimetypes

# Text extraction libraries
try:
    import PyPDF2
    from docx import Document
    TEXT_EXTRACTION_AVAILABLE = True
except ImportError:
    TEXT_EXTRACTION_AVAILABLE = False
    print("Warning: Text extraction libraries not available. Install with: pip install PyPDF2 python-docx")

logger = logging.getLogger(__name__)


class TextExtractor:
    """Utility class for extracting text from various file formats"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
    SUPPORTED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    }
    
    def __init__(self):
        self.extraction_methods = {
            '.pdf': self._extract_from_pdf,
            '.docx': self._extract_from_docx,
            '.txt': self._extract_from_txt
        }
    
    def is_supported_file(self, filename: str) -> bool:
        """Check if file type is supported for text extraction"""
        
        file_ext = self._get_file_extension(filename)
        return file_ext in self.SUPPORTED_EXTENSIONS
    
    def extract_text(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract text from file content
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename to determine file type
            
        Returns:
            Dictionary with extraction results
        """
        
        try:
            file_ext = self._get_file_extension(filename)
            
            if not self.is_supported_file(filename):
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_ext}',
                    'text': '',
                    'metadata': {}
                }
            
            if not TEXT_EXTRACTION_AVAILABLE and file_ext in ['.pdf', '.docx']:
                return {
                    'success': False,
                    'error': 'Text extraction libraries not available',
                    'text': '',
                    'metadata': {}
                }
            
            # Extract text using appropriate method
            extraction_method = self.extraction_methods[file_ext]
            result = extraction_method(file_content, filename)
            
            # Add metadata
            result['metadata'] = {
                'file_extension': file_ext,
                'file_size': len(file_content),
                'text_length': len(result.get('text', '')),
                'extraction_method': extraction_method.__name__
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'metadata': {}
            }
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension in lowercase with dot"""
        import os
        return os.path.splitext(filename.lower())[1]
    
    def _extract_from_txt(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from TXT file"""
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    text = file_content.decode(encoding)
                    return {
                        'success': True,
                        'text': text,
                        'encoding_used': encoding
                    }
                except UnicodeDecodeError:
                    continue
            
            # If all encodings fail, use utf-8 with error handling
            text = file_content.decode('utf-8', errors='replace')
            return {
                'success': True,
                'text': text,
                'encoding_used': 'utf-8 (with errors replaced)',
                'warning': 'Some characters may have been replaced due to encoding issues'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to extract text from TXT file: {str(e)}',
                'text': ''
            }
    
    def _extract_from_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from PDF file"""
        
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                return {
                    'success': False,
                    'error': 'PDF is encrypted and cannot be processed',
                    'text': ''
                }
            
            # Extract text from all pages
            text_content = []
            page_count = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():  # Only add non-empty pages
                        text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {str(e)}")
                    continue
            
            full_text = '\n\n'.join(text_content)
            
            return {
                'success': True,
                'text': full_text,
                'page_count': page_count,
                'pages_processed': len(text_content)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to extract text from PDF: {str(e)}',
                'text': ''
            }
    
    def _extract_from_docx(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from DOCX file"""
        
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
            # Extract text from paragraphs
            paragraphs = []
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:  # Only add non-empty paragraphs
                    paragraphs.append(text)
            
            # Extract text from tables
            table_content = []
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            row_text.append(cell_text)
                    if row_text:
                        table_content.append(' | '.join(row_text))
            
            # Combine all content
            all_content = []
            if paragraphs:
                all_content.extend(paragraphs)
            if table_content:
                all_content.append('\n--- Tables ---')
                all_content.extend(table_content)
            
            full_text = '\n\n'.join(all_content)
            
            return {
                'success': True,
                'text': full_text,
                'paragraph_count': len(paragraphs),
                'table_count': len(doc.tables),
                'table_rows_extracted': len(table_content)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to extract text from DOCX: {str(e)}',
                'text': ''
            }
    
    def validate_extracted_text(self, text: str, min_length: int = 10) -> Dict[str, Any]:
        """
        Validate extracted text quality
        
        Args:
            text: Extracted text to validate
            min_length: Minimum acceptable text length
            
        Returns:
            Validation results
        """
        
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'statistics': {}
        }
        
        # Basic statistics
        validation_result['statistics'] = {
            'character_count': len(text),
            'word_count': len(text.split()),
            'line_count': len(text.splitlines()),
            'paragraph_count': len([p for p in text.split('\n\n') if p.strip()])
        }
        
        # Validation checks
        if len(text) < min_length:
            validation_result['is_valid'] = False
            validation_result['warnings'].append(f'Text too short: {len(text)} characters (minimum: {min_length})')
        
        # Check for mostly non-alphabetic content (might indicate extraction issues)
        alphabetic_chars = sum(1 for c in text if c.isalpha())
        if len(text) > 0:
            alphabetic_ratio = alphabetic_chars / len(text)
            if alphabetic_ratio < 0.3:
                validation_result['warnings'].append(f'Low alphabetic content ratio: {alphabetic_ratio:.2f}')
        
        # Check for excessive whitespace or special characters
        whitespace_ratio = sum(1 for c in text if c.isspace()) / len(text) if len(text) > 0 else 0
        if whitespace_ratio > 0.7:
            validation_result['warnings'].append(f'Excessive whitespace: {whitespace_ratio:.2f}')
        
        return validation_result
    
    def clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = []
        for line in text.splitlines():
            cleaned_line = ' '.join(line.split())  # Normalize whitespace
            if cleaned_line:  # Only keep non-empty lines
                lines.append(cleaned_line)
        
        # Join lines with proper spacing
        cleaned_text = '\n'.join(lines)
        
        # Remove excessive newlines (more than 2 consecutive)
        import re
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        return cleaned_text.strip()


# Global instance for easy import
text_extractor = TextExtractor()


# Helper functions for common operations

def extract_text_from_file(file_content: bytes, filename: str) -> Optional[str]:
    """
    Simple helper function to extract text from file
    
    Args:
        file_content: Raw file content as bytes
        filename: Original filename
        
    Returns:
        Extracted text or None if extraction failed
    """
    
    result = text_extractor.extract_text(file_content, filename)
    
    if result['success']:
        return text_extractor.clean_extracted_text(result['text'])
    else:
        logger.error(f"Text extraction failed for {filename}: {result['error']}")
        return None


def get_supported_file_types() -> Dict[str, str]:
    """Get dictionary of supported file types and descriptions"""
    
    return {
        '.pdf': 'Portable Document Format',
        '.docx': 'Microsoft Word Document',
        '.txt': 'Plain Text File'
    }


def is_text_extraction_available() -> bool:
    """Check if text extraction libraries are available"""
    return TEXT_EXTRACTION_AVAILABLE