import json
import os
import boto3
from datetime import datetime

def lambda_handler(event, context):
    """
    Simple Hello World Lambda function to test AWS infrastructure connectivity
    """
    
    # Get environment variables
    user_pool_id = os.environ.get('USER_POOL_ID')
    s3_bucket = os.environ.get('S3_BUCKET')
    dynamodb_table = os.environ.get('DYNAMODB_TABLE')
    
    # Test AWS service connectivity
    services_status = {}
    
    try:
        # Test DynamoDB connectivity
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(dynamodb_table)
        table.table_status  # This will raise an exception if table doesn't exist
        services_status['dynamodb'] = 'connected'
    except Exception as e:
        services_status['dynamodb'] = f'error: {str(e)}'
    
    try:
        # Test S3 connectivity
        s3 = boto3.client('s3')
        s3.head_bucket(Bucket=s3_bucket)
        services_status['s3'] = 'connected'
    except Exception as e:
        services_status['s3'] = f'error: {str(e)}'
    
    try:
        # Test Cognito connectivity
        cognito = boto3.client('cognito-idp')
        cognito.describe_user_pool(UserPoolId=user_pool_id)
        services_status['cognito'] = 'connected'
    except Exception as e:
        services_status['cognito'] = f'error: {str(e)}'
    
    try:
        # Test Bedrock connectivity
        bedrock = boto3.client('bedrock')
        bedrock.list_foundation_models()
        services_status['bedrock'] = 'connected'
    except Exception as e:
        services_status['bedrock'] = f'error: {str(e)}'
    
    # Prepare response
    response_body = {
        'message': 'Hello from Intelligent LMS AI Agent!',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': {
            'user_pool_id': user_pool_id,
            's3_bucket': s3_bucket,
            'dynamodb_table': dynamodb_table
        },
        'services_status': services_status,
        'request_info': {
            'method': event.get('httpMethod'),
            'path': event.get('path'),
            'headers': event.get('headers', {})
        }
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(response_body, indent=2)
    }