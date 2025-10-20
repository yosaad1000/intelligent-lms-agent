"""
Shared utility functions for all microservices
"""

import uuid
import hashlib
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import json

logger = logging.getLogger(__name__)

def generate_uuid() -> str:
    """Generate a unique UUID string"""
    return str(uuid.uuid4())

def generate_session_id(user_id: str) -> str:
    """Generate a session ID for a user"""
    timestamp = str(int(time.time()))
    return f"{user_id}_{timestamp}_{generate_uuid()[:8]}"

def hash_string(text: str) -> str:
    """Generate SHA-256 hash of a string"""
    return hashlib.sha256(text.encode()).hexdigest()

def get_current_timestamp() -> int:
    """Get current Unix timestamp"""
    return int(time.time())

def get_current_iso_timestamp() -> str:
    """Get current ISO format timestamp"""
    return datetime.now(timezone.utc).isoformat()

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename

def extract_file_extension(filename: str) -> str:
    """Extract file extension from filename"""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def is_supported_file_type(filename: str) -> bool:
    """Check if file type is supported"""
    supported_extensions = {'pdf', 'docx', 'txt', 'doc'}
    extension = extract_file_extension(filename)
    return extension in supported_extensions

def create_s3_key(user_id: str, folder: str, filename: str) -> str:
    """Create S3 key with proper structure"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = sanitize_filename(filename)
    return f"users/{user_id}/{folder}/{timestamp}_{safe_filename}"

def parse_s3_key(s3_key: str) -> Dict[str, str]:
    """Parse S3 key to extract components"""
    parts = s3_key.split('/')
    if len(parts) >= 4:
        return {
            'user_id': parts[1],
            'folder': parts[2],
            'filename': '/'.join(parts[3:])
        }
    return {}

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely serialize object to JSON"""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def extract_concepts_simple(text: str) -> list[str]:
    """Simple concept extraction from text"""
    # This is a basic implementation
    # In production, you'd use more sophisticated NLP
    
    import re
    
    # Convert to lowercase for processing
    text_lower = text.lower()
    
    # Common academic concepts (expandable)
    concept_patterns = {
        'thermodynamics': r'\b(thermodynamics?|entropy|enthalpy|heat|temperature|energy)\b',
        'physics': r'\b(physics?|force|momentum|velocity|acceleration|gravity)\b',
        'chemistry': r'\b(chemistry?|molecule|atom|reaction|bond|element)\b',
        'mathematics': r'\b(math|equation|function|derivative|integral|calculus)\b',
        'biology': r'\b(biology?|cell|dna|protein|organism|evolution)\b',
        'computer_science': r'\b(programming|algorithm|data|structure|software)\b'
    }
    
    identified_concepts = []
    for concept, pattern in concept_patterns.items():
        if re.search(pattern, text_lower):
            identified_concepts.append(concept)
    
    return identified_concepts

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity (0-1)"""
    # Basic implementation using word overlap
    # In production, use more sophisticated methods
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Retry function with exponential backoff"""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
    
    return wrapper

class Timer:
    """Simple timer context manager"""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"{self.description} completed in {duration:.2f} seconds")
    
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise
    
    return wrapper