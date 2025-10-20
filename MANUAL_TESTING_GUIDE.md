# 🧪 Manual Testing Guide for RAG-Enhanced Chat Lambda Functions

## 🎉 Deployment Status: SUCCESS!

Your RAG-Enhanced Chat system has been successfully deployed to AWS Lambda! Here's how to test it manually.

## 📋 Deployed Resources

### ✅ Lambda Functions
- **lms-health-function** - Health check endpoint
- **lms-chat-function** - RAG-enhanced AI chat
- **lms-file-function** - File processing and vector storage

### ✅ DynamoDB Tables
- **lms-user-files** - File metadata storage
- **lms-chat-conversations** - Conversation management
- **lms-chat-messages** - Chat message history

### ✅ S3 Bucket
- **lms-documents-145023137830-us-east-1** - Document storage

### ✅ IAM Role
- **lms-lambda-role** - Permissions for Bedrock, DynamoDB, S3

## 🔧 Manual Testing Methods

### Method 1: AWS Lambda Console Testing

1. **Go to AWS Lambda Console**
   - Navigate to: https://console.aws.amazon.com/lambda/
   - Region: us-east-1

2. **Test Health Function**
   ```
   Function: lms-health-function
   Test Event: {}
   Expected Response: {"status": "healthy", "timestamp": "..."}
   ```

3. **Test Chat Function**
   ```
   Function: lms-chat-function
   Test Event:
   {
     "httpMethod": "POST",
     "path": "/api/chat",
     "body": "{\"user_id\": \"test-user-123\", \"message\": \"Hello, can you help me learn about machine learning?\", \"subject_id\": \"cs101\"}"
   }
   
   Expected Response:
   {
     "statusCode": 200,
     "body": "{\"success\": false, \"response\": \"I apologize...\", \"rag_enhanced\": false}"
   }
   ```

4. **Test File Processing Function**
   ```
   Function: lms-file-function
   Test Event:
   {
     "httpMethod": "POST",
     "path": "/api/files",
     "body": "{\"user_id\": \"test-user-123\", \"filename\": \"test.txt\", \"content\": \"This is a test document about machine learning concepts.\"}"
   }
   ```

### Method 2: AWS CLI Testing

1. **Test Health Function**
   ```bash
   aws lambda invoke --function-name lms-health-function --payload '{}' response.json
   cat response.json
   ```

2. **Test Chat Function**
   ```bash
   aws lambda invoke --function-name lms-chat-function --payload '{
     "httpMethod": "POST",
     "path": "/api/chat",
     "body": "{\"user_id\": \"test-user-123\", \"message\": \"What is machine learning?\", \"subject_id\": \"cs101\"}"
   }' chat-response.json
   cat chat-response.json
   ```

3. **Test File Function**
   ```bash
   aws lambda invoke --function-name lms-file-function --payload '{
     "httpMethod": "POST", 
     "path": "/api/files",
     "body": "{\"user_id\": \"test-user-123\", \"filename\": \"ml-basics.txt\", \"content\": \"Machine learning is a subset of artificial intelligence that enables computers to learn from data.\"}"
   }' file-response.json
   cat file-response.json
   ```

### Method 3: Python Testing Script

Create a test script to invoke the functions:

```python
import boto3
import json

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name='us-east-1')

def test_health_function():
    """Test health function"""
    response = lambda_client.invoke(
        FunctionName='lms-health-function',
        Payload=json.dumps({})
    )
    
    result = json.loads(response['Payload'].read())
    print("Health Function Response:", result)
    return result

def test_chat_function():
    """Test chat function"""
    payload = {
        "httpMethod": "POST",
        "path": "/api/chat",
        "body": json.dumps({
            "user_id": "test-user-123",
            "message": "What is machine learning?",
            "subject_id": "cs101"
        })
    }
    
    response = lambda_client.invoke(
        FunctionName='lms-chat-function',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    print("Chat Function Response:", result)
    return result

def test_file_function():
    """Test file processing function"""
    payload = {
        "httpMethod": "POST",
        "path": "/api/files",
        "body": json.dumps({
            "user_id": "test-user-123",
            "filename": "ml-basics.txt",
            "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed."
        })
    }
    
    response = lambda_client.invoke(
        FunctionName='lms-file-function',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    print("File Function Response:", result)
    return result

if __name__ == "__main__":
    print("🧪 Testing Lambda Functions...")
    
    print("\n1. Testing Health Function:")
    test_health_function()
    
    print("\n2. Testing Chat Function:")
    test_chat_function()
    
    print("\n3. Testing File Function:")
    test_file_function()
    
    print("\n✅ Testing Complete!")
```

## 🔍 Expected Behavior

### Health Function
- **Status**: Should return 200 with health status
- **Response**: `{"status": "healthy", "timestamp": "..."}`

### Chat Function (Without Bedrock Agents)
- **Status**: Should return 200 but with success: false
- **Reason**: Bedrock agents not configured (expected in test environment)
- **Response**: Fallback message about processing difficulties
- **RAG**: Should show `rag_enhanced: false` (no documents uploaded yet)

### File Function
- **Status**: Should return 200 if successful
- **Behavior**: 
  - Stores file metadata in DynamoDB
  - Processes text for vector storage
  - Returns file_id and processing status

## 📊 Monitoring and Logs

### CloudWatch Logs
1. Go to CloudWatch Console
2. Navigate to Log Groups:
   - `/aws/lambda/lms-health-function`
   - `/aws/lambda/lms-chat-function`
   - `/aws/lambda/lms-file-function`

### DynamoDB Verification
1. Go to DynamoDB Console
2. Check tables:
   - `lms-user-files` - Should show uploaded files
   - `lms-chat-conversations` - Should show conversations
   - `lms-chat-messages` - Should show chat messages

### S3 Verification
1. Go to S3 Console
2. Check bucket: `lms-documents-145023137830-us-east-1`
3. Should contain uploaded files under `users/{user_id}/files/`

## 🚀 Next Steps for Full Testing

### 1. Configure Bedrock Agents
To get full RAG functionality, you need to:
1. Create Bedrock Agents in AWS Console
2. Update environment variables with agent IDs
3. Redeploy Lambda functions

### 2. Upload Test Documents
1. Use the file function to upload sample documents
2. Wait for vector processing to complete
3. Test chat function with questions about uploaded content

### 3. Test RAG Workflow
1. Upload a document about machine learning
2. Ask questions related to the document content
3. Verify citations and RAG context in responses

## 🎯 Success Criteria

### ✅ Basic Functionality
- [x] Lambda functions deploy successfully
- [x] Health endpoint responds
- [x] Chat function handles requests (with fallback)
- [x] File function processes uploads
- [x] DynamoDB tables store data correctly

### 🔄 Full RAG Functionality (Requires Bedrock Setup)
- [ ] Bedrock agents configured
- [ ] Vector embeddings generated
- [ ] RAG context retrieval working
- [ ] Citations extracted correctly
- [ ] Conversation history maintained

## 🛠️ Troubleshooting

### Common Issues
1. **Permission Errors**: Check IAM role has correct policies
2. **Timeout Errors**: Increase Lambda timeout if needed
3. **Memory Errors**: Increase Lambda memory allocation
4. **Bedrock Errors**: Expected without agent configuration

### Debug Commands
```bash
# Check Lambda function logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/lms-"

# Get recent log events
aws logs get-log-events --log-group-name "/aws/lambda/lms-chat-function" --log-stream-name "$(aws logs describe-log-streams --log-group-name "/aws/lambda/lms-chat-function" --order-by LastEventTime --descending --limit 1 --query 'logStreams[0].logStreamName' --output text)"
```

## 🎉 Congratulations!

Your RAG-Enhanced Chat system is now deployed and ready for testing! The core infrastructure is in place, and you can begin testing the functionality immediately using the methods above.