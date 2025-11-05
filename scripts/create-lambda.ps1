# Create Lambda functions manually
Write-Host "Creating Lambda functions..." -ForegroundColor Green

# Load AWS credentials
.\load-aws-env.ps1

# Load configuration
$config = Get-Content "infrastructure-config.json" | ConvertFrom-Json

# Create deployment package
Write-Host "Creating deployment package..." -ForegroundColor Yellow

# Create a temporary directory for the package
$tempDir = "lambda-package"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir

# Copy source files
Copy-Item "src\*.py" -Destination $tempDir

# Create zip file
$zipFile = "lambda-deployment.zip"
if (Test-Path $zipFile) {
    Remove-Item $zipFile
}

# Use PowerShell to create zip
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory((Resolve-Path $tempDir).Path, (Resolve-Path ".").Path + "\$zipFile")

Write-Host "Deployment package created: $zipFile" -ForegroundColor Green

# Try to create Lambda functions (may fail due to IAM permissions)
Write-Host "`nAttempting to create Lambda functions..." -ForegroundColor Yellow

# Hello World Function
try {
    aws lambda create-function `
        --function-name "lms-hello-world" `
        --runtime "python3.9" `
        --role "arn:aws:iam::$($config.ACCOUNT_ID):role/LMSLambdaExecutionRole" `
        --handler "hello_world.lambda_handler" `
        --zip-file "fileb://$zipFile" `
        --environment "Variables={USER_POOL_ID=$($config.USER_POOL_ID),USER_POOL_CLIENT_ID=$($config.CLIENT_ID),S3_BUCKET=$($config.S3_BUCKET),DYNAMODB_TABLE=$($config.DYNAMODB_TABLE)}" `
        --region $($config.REGION)
    
    Write-Host "Hello World Lambda function created" -ForegroundColor Green
} catch {
    Write-Host "Lambda function creation failed (IAM permissions needed): $_" -ForegroundColor Yellow
}

# Auth Function
try {
    aws lambda create-function `
        --function-name "lms-auth" `
        --runtime "python3.9" `
        --role "arn:aws:iam::$($config.ACCOUNT_ID):role/LMSLambdaExecutionRole" `
        --handler "auth.lambda_handler" `
        --zip-file "fileb://$zipFile" `
        --environment "Variables={USER_POOL_ID=$($config.USER_POOL_ID),USER_POOL_CLIENT_ID=$($config.CLIENT_ID),S3_BUCKET=$($config.S3_BUCKET),DYNAMODB_TABLE=$($config.DYNAMODB_TABLE)}" `
        --region $($config.REGION)
    
    Write-Host "Auth Lambda function created" -ForegroundColor Green
} catch {
    Write-Host "Auth Lambda function creation failed (IAM permissions needed): $_" -ForegroundColor Yellow
}

# Clean up
Remove-Item -Recurse -Force $tempDir
Remove-Item $zipFile

Write-Host "`nLambda function creation attempted. Check AWS Console for results." -ForegroundColor Cyan