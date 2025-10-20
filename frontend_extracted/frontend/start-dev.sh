#!/bin/bash

# Development startup script for LMS Frontend
echo "🚀 Starting LMS Frontend in Development Mode..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "⚙️ Creating .env.local file..."
    cp .env.example .env.local 2>/dev/null || true
fi

echo "✅ Environment configured for development mode:"
echo "   - Mock Authentication: Enabled"
echo "   - Mock Bedrock Agent: Enabled"
echo "   - Dummy Data: Enabled"
echo ""
echo "🎯 Quick Login Options:"
echo "   - Teacher: teacher@demo.com"
echo "   - Student: student@demo.com"
echo ""
echo "🌐 Starting development server..."

# Start the development server
npm run dev