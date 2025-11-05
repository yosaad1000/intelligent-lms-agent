#!/usr/bin/env python3
"""
Fix Lambda IAM permissions
"""

import boto3
import json
from botocore.exceptions import ClientError

def update_lambda_policy():
    """Update the Lambda execution role policy"""
    print("🔧 Updating Lambda IAM permissions...")
    
    iam = boto3.client('iam')
    
    # Updated policy with missing permissions
    updated_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket",
                    "s3:HeadBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::lms-files-145023137830-us-east-1",
                    "arn:aws:s3:::lms-files-145023137830-us-east-1/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:UpdateItem",
                    "dynamodb:Scan",
                    "dynamodb:DescribeTable"
                ],
                "Resource": "arn:aws:dynamodb:us-east-1:145023137830:table/lms-data"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminSetUserPassword",
                    "cognito-idp:AdminInitiateAuth",
                    "cognito-idp:AdminGetUser",
                    "cognito-idp:AdminRespondToAuthChallenge",
                    "cognito-idp:GetUser",
                    "cognito-idp:DescribeUserPool",
                    "cognito-idp:DescribeUserPoolClient"
                ],
                "Resource": "arn:aws:cognito-idp:us-east-1:145023137830:userpool/us-east-1_ux07rphza"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeAgent",
                    "bedrock:ListFoundationModels"
                ],
                "Resource": "*"
            }
        ]
    }
    
    policy_name = "LMSLambdaCustomPolicy"
    policy_arn = f"arn:aws:iam::145023137830:policy/{policy_name}"
    
    try:
        # Create a new version of the policy
        response = iam.create_policy_version(
            PolicyArn=policy_arn,
            PolicyDocument=json.dumps(updated_policy),
            SetAsDefault=True
        )
        
        print(f"✅ Policy updated successfully")
        print(f"   New version: {response['PolicyVersion']['VersionId']}")
        
        return True
        
    except ClientError as e:
        print(f"❌ Policy update failed: {e}")
        return False

def main():
    print("🔧 Fixing Lambda Permissions")
    print("=" * 35)
    
    success = update_lambda_policy()
    
    if success:
        print("\n✅ Lambda permissions updated!")
        print("⏳ Waiting for changes to propagate...")
        import time
        time.sleep(10)
        print("✅ Ready for testing")
    else:
        print("\n❌ Failed to update permissions")

if __name__ == "__main__":
    main()