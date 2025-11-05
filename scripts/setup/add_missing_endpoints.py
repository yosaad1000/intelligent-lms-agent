#!/usr/bin/env python3
"""
Add missing API endpoints for file processing
"""

import boto3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EndpointAdder:
    """Add missing API Gateway endpoints"""
    
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
    
    def get_resources(self):
        """Get all API resources"""
        response = self.apigateway.get_resources(restApiId=self.api_id)
        return response['items']
    
    def find_resource_by_path(self, path):
        """Find resource by path"""
        resources = self.get_resources()
        for resource in resources:
            if resource['path'] == path:
                return resource['id']
        return None
    
    def create_resource_if_not_exists(self, parent_id, path_part):
        """Create resource if it doesn't exist"""
        full_path = f"/{path_part}" if parent_id else path_part
        
        # Check if exists
        existing_id = self.find_resource_by_path(full_path)
        if existing_id:
            logger.info(f"Resource {full_path} already exists: {existing_id}")
            return existing_id
        
        # Create new resource
        resource = self.apigateway.create_resource(
            restApiId=self.api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        
        logger.info(f"Created resource {full_path}: {resource['id']}")
        return resource['id']
    
    def add_method_and_integration(self, resource_id, method):
        """Add method and Lambda integration"""
        
        # Create method
        try:
            self.apigateway.put_method(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod=method,
                authorizationType='NONE'
            )
        except self.apigateway.exceptions.ConflictException:
            logger.info(f"{method} method already exists")
        
        # Create integration
        integration_uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{self.lambda_arn}/invocations"
        
        try:
            self.apigateway.put_integration(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod=method,
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=integration_uri
            )
            logger.info(f"Added {method} integration")
        except self.apigateway.exceptions.ConflictException:
            logger.info(f"{method} integration already exists")
    
    def add_all_missing_endpoints(self):
        """Add all missing endpoints"""
        
        logger.info("🔧 Adding missing API endpoints...")
        
        # Get root and files resource IDs
        root_id = self.find_resource_by_path('/')
        files_id = self.find_resource_by_path('/files')
        
        if not root_id:
            raise Exception("Root resource not found")
        
        if not files_id:
            raise Exception("Files resource not found")
        
        # 1. Add /files/process endpoint
        logger.info("📁 Adding /files/process endpoint...")
        process_id = self.create_resource_if_not_exists(files_id, 'process')
        self.add_method_and_integration(process_id, 'POST')
        
        # 2. Add /files/status endpoint  
        logger.info("📊 Adding /files/status endpoint...")
        status_id = self.create_resource_if_not_exists(files_id, 'status')
        self.add_method_and_integration(status_id, 'GET')
        
        # 3. Add /files/{file_id} endpoint for individual file operations
        logger.info("📄 Adding /files/{file_id} endpoint...")
        file_id_resource = self.create_resource_if_not_exists(files_id, '{file_id}')
        self.add_method_and_integration(file_id_resource, 'GET')
        self.add_method_and_integration(file_id_resource, 'PUT')
        self.add_method_and_integration(file_id_resource, 'DELETE')
        
        # 4. Add /files/{file_id}/process endpoint
        logger.info("⚙️ Adding /files/{file_id}/process endpoint...")
        file_process_id = self.create_resource_if_not_exists(file_id_resource, 'process')
        self.add_method_and_integration(file_process_id, 'POST')
        
        # 5. Deploy API
        logger.info("🚀 Deploying updated API...")
        deployment = self.apigateway.create_deployment(
            restApiId=self.api_id,
            stageName='prod',
            description='Added missing endpoints'
        )
        
        logger.info(f"✅ API deployed: {deployment['id']}")
        
        return True

def main():
    """Main function"""
    
    print("🔧 Adding Missing API Endpoints")
    print("=" * 50)
    
    adder = EndpointAdder()
    
    try:
        success = adder.add_all_missing_endpoints()
        
        if success:
            print("\n✅ All missing endpoints added successfully!")
            print("\n📋 Available endpoints:")
            print("- GET    /files                    (list files)")
            print("- POST   /files                    (create upload)")
            print("- GET    /files/status             (get file status)")
            print("- POST   /files/process            (process file)")
            print("- GET    /files/{file_id}          (get specific file)")
            print("- PUT    /files/{file_id}          (update file)")
            print("- DELETE /files/{file_id}          (delete file)")
            print("- POST   /files/{file_id}/process  (process specific file)")
            
            print(f"\n🔗 API URL: https://q1ox8qhf97.execute-api.us-east-1.amazonaws.com/prod")
            print("\n🧪 Test with: python test_file_processing.py")
        
    except Exception as e:
        print(f"❌ Failed to add endpoints: {e}")

if __name__ == "__main__":
    main()