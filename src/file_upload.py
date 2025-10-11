import json
import os
import boto3
import uuid
from datetime import datetime
from botocore.exceptions import ClientError
import base64

def lambda_handler(event, context):
    """
    File upload handler for student notes and documents
    Supports TXT files initially, stores in S3 and metadata in DynamoDB
    """
    
    # Handle different HTTP methods
    http_method = event.get('httpMethod', 'POST')
    
    if http_method == 'POST':
        return handle_file_upload(event)
    elif http_method == 'GET':
        return handle_get_files(event)
    elif http_method == 'DELETE':
        return handle_delete_file(event)
    else:
        return error_response(405, 'Method not allowed')

def handle_file_upload(event):
    """Handle file upload requests"""
    try:
        # Validate authentication
        user_info = validate_token(event)
        if not user_info:
            return error_response(401, 'Authentication required')
        
        user_id = user_info['username']
        
        # Parse the request body
        body = json.loads(event.get('body', '{}'))
        
        # Get file data
        file_name = body.get('fileName')
        file_content = body.get('fileContent')  # Base64 encoded
        file_type = body.get('fileType', 'text/plain')
        
        if not file_name or not file_content:
            return error_response(400, 'Missing required fields: fileName, fileContent')
        
        # Validate file type (only TXT files for now)
        if not file_name.lower().endswith('.txt'):
            return error_response(400, 'Only TXT files are supported in this version')
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Decode file content
        try:
            decoded_content = base64.b64decode(file_content).decode('utf-8')
        except Exception as e:
            return error_response(400, f'Invalid file content encoding: {str(e)}')
        
        # Upload to S3
        s3_key = f"users/{user_id}/notes/{file_id}_{file_name}"
        s3_success = upload_to_s3(decoded_content, s3_key)
        
        if not s3_success:
            return error_response(500, 'Failed to upload file to storage')
        
        # Store metadata in DynamoDB
        metadata = {
            'fileId': file_id,
            'userId': user_id,
            'fileName': file_name,
            'fileType': file_type,
            'uploadedAt': timestamp,
            'processingStatus': 'completed',  # Simple processing for TXT files
            's3Key': s3_key,
            'fileSize': len(decoded_content),
            'extractedConcepts': extract_basic_concepts(decoded_content)
        }
        
        db_success = store_file_metadata(metadata)
        
        if not db_success:
            return error_response(500, 'Failed to store file metadata')
        
        return success_response({
            'message': 'File uploaded successfully',
            'fileId': file_id,
            'fileName': file_name,
            'uploadedAt': timestamp,
            'processingStatus': 'completed',
            'extractedConcepts': metadata['extractedConcepts']
        })
        
    except json.JSONDecodeError:
        return error_response(400, 'Invalid JSON in request body')
    except Exception as e:
        return error_response(500, f'File upload error: {str(e)}')

def handle_get_files(event):
    """Handle get files requests"""
    try:
        # Validate authentication
        user_info = validate_token(event)
        if not user_info:
            return error_response(401, 'Authentication required')
        
        user_id = user_info['username']
        
        # Get user's files from DynamoDB
        files = get_user_files(user_id)
        
        return success_response({
            'files': files,
            'count': len(files)
        })
        
    except Exception as e:
        return error_response(500, f'Error retrieving files: {str(e)}')

def handle_delete_file(event):
    """Handle file deletion requests"""
    try:
        # Validate authentication
        user_info = validate_token(event)
        if not user_info:
            return error_response(401, 'Authentication required')
        
        user_id = user_info['username']
        
        # Get file ID from path parameters
        path_params = event.get('pathParameters', {})
        file_id = path_params.get('fileId')
        
        if not file_id:
            return error_response(400, 'Missing file ID in path')
        
        # Delete file and metadata
        success = delete_user_file(user_id, file_id)
        
        if success:
            return success_response({'message': 'File deleted successfully'})
        else:
            return error_response(404, 'File not found or access denied')
            
    except Exception as e:
        return error_response(500, f'Error deleting file: {str(e)}')

def validate_token(event):
    """Validate JWT token and return user info"""
    try:
        headers = event.get('headers', {})
        auth_header = (headers.get('Authorization') or 
                      headers.get('authorization') or 
                      headers.get('AUTHORIZATION'))
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        
        # Validate with Cognito
        cognito = boto3.client('cognito-idp')
        response = cognito.get_user(AccessToken=token)
        
        return {
            'username': response['Username'],
            'attributes': {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
        }
        
    except Exception:
        return None

def upload_to_s3(content, s3_key):
    """Upload file content to S3"""
    try:
        s3_bucket = os.environ.get('S3_BUCKET')
        if not s3_bucket:
            return False
        
        s3 = boto3.client('s3')
        s3.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=content,
            ContentType='text/plain',
            ServerSideEncryption='AES256'
        )
        
        return True
        
    except Exception as e:
        print(f"S3 upload error: {str(e)}")
        return False

def store_file_metadata(metadata):
    """Store file metadata in DynamoDB"""
    try:
        table_name = os.environ.get('DYNAMODB_TABLE')
        if not table_name:
            return False
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Store with composite key: PK = USER#{userId}, SK = FILE#{fileId}
        table.put_item(
            Item={
                'PK': f"USER#{metadata['userId']}",
                'SK': f"FILE#{metadata['fileId']}",
                'EntityType': 'FILE',
                'FileId': metadata['fileId'],
                'UserId': metadata['userId'],
                'FileName': metadata['fileName'],
                'FileType': metadata['fileType'],
                'UploadedAt': metadata['uploadedAt'],
                'ProcessingStatus': metadata['processingStatus'],
                'S3Key': metadata['s3Key'],
                'FileSize': metadata['fileSize'],
                'ExtractedConcepts': metadata['extractedConcepts']
            }
        )
        
        return True
        
    except Exception as e:
        print(f"DynamoDB store error: {str(e)}")
        return False

def get_user_files(user_id):
    """Get all files for a user from DynamoDB"""
    try:
        table_name = os.environ.get('DYNAMODB_TABLE')
        if not table_name:
            return []
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Query files for user
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': f"USER#{user_id}",
                ':sk': 'FILE#'
            }
        )
        
        files = []
        for item in response.get('Items', []):
            files.append({
                'fileId': item.get('FileId'),
                'fileName': item.get('FileName'),
                'fileType': item.get('FileType'),
                'uploadedAt': item.get('UploadedAt'),
                'processingStatus': item.get('ProcessingStatus'),
                'fileSize': item.get('FileSize'),
                'extractedConcepts': item.get('ExtractedConcepts', [])
            })
        
        return files
        
    except Exception as e:
        print(f"DynamoDB query error: {str(e)}")
        return []

def delete_user_file(user_id, file_id):
    """Delete a user's file from S3 and DynamoDB"""
    try:
        table_name = os.environ.get('DYNAMODB_TABLE')
        s3_bucket = os.environ.get('S3_BUCKET')
        
        if not table_name or not s3_bucket:
            return False
        
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Get file metadata first
        response = table.get_item(
            Key={
                'PK': f"USER#{user_id}",
                'SK': f"FILE#{file_id}"
            }
        )
        
        if 'Item' not in response:
            return False
        
        s3_key = response['Item'].get('S3Key')
        
        # Delete from S3
        if s3_key:
            s3 = boto3.client('s3')
            s3.delete_object(Bucket=s3_bucket, Key=s3_key)
        
        # Delete from DynamoDB
        table.delete_item(
            Key={
                'PK': f"USER#{user_id}",
                'SK': f"FILE#{file_id}"
            }
        )
        
        return True
        
    except Exception as e:
        print(f"Delete file error: {str(e)}")
        return False

def extract_basic_concepts(content):
    """Extract basic concepts from text content"""
    # Simple concept extraction for demo
    # In a real implementation, this would use NLP or AI services
    
    # Convert to lowercase and split into words
    words = content.lower().split()
    
    # Filter for potential concepts (longer words, remove common words)
    common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'a', 'an'}
    
    concepts = []
    for word in words:
        # Remove punctuation
        clean_word = ''.join(c for c in word if c.isalnum())
        
        # Keep words that are 4+ characters and not common words
        if len(clean_word) >= 4 and clean_word not in common_words:
            if clean_word not in concepts:
                concepts.append(clean_word)
    
    # Return top 10 concepts
    return concepts[:10]

def success_response(data):
    """Return a successful response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(data)
    }

def error_response(status_code, message):
    """Return an error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps({'error': message})
    }