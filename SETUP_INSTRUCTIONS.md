# 🚀 Repository Setup Instructions

## Quick Setup (Automated)

### Option 1: Using the Setup Script (Recommended)
```bash
# Make the setup script executable
chmod +x setup_repo.sh

# Run the setup script
./setup_repo.sh
```

The script will:
- Initialize git repository
- Create GitHub repository (if you have GitHub CLI)
- Push all code to GitHub
- Provide next steps

### Option 2: Manual Setup

#### Step 1: Initialize Local Repository
```bash
# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Intelligent LMS Agent project structure

- Complete microservices architecture with 5 services
- Authentication, File Processing, AI Chat, Voice Interview, Quiz Generator
- Comprehensive specifications and task lists
- Integration testing strategy
- Gradio-based user interface
- AWS Bedrock Agents integration
- Ready for hackathon development"
```

#### Step 2: Create GitHub Repository
1. Go to https://github.com/new
2. Repository name: `intelligent-lms-agent`
3. Description: `AI-powered Learning Management System with voice interviews and personalized quizzes. Built for AWS Hackathon with Bedrock Agents.`
4. Choose Public or Private
5. **Don't** initialize with README, .gitignore, or license (we already have them)
6. Click "Create repository"

#### Step 3: Push to GitHub
```bash
# Add remote origin (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/intelligent-lms-agent.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 🤝 Collaborative Setup

### For Your Friend (Team Member B)
Once the repository is created, your friend should:

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/intelligent-lms-agent.git
cd intelligent-lms-agent

# Set up development environment
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with AWS credentials
# (You'll need to share AWS credentials or set up separate accounts)
```

### Development Workflow
```bash
# Create feature branches for each microservice
git checkout -b feature/auth-service          # Team Member A
git checkout -b feature/file-processor        # Team Member B
git checkout -b feature/ai-chat               # Team Member A
git checkout -b feature/voice-interview       # Team Member A
git checkout -b feature/quiz-generator        # Team Member B

# Work on your assigned services
# Commit and push regularly
git add .
git commit -m "Implement authentication service basic functionality"
git push origin feature/auth-service

# Create pull requests for code review
# Merge to main when ready
```

## 🎯 Next Steps After Repository Setup

### 1. AWS Environment Setup
Both team members need to set up AWS resources:

```bash
# Set up AWS credentials
aws configure

# Create required AWS resources:
# - Cognito User Pool
# - S3 Bucket
# - Bedrock Agent
# - DynamoDB Tables
```

### 2. Start Development
Follow the task lists in order:

**Team Member A (You):**
1. `.kiro/specs/auth-microservice/tasks.md`
2. `.kiro/specs/ai-chat-microservice/tasks.md` 
3. `.kiro/specs/voice-interview-microservice/tasks.md`

**Team Member B (Friend):**
1. `.kiro/specs/file-processor-microservice/tasks.md`
2. `.kiro/specs/quiz-generator-microservice/tasks.md`

### 3. Test the Application
```bash
# Run the main application
python main.py

# Open browser to http://localhost:7860
# You should see the Gradio interface with placeholder functionality
```

### 4. Development Timeline
- **Days 1-2**: Foundation services (Auth + File Processing)
- **Days 3-4**: Core AI features (Chat + Voice Interview)  
- **Days 5-6**: Advanced features (Quiz + Integration)
- **Day 7**: Demo preparation and final polish

## 📚 Key Documentation

### For Development:
- `README.md` - Project overview and quick start
- `.kiro/specs/mvp-development-strategy.md` - Complete development strategy
- `.kiro/specs/integration-testing-strategy.md` - Testing approach
- Individual service specs in `.kiro/specs/[service-name]/`

### For Implementation:
- `src/shared/config.py` - Centralized configuration
- `src/shared/utils.py` - Shared utility functions
- `main.py` - Main Gradio application (currently with placeholders)

## 🔧 Troubleshooting

### Common Issues:

#### Git Push Fails
```bash
# If you get authentication errors
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# If repository already exists
git remote set-url origin https://github.com/YOUR_USERNAME/intelligent-lms-agent.git
```

#### Python Dependencies
```bash
# If pip install fails, try upgrading pip
python -m pip install --upgrade pip

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### AWS Credentials
```bash
# Set up AWS credentials
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region (us-east-1)

# Test AWS connection
aws sts get-caller-identity
```

## 🎉 Success Criteria

After setup, you should have:
- ✅ GitHub repository created and code pushed
- ✅ Both team members can clone and run the application
- ✅ Gradio interface loads at http://localhost:7860
- ✅ AWS credentials configured
- ✅ Ready to start implementing microservices

## 🆘 Need Help?

If you encounter issues:
1. Check the troubleshooting section above
2. Review the error messages carefully
3. Ensure all prerequisites are installed
4. Verify AWS credentials are correct
5. Check that all files were committed and pushed

The repository is now ready for collaborative hackathon development! 🚀