# Create AWS infrastructure manually using AWS CLI
Write-Host "Creating AWS infrastructure manually..." -ForegroundColor Green

# Load AWS credentials
.\load-aws-env.ps1

$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$REGION = "us-east-1"

Write-Host "Account ID: $ACCOUNT_ID" -ForegroundColor Cyan
Write-Host "Region: $REGION" -ForegroundColor Cyan

# 1. Create S3 bucket
$BUCKET_NAME = "lms-files-$ACCOUNT_ID-$REGION"
Write-Host "`nCreating S3 bucket: $BUCKET_NAME" -ForegroundColor Yellow

try {
    aws s3 mb s3://$BUCKET_NAME --region $REGION
    Write-Host "S3 bucket created successfully" -ForegroundColor Green
} catch {
    Write-Host "S3 bucket creation failed or already exists: $_" -ForegroundColor Yellow
}

# 2. Create Cognito User Pool
Write-Host "`nCreating Cognito User Pool..." -ForegroundColor Yellow

$userPoolResponse = aws cognito-idp create-user-pool `
    --pool-name "lms-user-pool" `
    --policies "PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=false}" `
    --auto-verified-attributes email `
    --schema "Name=email,AttributeDataType=String,Required=true,Mutable=true" "Name=custom:role,AttributeDataType=String,Required=false,Mutable=true" `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    $userPool = $userPoolResponse | ConvertFrom-Json
    $USER_POOL_ID = $userPool.UserPool.Id
    Write-Host "User Pool created: $USER_POOL_ID" -ForegroundColor Green
    
    # Create User Pool Client
    Write-Host "Creating User Pool Client..." -ForegroundColor Yellow
    $clientResponse = aws cognito-idp create-user-pool-client `
        --user-pool-id $USER_POOL_ID `
        --client-name "lms-web-client" `
        --explicit-auth-flows ADMIN_NO_SRP_AUTH USER_PASSWORD_AUTH `
        --token-validity-units "AccessToken=hours,IdToken=hours,RefreshToken=days" `
        --access-token-validity 24 `
        --id-token-validity 24 `
        --refresh-token-validity 30 `
        --region $REGION
    
    if ($LASTEXITCODE -eq 0) {
        $client = $clientResponse | ConvertFrom-Json
        $CLIENT_ID = $client.UserPoolClient.ClientId
        Write-Host "User Pool Client created: $CLIENT_ID" -ForegroundColor Green
    } else {
        Write-Host "User Pool Client creation failed" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "User Pool creation failed" -ForegroundColor Red
    exit 1
}

# 3. Create DynamoDB table
Write-Host "`nCreating DynamoDB table..." -ForegroundColor Yellow

aws dynamodb create-table `
    --table-name "lms-data" `
    --attribute-definitions "AttributeName=PK,AttributeType=S" "AttributeName=SK,AttributeType=S" `
    --key-schema "AttributeName=PK,KeyType=HASH" "AttributeName=SK,KeyType=RANGE" `
    --billing-mode PAY_PER_REQUEST `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "DynamoDB table created successfully" -ForegroundColor Green
} else {
    Write-Host "DynamoDB table creation failed or already exists" -ForegroundColor Yellow
}

# 4. Create IAM role for Lambda (if we have permissions)
Write-Host "`nAttempting to create IAM role..." -ForegroundColor Yellow

$trustPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@

try {
    $trustPolicy | Out-File -FilePath "trust-policy.json" -Encoding utf8
    
    aws iam create-role `
        --role-name "LMSLambdaExecutionRole" `
        --assume-role-policy-document file://trust-policy.json `
        --region $REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "IAM role created successfully" -ForegroundColor Green
        
        # Attach basic execution policy
        aws iam attach-role-policy `
            --role-name "LMSLambdaExecutionRole" `
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        
        Write-Host "Basic execution policy attached" -ForegroundColor Green
    }
} catch {
    Write-Host "IAM role creation failed (may not have permissions): $_" -ForegroundColor Yellow
}

# Clean up temporary file
Remove-Item -Path "trust-policy.json" -ErrorAction SilentlyContinue

# Output configuration
Write-Host "`n=== INFRASTRUCTURE CREATED ===" -ForegroundColor Green
Write-Host "S3 Bucket: $BUCKET_NAME" -ForegroundColor Cyan
Write-Host "User Pool ID: $USER_POOL_ID" -ForegroundColor Cyan
Write-Host "Client ID: $CLIENT_ID" -ForegroundColor Cyan
Write-Host "DynamoDB Table: lms-data" -ForegroundColor Cyan

# Save configuration to file
$config = @{
    S3_BUCKET = $BUCKET_NAME
    USER_POOL_ID = $USER_POOL_ID
    CLIENT_ID = $CLIENT_ID
    DYNAMODB_TABLE = "lms-data"
    REGION = $REGION
}

$config | ConvertTo-Json | Out-File -FilePath "infrastructure-config.json" -Encoding utf8
Write-Host "`nConfiguration saved to infrastructure-config.json" -ForegroundColor Green