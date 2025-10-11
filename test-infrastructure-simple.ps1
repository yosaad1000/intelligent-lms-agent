# Simple test script for LMS infrastructure components
Write-Host "🎓 Intelligent LMS AI Agent - Infrastructure Test" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Gray

# Load AWS credentials
.\load-aws-env.ps1

# Load configuration
$config = Get-Content "infrastructure-config.json" | ConvertFrom-Json
Write-Host "📋 Configuration loaded:" -ForegroundColor Cyan
Write-Host "   S3 Bucket: $($config.S3_BUCKET)" -ForegroundColor White
Write-Host "   User Pool: $($config.USER_POOL_ID)" -ForegroundColor White
Write-Host "   Client ID: $($config.CLIENT_ID)" -ForegroundColor White
Write-Host "   DynamoDB: $($config.DYNAMODB_TABLE)" -ForegroundColor White
Write-Host "   Region: $($config.REGION)" -ForegroundColor White

$results = @()

# Test S3 bucket access
Write-Host "`n🗄️ Testing S3 bucket access..." -ForegroundColor Yellow
aws s3api head-bucket --bucket $config.S3_BUCKET --region $config.REGION 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ S3 bucket '$($config.S3_BUCKET)' is accessible" -ForegroundColor Green
    $results += $true
} else {
    Write-Host "❌ S3 bucket access failed" -ForegroundColor Red
    $results += $false
}

# Test DynamoDB table access
Write-Host "`n🗃️ Testing DynamoDB table access..." -ForegroundColor Yellow
aws dynamodb describe-table --table-name $config.DYNAMODB_TABLE --region $config.REGION 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ DynamoDB table '$($config.DYNAMODB_TABLE)' is accessible" -ForegroundColor Green
    $results += $true
} else {
    Write-Host "❌ DynamoDB table access failed" -ForegroundColor Red
    $results += $false
}

# Test Cognito User Pool access
Write-Host "`n🔐 Testing Cognito User Pool access..." -ForegroundColor Yellow
aws cognito-idp describe-user-pool --user-pool-id $config.USER_POOL_ID --region $config.REGION 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Cognito User Pool is accessible" -ForegroundColor Green
    Write-Host "   🆔 Pool ID: $($config.USER_POOL_ID)" -ForegroundColor White
    Write-Host "   🔑 Client ID: $($config.CLIENT_ID)" -ForegroundColor White
    $results += $true
} else {
    Write-Host "❌ Cognito User Pool access failed" -ForegroundColor Red
    $results += $false
}

# Test Bedrock access
Write-Host "`n🤖 Testing Bedrock access..." -ForegroundColor Yellow
aws bedrock list-foundation-models --region $config.REGION 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Bedrock is accessible" -ForegroundColor Green
    $results += $true
} else {
    Write-Host "❌ Bedrock access failed" -ForegroundColor Red
    $results += $false
}

# Test Cognito authentication
Write-Host "`n🧪 Testing Cognito authentication..." -ForegroundColor Yellow
$testEmail = "test@example.com"
$testPassword = "TestPass123"

# Try to create a test user (ignore errors if user exists)
aws cognito-idp admin-create-user --user-pool-id $config.USER_POOL_ID --username $testEmail --user-attributes Name=email,Value=$testEmail Name=email_verified,Value=true Name=custom:role,Value=student --temporary-password $testPassword --message-action SUPPRESS --region $config.REGION 2>$null

# Set permanent password (ignore errors if already set)
aws cognito-idp admin-set-user-password --user-pool-id $config.USER_POOL_ID --username $testEmail --password $testPassword --permanent --region $config.REGION 2>$null

# Test login
aws cognito-idp admin-initiate-auth --user-pool-id $config.USER_POOL_ID --client-id $config.CLIENT_ID --auth-flow ADMIN_NO_SRP_AUTH --auth-parameters USERNAME=$testEmail,PASSWORD=$testPassword --region $config.REGION 2>$null | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Authentication test successful!" -ForegroundColor Green
    Write-Host "   📝 Test user: $testEmail" -ForegroundColor White
    Write-Host "   🔑 Login: Successful" -ForegroundColor White
    $results += $true
} else {
    Write-Host "❌ Authentication test failed" -ForegroundColor Red
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
    Write-Host "`n🎉 All infrastructure components are working correctly!" -ForegroundColor Green
    Write-Host "✅ MANUAL TEST CHECKPOINT COMPLETED" -ForegroundColor Green
    Write-Host "`nInfrastructure Summary:" -ForegroundColor Yellow
    Write-Host "• S3 bucket for file storage: ✅ Ready" -ForegroundColor White
    Write-Host "• Cognito User Pool for authentication: ✅ Ready" -ForegroundColor White
    Write-Host "• DynamoDB table for data storage: ✅ Ready" -ForegroundColor White
    Write-Host "• Bedrock for AI capabilities: ✅ Ready" -ForegroundColor White
    Write-Host "• Test user authentication: ✅ Working" -ForegroundColor White
    Write-Host "`n🚀 Ready to proceed with API Gateway and Lambda deployment!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ Some components need attention before proceeding" -ForegroundColor Yellow
}