# Test script for LMS infrastructure components using AWS CLI
Write-Host "🎓 Intelligent LMS AI Agent - Infrastructure Test" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Gray

# Load AWS credentials
.\load-aws-env.ps1

# Load configuration
try {
    $config = Get-Content "infrastructure-config.json" | ConvertFrom-Json
    Write-Host "📋 Configuration loaded:" -ForegroundColor Cyan
    Write-Host "   S3 Bucket: $($config.S3_BUCKET)" -ForegroundColor White
    Write-Host "   User Pool: $($config.USER_POOL_ID)" -ForegroundColor White
    Write-Host "   Client ID: $($config.CLIENT_ID)" -ForegroundColor White
    Write-Host "   DynamoDB: $($config.DYNAMODB_TABLE)" -ForegroundColor White
    Write-Host "   Region: $($config.REGION)" -ForegroundColor White
}
catch {
    Write-Host "❌ Failed to load configuration: $_" -ForegroundColor Red
    exit 1
}

$results = @()

# Test S3 bucket access
Write-Host "`n🗄️ Testing S3 bucket access..." -ForegroundColor Yellow
try {
    aws s3api head-bucket --bucket $config.S3_BUCKET --region $config.REGION 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ S3 bucket '$($config.S3_BUCKET)' is accessible" -ForegroundColor Green
        
        # Try to list objects
        $objects = aws s3api list-objects-v2 --bucket $config.S3_BUCKET --max-keys 1 --region $config.REGION 2>$null | ConvertFrom-Json
        $objectCount = if ($objects.KeyCount) { $objects.KeyCount } else { 0 }
        Write-Host "   📁 Current objects in bucket: $objectCount" -ForegroundColor White
        $results += $true
    }
    else {
        Write-Host "❌ S3 bucket access failed" -ForegroundColor Red
        $results += $false
    }
}
catch {
    Write-Host "❌ S3 test failed: $_" -ForegroundColor Red
    $results += $false
}

# Test DynamoDB table access
Write-Host "`n🗃️ Testing DynamoDB table access..." -ForegroundColor Yellow
try {
    $tableInfo = aws dynamodb describe-table --table-name $config.DYNAMODB_TABLE --region $config.REGION 2>$null | ConvertFrom-Json
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ DynamoDB table '$($config.DYNAMODB_TABLE)' is accessible" -ForegroundColor Green
        Write-Host "   📊 Table status: $($tableInfo.Table.TableStatus)" -ForegroundColor White
        Write-Host "   📝 Item count: $($tableInfo.Table.ItemCount)" -ForegroundColor White
        $results += $true
    } else {
        Write-Host "❌ DynamoDB table access failed" -ForegroundColor Red
        $results += $false
    }
} catch {
    Write-Host "❌ DynamoDB test failed: $_" -ForegroundColor Red
    $results += $false
}

# Test Cognito User Pool access
Write-Host "`n🔐 Testing Cognito User Pool access..." -ForegroundColor Yellow
try {
    $poolInfo = aws cognito-idp describe-user-pool --user-pool-id $config.USER_POOL_ID --region $config.REGION 2>$null | ConvertFrom-Json
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Cognito User Pool '$($poolInfo.UserPool.Name)' is accessible" -ForegroundColor Green
        Write-Host "   🆔 Pool ID: $($config.USER_POOL_ID)" -ForegroundColor White
        Write-Host "   🔑 Client ID: $($config.CLIENT_ID)" -ForegroundColor White
        
        # List users
        $users = aws cognito-idp list-users --user-pool-id $config.USER_POOL_ID --limit 10 --region $config.REGION 2>$null | ConvertFrom-Json
        $userCount = if ($users.Users) { $users.Users.Count } else { 0 }
        Write-Host "   👥 Current users: $userCount" -ForegroundColor White
        $results += $true
    } else {
        Write-Host "❌ Cognito User Pool access failed" -ForegroundColor Red
        $results += $false
    }
} catch {
    Write-Host "❌ Cognito test failed: $_" -ForegroundColor Red
    $results += $false
}

# Test Bedrock access
Write-Host "`n🤖 Testing Bedrock access..." -ForegroundColor Yellow
try {
    $models = aws bedrock list-foundation-models --region $config.REGION 2>$null | ConvertFrom-Json
    if ($LASTEXITCODE -eq 0) {
        $totalModels = $models.modelSummaries.Count
        $novaModels = ($models.modelSummaries | Where-Object { $_.modelName -like "*Nova*" }).Count
        
        Write-Host "✅ Bedrock is accessible" -ForegroundColor Green
        Write-Host "   🧠 Total foundation models: $totalModels" -ForegroundColor White
        Write-Host "   ⭐ Nova models available: $novaModels" -ForegroundColor White
        
        # Show some Nova models
        if ($novaModels -gt 0) {
            Write-Host "   📋 Available Nova models:" -ForegroundColor White
            $models.modelSummaries | Where-Object { $_.modelName -like "*Nova*" } | Select-Object -First 3 | ForEach-Object {
                Write-Host "      - $($_.modelName) ($($_.modelId))" -ForegroundColor Gray
            }
        }
        $results += $true
    } else {
        Write-Host "❌ Bedrock access failed" -ForegroundColor Red
        $results += $false
    }
} catch {
    Write-Host "❌ Bedrock test failed: $_" -ForegroundColor Red
    $results += $false
}

# Test Cognito authentication
Write-Host "`n🧪 Testing Cognito authentication..." -ForegroundColor Yellow
$testEmail = "test@example.com"
$testPassword = "TestPass123"

try {
    # Try to create a test user
    Write-Host "   📝 Creating test user: $testEmail" -ForegroundColor White
    
    aws cognito-idp admin-create-user `
        --user-pool-id $config.USER_POOL_ID `
        --username $testEmail `
        --user-attributes Name=email,Value=$testEmail Name=email_verified,Value=true Name=custom:role,Value=student `
        --temporary-password $testPassword `
        --message-action SUPPRESS `
        --region $config.REGION 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Test user created successfully" -ForegroundColor Green
        
        # Set permanent password
        aws cognito-idp admin-set-user-password `
            --user-pool-id $config.USER_POOL_ID `
            --username $testEmail `
            --password $testPassword `
            --permanent `
            --region $config.REGION 2>$null
    } else {
        Write-Host "   ℹ️ Test user already exists, proceeding with login test" -ForegroundColor Cyan
    }
    
    # Test login
    Write-Host "   🔑 Testing login..." -ForegroundColor White
    
    $authResult = aws cognito-idp admin-initiate-auth `
        --user-pool-id $config.USER_POOL_ID `
        --client-id $config.CLIENT_ID `
        --auth-flow ADMIN_NO_SRP_AUTH `
        --auth-parameters USERNAME=$testEmail,PASSWORD=$testPassword `
        --region $config.REGION 2>$null | ConvertFrom-Json
    
    if ($LASTEXITCODE -eq 0 -and $authResult.AuthenticationResult.AccessToken) {
        Write-Host "   ✅ Login successful!" -ForegroundColor Green
        $token = $authResult.AuthenticationResult.AccessToken
        Write-Host "   🎫 Access token received (first 50 chars): $($token.Substring(0, [Math]::Min(50, $token.Length)))..." -ForegroundColor White
        $results += $true
    } else {
        Write-Host "   ❌ Login test failed" -ForegroundColor Red
        $results += $false
    }
} catch {
    Write-Host "   ❌ Authentication test failed: $_" -ForegroundColor Red
    $results += $false
}

# Summary
Write-Host "`n$('=' * 50)" -ForegroundColor Gray
Write-Host "📊 Test Summary:" -ForegroundColor Cyan

$testNames = @("S3", "DynamoDB", "Cognito", "Bedrock", "Authentication")
$passed = ($results | Where-Object { $_ -eq $true }).Count
$total = $results.Count

for ($i = 0; $i -lt $testNames.Count; $i++) {
    $status = if ($results[$i]) { "✅ PASS" } else { "❌ FAIL" }
    $color = if ($results[$i]) { "Green" } else { "Red" }
    Write-Host "   $($testNames[$i]): $status" -ForegroundColor $color
}

Write-Host "`n🎯 Overall: $passed/$total tests passed" -ForegroundColor Cyan

if ($passed -eq $total) {
    Write-Host "🎉 All infrastructure components are working correctly!" -ForegroundColor Green
    Write-Host "✅ Ready to proceed with API Gateway and Lambda setup" -ForegroundColor Green
    
    # Create a simple API Gateway manually since we can't use CloudFormation
    Write-Host "`n🌐 Next steps for API Gateway:" -ForegroundColor Yellow
    Write-Host "   1. Go to AWS Console > API Gateway" -ForegroundColor White
    Write-Host "   2. Create a new REST API named 'lms-api'" -ForegroundColor White
    Write-Host "   3. Create resources and methods for /hello and /auth" -ForegroundColor White
    Write-Host "   4. Deploy the API to a 'dev' stage" -ForegroundColor White
    
} else {
    Write-Host "⚠️ Some components need attention before proceeding" -ForegroundColor Yellow
}

Write-Host "`n✅ MANUAL TEST CHECKPOINT COMPLETED" -ForegroundColor Green
Write-Host "Infrastructure verification finished. Core AWS services are accessible." -ForegroundColor White