"""
Shared configuration management for all microservices
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration management"""
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: str = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY: str = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_DEFAULT_REGION: str = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # AWS Cognito
    COGNITO_USER_POOL_ID: str = os.getenv('COGNITO_USER_POOL_ID', '')
    COGNITO_CLIENT_ID: str = os.getenv('COGNITO_CLIENT_ID', '')
    
    # AWS S3
    S3_BUCKET_NAME: str = os.getenv('S3_BUCKET_NAME', '')
    
    # AWS Bedrock
    BEDROCK_AGENT_ID: str = os.getenv('BEDROCK_AGENT_ID', '')
    BEDROCK_AGENT_ALIAS_ID: str = os.getenv('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
    KNOWLEDGE_BASE_ID: str = os.getenv('KNOWLEDGE_BASE_ID', '')
    
    # DynamoDB
    DYNAMODB_TABLE_PREFIX: str = os.getenv('DYNAMODB_TABLE_PREFIX', 'lms')
    CHAT_HISTORY_TABLE: str = os.getenv('CHAT_HISTORY_TABLE', 'lms-chat-history')
    FILE_METADATA_TABLE: str = os.getenv('FILE_METADATA_TABLE', 'lms-file-metadata')
    USER_PROGRESS_TABLE: str = os.getenv('USER_PROGRESS_TABLE', 'lms-user-progress')
    
    # Application
    APP_NAME: str = os.getenv('APP_NAME', 'Intelligent LMS Agent')
    APP_VERSION: str = os.getenv('APP_VERSION', '1.0.0')
    DEBUG: bool = os.getenv('DEBUG', 'True').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # Gradio
    GRADIO_SERVER_NAME: str = os.getenv('GRADIO_SERVER_NAME', '0.0.0.0')
    GRADIO_SERVER_PORT: int = int(os.getenv('GRADIO_SERVER_PORT', 7860))
    GRADIO_SHARE: bool = os.getenv('GRADIO_SHARE', 'False').lower() == 'true'
    
    # Security
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
    SESSION_TIMEOUT: int = int(os.getenv('SESSION_TIMEOUT', 3600))
    
    # Performance
    MAX_FILE_SIZE_MB: int = int(os.getenv('MAX_FILE_SIZE_MB', 10))
    MAX_CONCURRENT_UPLOADS: int = int(os.getenv('MAX_CONCURRENT_UPLOADS', 5))
    CACHE_TTL_SECONDS: int = int(os.getenv('CACHE_TTL_SECONDS', 300))
    
    # Voice Processing
    MAX_AUDIO_DURATION_SECONDS: int = int(os.getenv('MAX_AUDIO_DURATION_SECONDS', 300))
    AUDIO_SAMPLE_RATE: int = int(os.getenv('AUDIO_SAMPLE_RATE', 16000))
    TRANSCRIBE_LANGUAGE_CODE: str = os.getenv('TRANSCRIBE_LANGUAGE_CODE', 'en-US')
    
    # Demo
    DEMO_MODE: bool = os.getenv('DEMO_MODE', 'False').lower() == 'true'
    DEMO_USER_EMAIL: str = os.getenv('DEMO_USER_EMAIL', 'demo@example.com')
    DEMO_USER_PASSWORD: str = os.getenv('DEMO_USER_PASSWORD', 'DemoPass123')
    
    @classmethod
    def validate_config(cls) -> list[str]:
        """Validate required configuration and return list of missing items"""
        missing = []
        
        required_configs = [
            ('AWS_ACCESS_KEY_ID', cls.AWS_ACCESS_KEY_ID),
            ('AWS_SECRET_ACCESS_KEY', cls.AWS_SECRET_ACCESS_KEY),
            ('COGNITO_USER_POOL_ID', cls.COGNITO_USER_POOL_ID),
            ('COGNITO_CLIENT_ID', cls.COGNITO_CLIENT_ID),
            ('S3_BUCKET_NAME', cls.S3_BUCKET_NAME),
        ]
        
        for name, value in required_configs:
            if not value:
                missing.append(name)
        
        return missing
    
    @classmethod
    def get_aws_config(cls) -> dict:
        """Get AWS configuration dictionary"""
        return {
            'aws_access_key_id': cls.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': cls.AWS_SECRET_ACCESS_KEY,
            'region_name': cls.AWS_DEFAULT_REGION
        }

# Global config instance
config = Config()