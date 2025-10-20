#!/usr/bin/env python3
"""
Properly fix API Gateway configuration
"""

import boto3
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIGatewayFixer:
    """Fix API Gateway configuration properly"""
    
    def __init__(self):
        self.apigateway = boto3.client('apigateway')
        self.lambda_client = boto3.client('lambda')
        self.api_id = 'q1ox8qhf97'
        self.function_name = 'lms-enhanced-file-processing'
        
        # Get AWS account info
        sts = boto3.client('sts')
        self.account_id = sts.get_caller_identity()['Account']
        self.region = boto3.Session().region_name or 'us-east-1'
        
        self.lambda_arn = f"arn:aws:lambda:{self.region}:{self.account_id}:function:{self.function_name}"
        
    def get_api_resources(self):
        """Get all API resources"""
        try:
            response = self.apigateway.get_resources(restApiId=self.api_id)
            return response['items']
        except Exception as e:
            logger.error(f"Failed to get resources: {e}")
            return []
    
    def delete_existing_resources(self):
        """Delete existing problematic resources"""
        logger.info("🧹 Cleaning up existing resources...")
        
        resources = self.get_api_resources()
        
        for resource in resources:
            # Don't delete root resource
            if resource['path'] == '/':
                continue
                
            try:
                logger.info(f"Deleting resource: {resource['path']}")
                self.apigateway.delete_resource(
                    restApiId=self.api_id,
                    resourceId=resource['id']
                )
            except Exception as e:
                logger.warning(f"Could not delete resource {resource['path']}: {e}")
    
    def create_files_resource(self):
        """Create /files resource properly"""
        logger.info("📁 Creating /files resource...")
        
        # Get root resource
        resources = self.get_api_resources()
        root_id = None
        
        for resource in resources:
            if resource['path'] == '/':
                root_id = resource['id']
                break
        
        if not root_id:
            raise Exception("Root resource not found")
        
        # Create /files resource
        files_resource = self.apigateway.create_resource(
            restApiId=self.api_id,
            parentId=root_id,
            pathPart='files'
        )
        
        logger.info(f"Created /files resource: {files_resource['id']}")
        return files_resource['id']
    
    def setup_method_and_integration(self, resource_id, method):
        """Setup method and Lambda integration"""
        logger.info(f"🔧 Setting up {method} method...")
        
        # Create method
        self.apigateway.put_method(
            restApiId=self.api_id,
            resourceId=resource_id,
            httpMethod=method,
            authorizationType='NONE',
            requestParameters={}
        )
        
        # Create integration
        integration_uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{self.lambda_arn}/invocations"
        
        self.apigateway.put_integration(
            restApiId=self.api_id,
            resourceId=resource_id,
            httpMethod=method,
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=integration_uri
        )
        
        logger.info(f"✅ {method} method and integration created")
    
    def setup_cors(self, resource_id):
        """Setup CORS for OPTIONS method"""
        logger.info("🌐 Setting up CORS...")
        
        # Create OPTIONS method
        self.apigateway.put_method(
            restApiId=self.api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        # Create mock integration for OPTIONS
        self.apigateway.put_integration(
            restApiId=self.api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        # Setup method response
        self.apigateway.put_method_response(
            restApiId=self.api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': False,
                'method.response.header.Access-Control-Allow-Methods': False,
                'method.response.header.Access-Control-Allow-Origin': False
            }
        )
        
        # Setup integration response
        self.apigateway.put_integration_response(
            restApiId=self.api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                'method.response.header.Access-Control-Allow-Origin': "'*'"
            }
        )
        
        logger.info("✅ CORS configured")
    
    def add_lambda_permission(self):
        """Add Lambda permission for API Gateway"""
        logger.info("🔐 Adding Lambda permission...")
        
        try:
            # Remove existing permission if it exists
            try:
                self.lambda_client.remove_permission(
                    FunctionName=self.function_name,
                    StatementId='api-gateway-invoke'
                )
            except:
                pass
            
            # Add new permission
            self.lambda_client.add_permission(
                FunctionName=self.function_name,
                StatementId='api-gateway-invoke',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{self.region}:{self.account_id}:{self.api_id}/*/*'
            )
            
            logger.info("✅ Lambda permission added")
            
        except Exception as e:
            logger.error(f"Failed to add Lambda permission: {e}")
            raise
    
    def deploy_api(self):
        """Deploy the API"""
        logger.info("🚀 Deploying API...")
        
        try:
            deployment = self.apigateway.create_deployment(
                restApiId=self.api_id,
                stageName='prod',
                description='Fixed API Gateway deployment'
            )
            
            logger.info(f"✅ API deployed: {deployment['id']}")
            return deployment['id']
            
        except Exception as e:
            logger.error(f"Failed to deploy API: {e}")
            raise
    
    def test_api(self):
        """Test the fixed API"""
        logger.info("🧪 Testing fixed API...")
        
        import requests
        import time
        
        # Wait for deployment to propagate
        time.sleep(10)
        
        api_url = f"https://{self.api_id}.execute-api.{self.region}.amazonaws.com/prod"
        
        try:
            response = requests.get(f"{api_url}/files", params={'user_id': 'test-user-123'})
            
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response: {response.text}")
            
            if response.status_code == 200:
                logger.info("✅ API is working!")
                return True
            else:
                logger.error(f"❌ API returned: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ API test failed: {e}")
            return False
    
    def fix_complete_api(self):
        """Complete API Gateway fix"""
        logger.info("🔧 Starting complete API Gateway fix...")
        
        try:
            # Step 1: Clean up existing resources
            self.delete_existing_resources()
            
            # Step 2: Create /files resource
            files_resource_id = self.create_files_resource()
            
            # Step 3: Setup GET method and integration
            self.setup_method_and_integration(files_resource_id, 'GET')
            
            # Step 4: Setup POST method and integration
            self.setup_method_and_integration(files_resource_id, 'POST')
            
            # Step 5: Setup CORS
            self.setup_cors(files_resource_id)
            
            # Step 6: Add Lambda permission
            self.add_lambda_permission()
            
            # Step 7: Deploy API
            deployment_id = self.deploy_api()
            
            # Step 8: Test API
            api_working = self.test_api()
            
            return {
                'success': True,
                'deployment_id': deployment_id,
                'api_working': api_working,
                'api_url': f"https://{self.api_id}.execute-api.{self.region}.amazonaws.com/prod"
            }
            
        except Exception as e:
            logger.error(f"❌ Complete fix failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

def main():
    """Main fix function"""
    
    print("🔧 Fixing API Gateway Configuration")
    print("=" * 50)
    
    fixer = APIGatewayFixer()
    result = fixer.fix_complete_api()
    
    print("\n📋 Fix Results:")
    if result['success']:
        print("✅ API Gateway fixed successfully!")
        print(f"🚀 Deployment ID: {result['deployment_id']}")
        print(f"🌐 API URL: {result['api_url']}")
        print(f"🧪 API Working: {'Yes' if result['api_working'] else 'No'}")
        
        if result['api_working']:
            print("\n🎉 API is ready! You can now:")
            print("1. Open test_enhanced_file_processing.html")
            print("2. Upload files and test processing")
            print("3. Test Textract and Comprehend integration")
        else:
            print("\n⚠️ API deployed but not responding correctly. Check logs.")
    else:
        print(f"❌ Fix failed: {result['error']}")

if __name__ == "__main__":
    main()