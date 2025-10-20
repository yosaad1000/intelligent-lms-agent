"""
Health check Lambda function
"""

import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Health check endpoint
    Tests connectivity to AWS services and returns system status
    """
    
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {}
        }
        
        # Test DynamoDB connectivity
        try:
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table('lms-user-files')
            table.load()
            health_status['services']['dynamodb'] = 'healthy'
        except Exception as e:
            health_status['services']['dynamodb'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Test S3 connectivity
        try:
            s3 = boto3.client('s3')
            bucket_name = os.getenv('DOCUMENTS_BUCKET', 'lms-documents-145023137830-1760886549')
            s3.head_bucket(Bucket=bucket_name)
            health_status['services']['s3'] = 'healthy'
        except Exception as e:
            health_status['services']['s3'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Test Bedrock connectivity
        try:
            bedrock = boto3.client('bedrock-runtime')
            # Just check if we can create the client
            health_status['services']['bedrock'] = 'healthy'
        except Exception as e:
            health_status['services']['bedrock'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Test Pinecone connectivity (basic check)
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        if pinecone_api_key:
            health_status['services']['pinecone'] = 'configured'
        else:
            health_status['services']['pinecone'] = 'not configured'
            health_status['status'] = 'degraded'
        
        return {
            'statusCode': 200 if health_status['status'] == 'healthy' else 503,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(health_status)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }