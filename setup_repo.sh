#!/bin/bash

# Intelligent LMS Agent - Repository Setup Script
# This script helps you create and push the GitHub repository

echo "🎓 Intelligent LMS Agent - Repository Setup"
echo "=========================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if GitHub CLI is installed (optional)
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI detected"
    USE_GH_CLI=true
else
    echo "ℹ️  GitHub CLI not found. You'll need to create the repository manually on GitHub."
    USE_GH_CLI=false
fi

# Get repository details
echo ""
echo "📝 Repository Configuration"
echo "-------------------------"

read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter repository name (default: intelligent-lms-agent): " REPO_NAME
REPO_NAME=${REPO_NAME:-intelligent-lms-agent}

read -p "Make repository private? (y/N): " PRIVATE_REPO
if [[ $PRIVATE_REPO =~ ^[Yy]$ ]]; then
    VISIBILITY="private"
else
    VISIBILITY="public"
fi

echo ""
echo "🔧 Setting up local repository..."

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "Creating .gitignore..."
    # .gitignore content would be created here
fi

# Add all files
git add .

# Create initial commit
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    git commit -m "Initial commit: Intelligent LMS Agent project structure

- Complete microservices architecture with 5 services
- Authentication, File Processing, AI Chat, Voice Interview, Quiz Generator
- Comprehensive specifications and task lists
- Integration testing strategy
- Gradio-based user interface
- AWS Bedrock Agents integration
- Ready for hackathon development"
    echo "✅ Initial commit created"
fi

# Set up remote repository
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

echo ""
echo "🌐 Setting up remote repository..."

if [ "$USE_GH_CLI" = true ]; then
    echo "Creating repository using GitHub CLI..."
    
    if [ "$VISIBILITY" = "private" ]; then
        gh repo create "$REPO_NAME" --private --description "AI-powered Learning Management System with voice interviews and personalized quizzes. Built for AWS Hackathon with Bedrock Agents."
    else
        gh repo create "$REPO_NAME" --public --description "AI-powered Learning Management System with voice interviews and personalized quizzes. Built for AWS Hackathon with Bedrock Agents."
    fi
    
    if [ $? -eq 0 ]; then
        echo "✅ Repository created successfully on GitHub"
        
        # Add remote origin
        git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
        
        # Push to GitHub
        git branch -M main
        git push -u origin main
        
        if [ $? -eq 0 ]; then
            echo "✅ Code pushed to GitHub successfully"
        else
            echo "❌ Failed to push to GitHub"
            exit 1
        fi
    else
        echo "❌ Failed to create repository on GitHub"
        exit 1
    fi
else
    echo "Manual repository creation required:"
    echo ""
    echo "1. Go to https://github.com/new"
    echo "2. Repository name: $REPO_NAME"
    echo "3. Description: AI-powered Learning Management System with voice interviews and personalized quizzes. Built for AWS Hackathon with Bedrock Agents."
    echo "4. Visibility: $VISIBILITY"
    echo "5. Don't initialize with README, .gitignore, or license (we already have them)"
    echo "6. Click 'Create repository'"
    echo ""
    read -p "Press Enter after creating the repository on GitHub..."
    
    # Add remote origin
    git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
    
    # Push to GitHub
    git branch -M main
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo "✅ Code pushed to GitHub successfully"
    else
        echo "❌ Failed to push to GitHub. Please check your repository URL and permissions."
        exit 1
    fi
fi

echo ""
echo "🎉 Repository setup complete!"
echo "=========================="
echo ""
echo "📍 Repository URL: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
echo ""
echo "🚀 Next Steps:"
echo "1. Clone the repository on your friend's machine:"
echo "   git clone https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
echo ""
echo "2. Set up the development environment:"
echo "   cd ${REPO_NAME}"
echo "   pip install -r requirements.txt"
echo "   cp .env.example .env"
echo "   # Edit .env with your AWS credentials"
echo ""
echo "3. Start development:"
echo "   python main.py"
echo ""
echo "4. Begin implementing microservices according to the task lists in:"
echo "   - .kiro/specs/auth-microservice/tasks.md"
echo "   - .kiro/specs/file-processor-microservice/tasks.md"
echo "   - .kiro/specs/ai-chat-microservice/tasks.md"
echo "   - .kiro/specs/voice-interview-microservice/tasks.md"
echo ""
echo "📚 Documentation available in:"
echo "   - README.md - Project overview and quick start"
echo "   - .kiro/specs/ - Detailed specifications"
echo "   - .kiro/specs/mvp-development-strategy.md - Development timeline"
echo ""
echo "Happy coding! 🎯"