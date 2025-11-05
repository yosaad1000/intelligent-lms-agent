# Deploy script for Intelligent LMS AI Agent
Write-Host "Deploying Intelligent LMS AI Agent Infrastructure..." -ForegroundColor Green

# Load AWS credentials
.\load-aws-env.ps1

# Create deployment bucket if it doesn't exist
$BUCKET_NAME = "lms-deployment-$(Get-Random -Minimum 1000 -Maximum 9999)"
Write-Host "Creating deployment bucket: $BUCKET_NAME" -ForegroundColor Yellow

try {
    aws s3 mb s3://$BUCKET_NAME --region us-east-1
    Write-Host "Deployment bucket created successfully" -ForegroundColor Green
} catch {
    Write-Host "Bucket creation failed or already exists: $_" -ForegroundColor Yellow
}

# Package and deploy the CloudFormation stack
Write-Host "Packaging CloudFormation template..." -ForegroundColor Yellow

aws cloudformation package `
    --template-file infrastructure/template.yaml `
    --s3-bucket $BUCKET_NAME `
    --output-template-file infrastructure/packaged-template.yaml `
    --region us-east-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Template packaged successfully" -ForegroundColor Green
    
    Write-Host "Deploying CloudFormation stack..." -ForegroundColor Yellow
    
    aws cloudformation deploy `
        --template-file infrastructure/packaged-template.yaml `
        --stack-name lms-infrastructure `
        --capabilities CAPABILITY_IAM `
        --region us-east-1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Stack deployed successfully!" -ForegroundColor Green
        
        # Get stack outputs
        Write-Host "Getting stack outputs..." -ForegroundColor Yellow
        aws cloudformation describe-stacks `
            --stack-name lms-infrastructure `
            --query 'Stacks[0].Outputs' `
            --region us-east-1
    } else {
        Write-Host "Stack deployment failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Template packaging failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Deployment completed!" -ForegroundColor Green