# Development startup script for LMS Frontend
Write-Host "🚀 Starting LMS Frontend in Development Mode..." -ForegroundColor Green

# Check if Node.js is installed
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js is not installed. Please install Node.js first." -ForegroundColor Red
    exit 1
}

# Check if npm is installed
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "❌ npm is not installed. Please install npm first." -ForegroundColor Red
    exit 1
}

# Install dependencies if node_modules doesn't exist
if (!(Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Create .env.local if it doesn't exist
if (!(Test-Path ".env.local")) {
    Write-Host "⚙️ Creating .env.local file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env.local" -ErrorAction SilentlyContinue
}

Write-Host "✅ Environment configured for development mode:" -ForegroundColor Green
Write-Host "   - Mock Authentication: Enabled" -ForegroundColor Cyan
Write-Host "   - Mock Bedrock Agent: Enabled" -ForegroundColor Cyan
Write-Host "   - Dummy Data: Enabled" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Quick Login Options:" -ForegroundColor Yellow
Write-Host "   - Teacher: teacher@demo.com" -ForegroundColor Cyan
Write-Host "   - Student: student@demo.com" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Starting development server..." -ForegroundColor Green

# Start the development server
npm run dev