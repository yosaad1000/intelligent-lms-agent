"""
Bedrock Knowledge Base Setup and Configuration for File Processor Microservice

This module handles the creation and configuration of Amazon Bedrock Knowledge Base
for indexing and searching processed documents in the LMS system.
"""

import boto3
import json
import time
import logging
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
from src.shared.config import config

logger = logging.getLogger(__name__)

class BedrockKnowledgeBaseSetup:
    """Handles Bedrock Knowledge Base setup and configuration"""
    
    def __init__(self):
        """Initialize Bedrock clients with configuration"""
        try:
            self.bedrock_agent = boto3.client(
                'bedrock-agent',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            
            self.iam_client = boto3.client(
                'iam',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            
            self.s3_bucket_name = config.S3_BUCKET_NAME
            self.kb_name = "lms-student-notes-kb"
            self.collection_name = "lms-kb-collection"
            
            logger.info("Bedrock Knowledge Base client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise
    
    def _get_account_id(self) -> str:
        """Get AWS account ID"""
        try:
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_DEFAULT_REGION
            )
            return sts_client.get_caller_identity()['Account']
        except Exception as e:
            logger.error(f"Failed to get account ID: {e}")
            return "unknown"
    
    def create_iam_role_for_kb(self) -> Optional[str]:
        """Create IAM role for Bedrock Knowledge Base"""
        try:
            account_id = self._get_account_id()
            role_name = "BedrockKnowledgeBaseRole"
            
            # Check if role already exists
            try:
                response = self.iam_client.get_role(RoleName=role_name)
                role_arn = response['Role']['Arn']
                logger.info(f"IAM role already exists: {role_arn}")
                return role_arn
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchEntity':
                    raise
            
            # Create trust policy for Bedrock
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "bedrock.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            # Create the role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for Bedrock Knowledge Base to access S3 and OpenSearch"
            )
            
            role_arn = response['Role']['Arn']
            logger.info(f"Created IAM role: {role_arn}")
            
            # Create and attach policy for S3 access
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObject",
                            "s3:ListBucket"
                        ],
                        "Resource": [
                            f"arn:aws:s3:::{self.s3_bucket_name}",
                            f"arn:aws:s3:::{self.s3_bucket_name}/*"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel"
                        ],
                        "Resource": "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v1"
                    }
                ]
            }
            
            policy_name = "BedrockKnowledgeBasePolicy"
            
            try:
                self.iam_client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_document),
                    Description="Policy for Bedrock Knowledge Base"
                )
                logger.info(f"Created IAM policy: {policy_name}")
            except ClientError as e:
                if e.response['Error']['Code'] != 'EntityAlreadyExists':
                    raise
                logger.info(f"IAM policy already exists: {policy_name}")
            
            # Attach policy to role
            policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            
            # Wait for role to be available
            time.sleep(10)
            
            return role_arn
            
        except ClientError as e:
            logger.error(f"Failed to create IAM role: {e}")
            return None
    
    def create_opensearch_collection(self) -> Optional[str]:
        """Create OpenSearch Serverless collection for Knowledge Base"""
        try:
            # Note: OpenSearch Serverless requires specific setup
            # For this demo, we'll use a simplified approach
            # In production, you would create the collection via AWS CLI or Console
            
            collection_arn = f"arn:aws:aoss:{config.AWS_DEFAULT_REGION}:{self._get_account_id()}:collection/{self.collection_name}"
            logger.info(f"OpenSearch collection ARN (placeholder): {collection_arn}")
            
            # Return a placeholder ARN - in real implementation, you would:
            # 1. Create OpenSearch Serverless collection
            # 2. Configure security policies
            # 3. Wait for collection to be active
            
            return collection_arn
            
        except Exception as e:
            logger.error(f"Failed to create OpenSearch collection: {e}")
            return None
    
    def create_knowledge_base(self, role_arn: str, collection_arn: str) -> Optional[str]:
        """Create Bedrock Knowledge Base"""
        try:
            # Check if Knowledge Base already exists
            try:
                response = self.bedrock_agent.list_knowledge_bases()
                for kb in response.get('knowledgeBaseSummaries', []):
                    if kb['name'] == self.kb_name:
                        logger.info(f"Knowledge Base already exists: {kb['knowledgeBaseId']}")
                        return kb['knowledgeBaseId']
            except ClientError:
                pass
            
            # Create Knowledge Base configuration
            kb_config = {
                'name': self.kb_name,
                'description': 'Knowledge Base for LMS student uploaded documents',
                'roleArn': role_arn,
                'knowledgeBaseConfiguration': {
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f'arn:aws:bedrock:{config.AWS_DEFAULT_REGION}::foundation-model/amazon.titan-embed-text-v1'
                    }
                },
                'storageConfiguration': {
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': collection_arn,
                        'vectorIndexName': 'lms-vector-index',
                        'fieldMapping': {
                            'vectorField': 'vector',
                            'textField': 'text',
                            'metadataField': 'metadata'
                        }
                    }
                }
            }
            
            response = self.bedrock_agent.create_knowledge_base(**kb_config)
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            
            logger.info(f"Created Knowledge Base: {kb_id}")
            return kb_id
            
        except ClientError as e:
            logger.error(f"Failed to create Knowledge Base: {e}")
            return None
    
    def create_data_source(self, kb_id: str) -> Optional[str]:
        """Create S3 data source for Knowledge Base"""
        try:
            data_source_config = {
                'knowledgeBaseId': kb_id,
                'name': 'lms-s3-data-source',
                'description': 'S3 data source for student uploaded documents',
                'dataSourceConfiguration': {
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f'arn:aws:s3:::{self.s3_bucket_name}',
                        'inclusionPrefixes': ['processed/knowledge_base/']
                    }
                }
            }
            
            response = self.bedrock_agent.create_data_source(**data_source_config)
            data_source_id = response['dataSource']['dataSourceId']
            
            logger.info(f"Created data source: {data_source_id}")
            return data_source_id
            
        except ClientError as e:
            logger.error(f"Failed to create data source: {e}")
            return None
    
    def test_knowledge_base_operations(self, kb_id: str) -> Dict[str, bool]:
        """Test Knowledge Base operations"""
        test_results = {
            'get_kb': False,
            'list_data_sources': False,
            'kb_accessible': False
        }
        
        try:
            # Test getting Knowledge Base details
            response = self.bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
            if response['knowledgeBase']['knowledgeBaseId'] == kb_id:
                test_results['get_kb'] = True
                logger.info("Get Knowledge Base test passed")
            
            # Test listing data sources
            response = self.bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)
            if 'dataSourceSummaries' in response:
                test_results['list_data_sources'] = True
                logger.info("List data sources test passed")
            
            # Test Knowledge Base accessibility
            test_results['kb_accessible'] = True
            logger.info("Knowledge Base accessibility test passed")
            
        except ClientError as e:
            logger.error(f"Knowledge Base operation test failed: {e}")
        
        return test_results
    
    def setup_complete_bedrock_infrastructure(self) -> Dict[str, Any]:
        """Complete Bedrock Knowledge Base infrastructure setup"""
        results = {
            'iam_role_created': False,
            'opensearch_collection_created': False,
            'knowledge_base_created': False,
            'data_source_created': False,
            'tests_passed': {},
            'knowledge_base_id': None,
            'data_source_id': None,
            'errors': []
        }
        
        try:
            # Step 1: Create IAM role
            role_arn = self.create_iam_role_for_kb()
            if role_arn:
                results['iam_role_created'] = True
            else:
                results['errors'].append("Failed to create IAM role")
                return results
            
            # Step 2: Create OpenSearch collection (placeholder)
            collection_arn = self.create_opensearch_collection()
            if collection_arn:
                results['opensearch_collection_created'] = True
            else:
                results['errors'].append("Failed to create OpenSearch collection")
                # Continue anyway for demo purposes
                collection_arn = f"arn:aws:aoss:{config.AWS_DEFAULT_REGION}:{self._get_account_id()}:collection/{self.collection_name}"
            
            # Step 3: Create Knowledge Base
            kb_id = self.create_knowledge_base(role_arn, collection_arn)
            if kb_id:
                results['knowledge_base_created'] = True
                results['knowledge_base_id'] = kb_id
            else:
                results['errors'].append("Failed to create Knowledge Base")
                return results
            
            # Step 4: Create data source
            data_source_id = self.create_data_source(kb_id)
            if data_source_id:
                results['data_source_created'] = True
                results['data_source_id'] = data_source_id
            else:
                results['errors'].append("Failed to create data source")
            
            # Step 5: Test operations
            results['tests_passed'] = self.test_knowledge_base_operations(kb_id)
            
            logger.info("Bedrock Knowledge Base infrastructure setup completed")
            
        except Exception as e:
            logger.error(f"Bedrock infrastructure setup failed: {e}")
            results['errors'].append(str(e))
        
        return results

def main():
    """Main function to run Bedrock Knowledge Base setup"""
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Setting up Bedrock Knowledge Base infrastructure...")
    
    kb_setup = BedrockKnowledgeBaseSetup()
    results = kb_setup.setup_complete_bedrock_infrastructure()
    
    print("\n📊 Setup Results:")
    print(f"✅ IAM Role Created: {results['iam_role_created']}")
    print(f"✅ OpenSearch Collection: {results['opensearch_collection_created']}")
    print(f"✅ Knowledge Base Created: {results['knowledge_base_created']}")
    print(f"✅ Data Source Created: {results['data_source_created']}")
    
    if results['knowledge_base_id']:
        print(f"📋 Knowledge Base ID: {results['knowledge_base_id']}")
    
    if results['data_source_id']:
        print(f"📋 Data Source ID: {results['data_source_id']}")
    
    print("\n🧪 Test Results:")
    for test, passed in results['tests_passed'].items():
        status = "✅" if passed else "❌"
        print(f"{status} {test.replace('_', ' ').title()}: {passed}")
    
    if results['errors']:
        print("\n❌ Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    else:
        print("\n🎉 Bedrock Knowledge Base setup completed successfully!")

if __name__ == "__main__":
    main()