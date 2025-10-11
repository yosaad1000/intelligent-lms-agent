# IAM Permissions Reference

## Required AWS Service Permissions

### Core Services
```json
{
  "cognito-idp": [
    "AdminCreateUser", 
    "AdminSetUserPassword", 
    "ListUsers"
  ],
  "s3": [
    "GetObject", 
    "PutObject", 
    "DeleteObject"
  ],
  "dynamodb": [
    "PutItem", 
    "GetItem", 
    "Query", 
    "UpdateItem", 
    "Scan"
  ],
  "bedrock": [
    "InvokeModel", 
    "CreateKnowledgeBase", 
    "InvokeAgent"
  ],
  "transcribe": [
    "StartTranscriptionJob", 
    "GetTranscriptionJob"
  ],
  "lambda": [
    "InvokeFunction"
  ],
  "apigateway": [
    "POST", 
    "GET", 
    "DELETE"
  ],
  "sagemaker": [
    "InvokeEndpoint", 
    "CreateFeatureGroup"
  ],
  "logs": [
    "CreateLogGroup", 
    "CreateLogStream", 
    "PutLogEvents"
  ],
  "secretsmanager": [
    "GetSecretValue"
  ]
}
```

## Security Principles
- **Least Privilege**: Grant minimum permissions required
- **Resource-Specific**: Scope permissions to specific resources when possible
- **User Isolation**: Students can only access their own data
- **Role Separation**: Different roles for students, teachers, and system functions

## IAM Best Practices
- Use IAM roles for Lambda functions
- Implement resource-based policies for S3 buckets
- Use Cognito groups for role-based access control
- Regular permission audits and cleanup