# OpenSearch Serverless Manual Setup Guide

## Overview
This guide walks you through manually setting up OpenSearch Serverless for the Bedrock Knowledge Base integration. OpenSearch Serverless is required for vector storage and search capabilities in the Knowledge Base.

## Prerequisites
- AWS CLI configured with appropriate permissions
- Access to AWS Console
- Completed Task 1.1 infrastructure setup

## Step-by-Step Setup

### Step 1: Create OpenSearch Serverless Collection

#### Option A: Using AWS Console (Recommended)

1. **Navigate to OpenSearch Service**
   - Go to AWS Console → OpenSearch Service
   - Click "Serverless" in the left navigation
   - Click "Create collection"

2. **Collection Configuration**
   ```
   Collection name: lms-kb-collection
   Collection type: Vector search
   Description: Vector collection for LMS Knowledge Base
   ```

3. **Security Configuration**
   - **Encryption**: Use AWS owned key (default)
   - **Network access**: Public access (for demo)
   - **Data access policy**: Create new policy

4. **Data Access Policy**
   ```json
   [
     {
       "Rules": [
         {
           "Resource": [
             "collection/lms-kb-collection"
           ],
           "Permission": [
             "aoss:CreateCollectionItems",
             "aoss:DeleteCollectionItems",
             "aoss:UpdateCollectionItems",
             "aoss:DescribeCollectionItems"
           ],
           "ResourceType": "collection"
         },
         {
           "Resource": [
             "index/lms-kb-collection/*"
           ],
           "Permission": [
             "aoss:CreateIndex",
             "aoss:DeleteIndex",
             "aoss:UpdateIndex",
             "aoss:DescribeIndex",
             "aoss:ReadDocument",
             "aoss:WriteDocument"
           ],
           "ResourceType": "index"
         }
       ],
       "Principal": [
         "arn:aws:iam::145023137830:role/BedrockKnowledgeBaseRole",
         "arn:aws:iam::145023137830:root"
       ],
       "Description": "Data access for LMS Knowledge Base"
     }
   ]
   ```

5. **Network Policy** (if using VPC)
   ```json
   [
     {
       "Rules": [
         {
           "Resource": [
             "collection/lms-kb-collection"
           ],
           "ResourceType": "collection"
         }
       ],
       "AllowFromPublic": true,
       "Description": "Public access for LMS Knowledge Base collection"
     }
   ]
   ```

#### Option B: Using AWS CLI

1. **Create Security Policies First**

   Create data access policy:
   ```bash
   aws opensearchserverless create-access-policy \
     --name lms-kb-data-policy \
     --type data \
     --policy '[{"Rules":[{"Resource":["collection/lms-kb-collection"],"Permission":["aoss:CreateCollectionItems","aoss:DeleteCollectionItems","aoss:UpdateCollectionItems","aoss:DescribeCollectionItems"],"ResourceType":"collection"},{"Resource":["index/lms-kb-collection/*"],"Permission":["aoss:CreateIndex","aoss:DeleteIndex","aoss:UpdateIndex","aoss:DescribeIndex","aoss:ReadDocument","aoss:WriteDocument"],"ResourceType":"index"}],"Principal":["arn:aws:iam::145023137830:role/BedrockKnowledgeBaseRole","arn:aws:iam::145023137830:root"],"Description":"Data access for LMS Knowledge Base"}]'
   ```

   Create network policy:
   ```bash
   aws opensearchserverless create-access-policy \
     --name lms-kb-network-policy \
     --type network \
     --policy '[{"Rules":[{"Resource":["collection/lms-kb-collection"],"ResourceType":"collection"}],"AllowFromPublic":true,"Description":"Public access for LMS Knowledge Base collection"}]'
   ```

2. **Create the Collection**
   ```bash
   aws opensearchserverless create-collection \
     --name lms-kb-collection \
     --type VECTORSEARCH \
     --description "Vector collection for LMS Knowledge Base"
   ```

### Step 2: Wait for Collection to be Active

Monitor the collection status:
```bash
aws opensearchserverless list-collections --collection-filters name=lms-kb-collection
```

Wait until status shows "ACTIVE" (usually takes 5-10 minutes).

### Step 3: Create Vector Index

Once the collection is active, create the vector index:

1. **Get Collection Endpoint**
   ```bash
   aws opensearchserverless list-collections --collection-filters name=lms-kb-collection
   ```
   Note the collection endpoint (e.g., `https://xyz.us-east-1.aoss.amazonaws.com`)

2. **Create Index Using Python Script**

Create `create_vector_index.py`:
```python
import boto3
import requests
from requests_aws4auth import AWS4Auth
import json

# Configuration
region = 'us-east-1'
service = 'aoss'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

# Collection endpoint (replace with your actual endpoint)
host = 'https://your-collection-id.us-east-1.aoss.amazonaws.com'
index_name = 'lms-vector-index'

# Index configuration for Bedrock Knowledge Base
index_body = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 512,
            "knn.algo_param.ef_construction": 512
        }
    },
    "mappings": {
        "properties": {
            "vector": {
                "type": "knn_vector",
                "dimension": 1536,  # Titan embedding dimension
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib",
                    "parameters": {
                        "ef_construction": 512,
                        "m": 16
                    }
                }
            },
            "text": {
                "type": "text"
            },
            "metadata": {
                "type": "object"
            }
        }
    }
}

# Create the index
url = f"{host}/{index_name}"
response = requests.put(url, auth=awsauth, json=index_body, headers={'Content-Type': 'application/json'})

if response.status_code == 200:
    print(f"✅ Vector index '{index_name}' created successfully")
else:
    print(f"❌ Failed to create index: {response.status_code} - {response.text}")
```

3. **Install Required Dependencies**
   ```bash
   pip install requests-aws4auth
   ```

4. **Run the Script**
   ```bash
   python create_vector_index.py
   ```

### Step 4: Update Bedrock Knowledge Base Configuration

Now that OpenSearch Serverless is set up, update the Knowledge Base:

1. **Get Collection ARN**
   ```bash
   aws opensearchserverless list-collections --collection-filters name=lms-kb-collection
   ```

2. **Update Environment Variables**
   Add to your `.env` file:
   ```env
   OPENSEARCH_COLLECTION_ARN=arn:aws:aoss:us-east-1:145023137830:collection/your-collection-id
   OPENSEARCH_COLLECTION_ENDPOINT=https://your-collection-id.us-east-1.aoss.amazonaws.com
   ```

3. **Run Knowledge Base Setup Again**
   ```bash
   python test_bedrock_kb_setup.py
   ```

### Step 5: Verify Setup

Create a verification script `verify_opensearch_setup.py`:

```python
import boto3
import requests
from requests_aws4auth import AWS4Auth
import json

def verify_opensearch_setup():
    # Check collection status
    client = boto3.client('opensearchserverless', region_name='us-east-1')
    
    try:
        response = client.list_collections(collectionFilters={'name': 'lms-kb-collection'})
        collections = response.get('collectionSummaries', [])
        
        if not collections:
            print("❌ Collection not found")
            return False
            
        collection = collections[0]
        print(f"✅ Collection Status: {collection['status']}")
        print(f"📋 Collection ARN: {collection['arn']}")
        
        if collection['status'] != 'ACTIVE':
            print("⚠️ Collection is not active yet")
            return False
            
        # Test index access
        endpoint = f"https://{collection['id']}.us-east-1.aoss.amazonaws.com"
        
        # Set up authentication
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 'us-east-1', 'aoss', session_token=credentials.token)
        
        # Test index exists
        response = requests.get(f"{endpoint}/lms-vector-index", auth=awsauth)
        
        if response.status_code == 200:
            print("✅ Vector index is accessible")
            return True
        else:
            print(f"❌ Vector index not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying setup: {e}")
        return False

if __name__ == "__main__":
    success = verify_opensearch_setup()
    if success:
        print("\n🎉 OpenSearch Serverless setup is complete!")
    else:
        print("\n❌ OpenSearch Serverless setup needs attention")
```

## Troubleshooting

### Common Issues

1. **Collection Creation Fails**
   - Check IAM permissions for OpenSearch Serverless
   - Ensure unique collection name
   - Verify region settings

2. **Access Denied Errors**
   - Review data access policies
   - Check principal ARNs in policies
   - Verify IAM role permissions

3. **Index Creation Fails**
   - Ensure collection is ACTIVE
   - Check network policies
   - Verify authentication credentials

4. **Knowledge Base Still Fails**
   - Confirm collection ARN is correct
   - Check vector index name matches configuration
   - Verify field mappings are correct

### Useful Commands

Check collection status:
```bash
aws opensearchserverless list-collections
```

Get collection details:
```bash
aws opensearchserverless batch-get-collection --names lms-kb-collection
```

List access policies:
```bash
aws opensearchserverless list-access-policies --type data
aws opensearchserverless list-access-policies --type network
```

## Cost Considerations

OpenSearch Serverless pricing:
- **OCU (OpenSearch Compute Units)**: ~$0.24/hour per OCU
- **Storage**: ~$0.024/GB per month
- **Data transfer**: Standard AWS rates

For development/demo:
- Minimum 2 OCUs required (~$11.52/day)
- Consider using time-limited collections
- Delete when not actively developing

## Security Best Practices

1. **Use least privilege access policies**
2. **Enable VPC endpoints for production**
3. **Use encryption at rest and in transit**
4. **Monitor access logs**
5. **Regularly review and rotate credentials**

## Next Steps After Setup

1. **Test Knowledge Base Creation**
   ```bash
   python test_bedrock_kb_setup.py
   ```

2. **Update Configuration**
   - Add collection ARN to environment variables
   - Update Bedrock KB configuration

3. **Test Document Ingestion**
   - Upload test documents to S3
   - Trigger Knowledge Base sync
   - Verify vector search functionality

## Summary

Once OpenSearch Serverless is set up:
- ✅ Collection created and active
- ✅ Vector index configured for embeddings
- ✅ Access policies configured
- ✅ Bedrock Knowledge Base can be created
- ✅ Ready for document ingestion and search

The manual setup is a one-time process. After completion, the Bedrock Knowledge Base will be fully functional for the file processor microservice.