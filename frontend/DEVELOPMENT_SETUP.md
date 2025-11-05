# Frontend Development Setup Guide

This guide provides detailed instructions for setting up the LMS AI Agent frontend development environment.

## Prerequisites

### Required Software

1. **Node.js** (version 18 or higher)
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify installation: `node --version` and `npm --version`

2. **Git** (for version control)
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify installation: `git --version`

3. **Code Editor** (recommended: VS Code)
   - Download from [code.visualstudio.com](https://code.visualstudio.com/)
   - Install recommended extensions (see below)

### AWS Account Setup

1. **AWS Account**: Ensure you have access to AWS Bedrock services
2. **IAM Permissions**: Your AWS user/role needs permissions for:
   - Bedrock Agent Runtime
   - S3 (for document storage)
   - API Gateway (for backend APIs)

3. **Bedrock Agent**: Ensure the LMS AI Agent is deployed and accessible

### Supabase Setup

1. **Create Supabase Project**:
   - Go to [supabase.com](https://supabase.com/)
   - Create a new project
   - Note down the project URL and anon key

2. **Configure Authentication**:
   - Enable email/password authentication
   - Configure redirect URLs for your development environment

## Installation Steps

### 1. Clone and Navigate

```bash
# If you haven't cloned the repository yet
git clone <repository-url>
cd lms-ai-agent/frontend
```

### 2. Install Dependencies

```bash
# Install all npm dependencies
npm install

# Verify installation
npm list --depth=0
```

### 3. Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env.local
```

Edit `.env.local` with your specific configuration:

```env
# AWS Configuration
VITE_AWS_REGION=us-east-1
VITE_BEDROCK_AGENT_ID=your-actual-agent-id
VITE_BEDROCK_AGENT_ALIAS_ID=production

# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# API Configuration
VITE_API_BASE_URL=https://your-api-gateway-url.amazonaws.com

# Development Settings
VITE_DEVELOPMENT_MODE=true
VITE_MOCK_DATA_ENABLED=true
VITE_ENABLE_TESTING_MODE=true

# Optional: Google Integration
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_GOOGLE_API_KEY=your-google-api-key
```

### 4. Verify Setup

```bash
# Start the development server
npm run dev

# The application should open at http://localhost:5173
```

## Development Environment

### VS Code Extensions (Recommended)

Install these extensions for the best development experience:

```json
{
  "recommendations": [
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense",
    "ms-vscode.vscode-json",
    "bradlc.vscode-tailwindcss"
  ]
}
```

### Development Scripts

The following npm scripts are available:

```bash
# Development
npm run dev              # Start development server with hot reload
npm run build            # Build for production
npm run preview          # Preview production build locally

# Testing
npm run test             # Run tests once
npm run test:watch       # Run tests in watch mode

# Code Quality
npm run lint             # Run ESLint
```

## Development Workflow

### 1. Feature Development

```bash
# Create a new feature branch
git checkout -b feature/your-feature-name

# Start development server
npm run dev

# Make your changes...

# Run tests
npm run test

# Build to ensure no build errors
npm run build
```

### 2. Testing Your Changes

```bash
# Run all tests
npm run test

# Run specific test files
npm run test -- --grep "ComponentName"

# Run tests in watch mode during development
npm run test:watch
```

## Environment-Specific Configuration

### Development Mode Features

When `VITE_DEVELOPMENT_MODE=true`:
- Mock data services are available
- Additional debugging information
- Development-only UI components
- Relaxed authentication requirements

### Mock Data

Enable mock data with `VITE_MOCK_DATA_ENABLED=true`:
- Simulated API responses
- Test user accounts
- Sample documents and quizzes
- Offline development capability

## Troubleshooting

### Common Setup Issues

1. **Node Version Issues**:
   ```bash
   # Check Node version
   node --version
   
   # If using nvm, switch to correct version
   nvm use 18
   ```

2. **Dependency Installation Failures**:
   ```bash
   # Clear npm cache
   npm cache clean --force
   
   # Delete node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Environment Variables Not Loading**:
   - Ensure file is named `.env.local` (not `.env`)
   - Verify all variables start with `VITE_`
   - Restart development server after changes
   - Check for syntax errors in the .env file

4. **Build Errors**:
   ```bash
   # Check for unused imports
   npm run lint
   
   # Verify all environment variables are available
   npm run build
   ```

### AWS Integration Issues

1. **Bedrock Agent Connection**:
   - Verify agent ID and alias in environment variables
   - Check AWS credentials configuration
   - Ensure proper CORS settings on API Gateway

2. **Authentication Issues**:
   - Verify Supabase project configuration
   - Check redirect URLs in Supabase dashboard
   - Ensure proper JWT token handling

## Getting Help

If you encounter issues:

1. Check this troubleshooting guide
2. Review the main README.md
3. Check existing GitHub issues
4. Create a new issue with detailed information

Happy coding! 🚀