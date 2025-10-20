"""
Health check Lambda function with enhanced error handling and validation
"""

import json
import boto3
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.exceptions import lambda_error_handler, get_cors_headers
from shared.validation import HealthResponse, create_success_response
from shared.logging_config import get_logger, log_lambda_start, log_lambda_end, log_api_call
import time

logger = get_logger(__name__)


@lambda_error_handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Health check endpoint with comprehensive service monitoring
    Tests connectivity to AWS services and returns detailed system status
    """
    
    start_time = time.time()
    correlation_id = log_lambda_start(event, context, logger)
    
    logger.info("Starting health check", extra={'correlation_id': correlation_id})
    
    health_status = {
        'success': True,
        'status': 'healthy',
        'services': {}
    }
    
    # Test DynamoDB connectivity
    try:
        start_service_time = time.time()
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('lms-user-files')
        table.load()
        
        service_duration = (time.time() - start_service_time) * 1000
        health_status['services']['dynamodb'] = 'healthy'
        
        log_api_call('dynamodb', 'table_load', service_duration, True, logger=logger)
        
    except Exception as e:
        service_duration = (time.time() - start_service_time) * 1000
        health_status['services']['dynamodb'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'
        
        log_api_call('dynamodb', 'table_load', service_duration, False, str(e), logger)
        logger.warning(f"DynamoDB health check failed: {str(e)}")
    
    # Test S3 connectivity
    try:
        start_service_time = time.time()
        s3 = boto3.client('s3')
        bucket_name = os.getenv('DOCUMENTS_BUCKET', 'lms-documents-145023137830-1760886549')
        s3.head_bucket(Bucket=bucket_name)
        
        service_duration = (time.time() - start_service_time) * 1000
        health_status['services']['s3'] = 'healthy'
        
        log_api_call('s3', 'head_bucket', service_duration, True, logger=logger)
        
    except Exception as e:
        service_duration = (time.time() - start_service_time) * 1000
        health_status['services']['s3'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'
        
        log_api_call('s3', 'head_bucket', service_duration, False, str(e), logger)
        logger.warning(f"S3 health check failed: {str(e)}")
    
    # Test Bedrock connectivity
    try:
        start_service_time = time.time()
        bedrock = boto3.client('bedrock-runtime')
        # Test with a simple model list call
        bedrock.list_foundation_models()
        
        service_duration = (time.time() - start_service_time) * 1000
        health_status['services']['bedrock'] = 'healthy'
        
        log_api_call('bedrock', 'list_models', service_duration, True, logger=logger)
        
    except Exception as e:
        service_duration = (time.time() - start_service_time) * 1000
        health_status['services']['bedrock'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'degraded'
        
        log_api_call('bedrock', 'list_models', service_duration, False, str(e), logger)
        logger.warning(f"Bedrock health check failed: {str(e)}")
    
    # Test Pinecone connectivity (configuration check)
    pinecone_api_key = os.getenv('PINECONE_API_KEY')
    if pinecone_api_key:
        health_status['services']['pinecone'] = 'configured'
        logger.info("Pinecone API key configured")
    else:
        health_status['services']['pinecone'] = 'not configured'
        health_status['status'] = 'degraded'
        logger.warning("Pinecone API key not configured")
    
    # Determine overall status
    unhealthy_services = [
        service for service, status in health_status['services'].items() 
        if 'unhealthy' in status or 'not configured' in status
    ]
    
    if unhealthy_services:
        health_status['status'] = 'degraded'
        logger.warning(f"System degraded due to unhealthy services: {unhealthy_services}")
    
    # Create validated response
    response_data = create_success_response(HealthResponse, health_status)
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    response = {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(response_data)
    }
    
    # Log completion
    duration_ms = (time.time() - start_time) * 1000
    log_lambda_end(response, duration_ms, logger, correlation_id)
    
    logger.info(f"Health check completed: {health_status['status']}", extra={
        'status': health_status['status'],
        'services_checked': len(health_status['services']),
        'unhealthy_services': len(unhealthy_services),
        'duration_ms': duration_ms
    })
    
    return response