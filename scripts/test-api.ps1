# Test script for LMS API endpoints
Write-Host "Testing LMS API endpoints..." -ForegroundColor Green

# Load AWS credentials
.\load-aws-env.ps1

# Get the API Gateway URL from CloudFormation stack
Write-Host "Getting API Gateway URL..." -ForegroundColor Yellow
$API_URL = aws cloudformation describe-stacks `
    --stack-name lms-infrastructure `
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' `
    --output text `
    --region us-east-1

if (-not $API_URL) {
    Write-Host "Could not retrieve API URL. Make sure the stack is deployed." -ForegroundColor Red
    exit 1
}

Write-Host "API URL: $API_URL" -ForegroundColor Cyan

# Test Hello World endpoint
Write-Host "`nTesting Hello World endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/hello" -Method GET
    Write-Host "Hello World Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Hello World test failed: $_" -ForegroundColor Red
}

# Test Authentication endpoint - Register a test user
Write-Host "`nTesting Authentication - Register..." -ForegroundColor Yellow
$registerBody = @{
    action = "register"
    email = "test@example.com"
    password = "TestPass123"
    role = "student"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/auth" -Method POST -Body $registerBody -ContentType "application/json"
    Write-Host "Registration Response:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Registration test failed (user might already exist): $_" -ForegroundColor Yellow
}

# Test Authentication endpoint - Login
Write-Host "`nTesting Authentication - Login..." -ForegroundColor Yellow
$loginBody = @{
    action = "login"
    email = "test@example.com"
    password = "TestPass123"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/auth" -Method POST -Body $loginBody -ContentType "application/json"
    Write-Host "Login Response:" -ForegroundColor Green
    # Don't show full tokens for security, just show structure
    $sanitized = @{
        message = $response.message
        user = $response.user
        tokens_present = @{
            access_token = if ($response.tokens.access_token) { "Present" } else { "Missing" }
            id_token = if ($response.tokens.id_token) { "Present" } else { "Missing" }
            refresh_token = if ($response.tokens.refresh_token) { "Present" } else { "Missing" }
        }
    }
    $sanitized | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Login test failed: $_" -ForegroundColor Red
}

Write-Host "`nAPI testing completed!" -ForegroundColor Green