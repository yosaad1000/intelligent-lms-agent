# 🎓 Intelligent LMS Agent - AWS Hackathon Project

## Overview
An AI-powered Learning Management System built with AWS Bedrock Agents, featuring voice interviews, personalized quizzes, and intelligent chat assistance.

## 🏆 Key Features (Hackathon Differentiators)
- **🎤 Voice Interview System** - AI-powered voice analysis with adaptive questioning
- **💬 Intelligent Chat** - Bedrock Agent with Knowledge Base integration
- **📝 Personalized Quizzes** - Generated from uploaded study materials
- **📁 Smart File Processing** - PDF/DOCX text extraction and indexing
- **🔐 Secure Authentication** - AWS Cognito integration

## 🏗️ Architecture
Built as 5 microservices that integrate into a single Gradio application:

1. **Authentication Service** - User management with AWS Cognito
2. **File Processor Service** - Upload, extract, and index study materials
3. **AI Chat Service** - Bedrock Agent for intelligent conversations
4. **Voice Interview Service** - Speech analysis and adaptive questioning
5. **Quiz Generator Service** - Personalized assessments

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- AWS Account with Bedrock access
- AWS CLI configured

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/intelligent-lms-agent.git
cd intelligent-lms-agent

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your AWS credentials and configuration

# Run the application
python main.py
```

### AWS Setup Required
1. **AWS Cognito User Pool** - For authentication
2. **S3 Bucket** - For file storage
3. **Bedrock Agent** - For AI intelligence
4. **Bedrock Knowledge Base** - For document indexing
5. **DynamoDB Tables** - For metadata storage

## 📁 Project Structure
```
intelligent-lms-agent/
├── src/
│   ├── auth_service/          # Authentication microservice
│   ├── file_processor/        # File processing microservice
│   ├── ai_chat/              # AI chat microservice
│   ├── voice_interview/      # Voice interview microservice
│   ├── quiz_generator/       # Quiz generation microservice
│   └── shared/               # Shared utilities
├── tests/
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── performance/          # Performance tests
├── docs/
│   ├── specs/                # Detailed specifications
│   └── api/                  # API documentation
├── infrastructure/           # AWS infrastructure code
├── demo/                     # Demo content and scenarios
└── main.py                   # Main Gradio application
```

## 🎯 Development Strategy

### Team Assignment
- **Team Member A**: Authentication + AI Chat + Voice Interview
- **Team Member B**: File Processor + Quiz Generator + Integration

### Development Timeline
- **Days 1-2**: Foundation services (Auth + File Processing)
- **Days 3-4**: Core AI features (Chat + Voice Interview)
- **Days 5-6**: Advanced features (Quiz + Integration)
- **Day 7**: Demo preparation and final polish

## 🧪 Testing
```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run with coverage
pytest --cov=src/
```

## 📊 Demo Flow (5 Minutes)
1. **Authentication** (20s) - Register and login
2. **File Upload** (20s) - Upload study materials
3. **AI Chat** (90s) - Ask questions about content
4. **Voice Interview** (2min) - **STAR FEATURE** - Voice analysis
5. **Quiz Generation** (60s) - Take personalized quiz
6. **Results** (30s) - View comprehensive analytics

## 🏅 Hackathon Highlights
- **Multi-Modal AI**: Text, voice, and visual interactions
- **AWS Integration**: Bedrock, Cognito, S3, Transcribe, DynamoDB
- **Real-time Processing**: Live voice analysis and feedback
- **Adaptive Intelligence**: Questions adapt to student performance
- **Scalable Architecture**: Microservices design for growth

## 📚 Documentation
- [Specifications](docs/specs/) - Detailed technical specifications
- [API Documentation](docs/api/) - Service APIs and integration
- [Development Guide](docs/development.md) - Setup and development workflow
- [Testing Strategy](docs/testing.md) - Comprehensive testing approach

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 Acknowledgments
- AWS Bedrock team for the amazing AI capabilities
- Gradio team for the fantastic UI framework
- AWS Hackathon organizers for the opportunity

---
**Built for AWS Agentic Hackathon 2024** 🚀