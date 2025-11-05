#!/usr/bin/env python3
"""
Create API Gateway for the LMS API
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

def create_api_gateway():
    """Create API Gateway REST API"""
    print("🌐 Creating API Gateway...")
    
    apigateway = boto3.client('apigateway')
    
    # Create REST API
    try:
        api_response = apigateway.create_rest_api(
            name='lms-api',
            description='Intelligent LMS AI Agent API',
            endpointConfiguration={
                'types': ['REGIONAL']
            }
        )
        
        api_id = api_response['id']
        print(f"✅ API Gateway created: {api_id}")
        
    except ClientError as e:
        print(f"❌ API Gateway creation failed: {e}")
        return None
    
    return api_id

def get_root_resource_id(api_id):
    """Get the root resource ID"""
    apigateway = boto3.client('apigateway')
    
    resources = apigateway.get_resources(restApiId=api_id)
    
    for resource in resources['items']:
        if resource['path'] == '/':
            return resource['id']
    
    return None

def create_resource(api_id, parent_id, path_part):
    """Create a resource under the parent"""
    print(f"📁 Creating resource: /{path_part}")
    
    apigateway = boto3.client('apigateway')
    
    try:
        resource_response = apigateway.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        
        resource_id = resource_response['id']
        print(f"✅ Resource created: {resource_id}")
        return resource_id
        
    except ClientError as e:
        print(f"❌ Resource creation failed: {e}")
        return None

def create_method(api_id, resource_id, http_method, lambda_function_name):
    """Create a method for a resource"""
    print(f"🔧 Creating {http_method} method...")
    
    apigateway = boto3.client('apigateway')
    lambda_client = boto3.client('lambda')
    
    # Get Lambda function ARN
    try:
        lambda_response = lambda_client.get_function(FunctionName=lambda_function_name)
        lambda_arn = lambda_response['Configuration']['FunctionArn']
    except ClientError as e:
        print(f"❌ Failed to get Lambda function: {e}")
        return False
    
    # Create method
    try:
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            authorizationType='NONE'
        )
        print(f"✅ {http_method} method created")
        
    except ClientError as e:
        print(f"❌ Method creation failed: {e}")
        return False
    
    # Create integration
    try:
        region = 'us-east-1'
        account_id = '145023137830'
        
        integration_uri = f"arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=integration_uri
        )
        print(f"✅ Integration created")
        
    except ClientError as e:
        print(f"❌ Integration creation failed: {e}")
        return False
    
    # Add Lambda permission for API Gateway
    try:
        statement_id = f"apigateway-{api_id}-{resource_id}-{http_method}"
        source_arn = f"arn:aws:execute-api:{region}:{account_id}:{api_id}/*/{http_method}/*"
        
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=statement_id,
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=source_arn
        )
        print(f"✅ Lambda permission added")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print(f"ℹ️ Lambda permission already exists")
        else:
            print(f"❌ Lambda permission failed: {e}")
            return False
    
    return True

def enable_cors(api_id, resource_id):
    """Enable CORS for a resource"""
    print("🌍 Enabling CORS...")
    
    apigateway = boto3.client('apigateway')
    
    try:
        # Create OPTIONS method for CORS
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        # Create mock integration for OPTIONS
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        # Create method response for OPTIONS
        apigateway.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': False,
                'method.response.header.Access-Control-Allow-Methods': False,
                'method.response.header.Access-Control-Allow-Origin': False
            }
        )
        
        # Create integration response for OPTIONS
        apigateway.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                'method.response.header.Access-Control-Allow-Origin': "'*'"
            }
        )
        
        print("✅ CORS enabled")
        return True
        
    except ClientError as e:
        print(f"❌ CORS setup failed: {e}")
        return False

def deploy_api(api_id, stage_name='dev'):
    """Deploy the API to a stage"""
    print(f"🚀 Deploying API to {stage_name} stage...")
    
    apigateway = boto3.client('apigateway')
    
    try:
        deployment_response = apigateway.create_deployment(
            restApiId=api_id,
            stageName=stage_name,
            description=f'Deployment to {stage_name} stage'
        )
        
        deployment_id = deployment_response['id']
        print(f"✅ API deployed: {deployment_id}")
        
        # Get the invoke URL
        region = 'us-east-1'
        invoke_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage_name}"
        print(f"🌐 API URL: {invoke_url}")
        
        return invoke_url
        
    except ClientError as e:
        print(f"❌ API deployment failed: {e}")
        return None

def main():
    print("🎓 Creating API Gateway for LMS")
    print("=" * 40)
    
    try:
        # Step 1: Create API Gateway
        api_id = create_api_gateway()
        if not api_id:
            return False
        
        # Step 2: Get root resource
        root_resource_id = get_root_resource_id(api_id)
        if not root_resource_id:
            print("❌ Failed to get root resource")
            return False
        
        # Step 3: Create /hello resource
        hello_resource_id = create_resource(api_id, root_resource_id, 'hello')
        if not hello_resource_id:
            return False
        
        # Step 4: Create GET method for /hello
        if not create_method(api_id, hello_resource_id, 'GET', 'lms-hello-world'):
            return False
        
        # Step 5: Enable CORS for /hello
        enable_cors(api_id, hello_resource_id)
        
        # Step 6: Create /auth resource
        auth_resource_id = create_resource(api_id, root_resource_id, 'auth')
        if not auth_resource_id:
            return False
        
        # Step 7: Create POST method for /auth
        if not create_method(api_id, auth_resource_id, 'POST', 'lms-auth'):
            return False
        
        # Step 8: Enable CORS for /auth
        enable_cors(api_id, auth_resource_id)
        
        # Step 9: Deploy API
        api_url = deploy_api(api_id)
        if not api_url:
            return False
        
        # Save API configuration
        api_config = {
            'api_id': api_id,
            'api_url': api_url,
            'hello_endpoint': f"{api_url}/hello",
            'auth_endpoint': f"{api_url}/auth"
        }
        
        with open('api-config.json', 'w') as f:
            json.dump(api_config, f, indent=2)
        
        print("\n" + "=" * 40)
        print("🎉 API Gateway created successfully!")
        print(f"✅ API ID: {api_id}")
        print(f"✅ API URL: {api_url}")
        print(f"✅ Hello endpoint: {api_url}/hello")
        print(f"✅ Auth endpoint: {api_url}/auth")
        print("✅ Configuration saved to api-config.json")
        print("\n📋 Ready for testing!")
        
        return True
        
    except Exception as e:
        print(f"❌ API Gateway creation failed: {e}")
        return False

if __name__ == "__main__":
    main()