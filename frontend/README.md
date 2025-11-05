# LMS AI Agent - Frontend Application

A modern React-based frontend for the Learning Management System (LMS) AI Agent, built with TypeScript, Vite, and Tailwind CSS.

## Overview

This frontend application provides a comprehensive interface for students and teachers to interact with the LMS AI Agent system. It features role-based dashboards, document management, quiz generation, learning analytics, and AI-powered chat functionality.

## Technology Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 4.4.5
- **Styling**: Tailwind CSS 3.3.0
- **Routing**: React Router DOM 6.8.1
- **Testing**: Vitest with React Testing Library
- **AWS Integration**: AWS SDK for Bedrock Agent Runtime
- **Authentication**: Supabase Auth
- **UI Components**: Heroicons React

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- AWS account with Bedrock Agent access
- Supabase project (for authentication)

### Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Environment Setup**:
   ```bash
   cp .env.example .env.local
   ```
   
   Configure the following environment variables:
   ```env
   # AWS Configuration
   VITE_AWS_REGION=us-east-1
   VITE_BEDROCK_AGENT_ID=your-agent-id
   VITE_BEDROCK_AGENT_ALIAS_ID=production
   
   # Supabase Configuration
   VITE_SUPABASE_URL=your-supabase-url
   VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
   
   # API Configuration
   VITE_API_BASE_URL=https://your-api-gateway-url
   
   # Development Mode
   VITE_DEVELOPMENT_MODE=true
   VITE_MOCK_DATA_ENABLED=true
   ```

3. **Start Development Server**:
   ```bash
   npm run dev
   ```
   
   Or use the provided scripts:
   ```bash
   # Windows
   .\start-dev.ps1
   
   # Unix/Linux/macOS
   ./start-dev.sh
   ```

4. **Access the Application**:
   - Development: http://localhost:5173
   - The app will automatically open in your default browser

## Project Structure

```
frontend/
├── public/                     # Static assets
├── src/
│   ├── components/            # Reusable UI components
│   │   ├── AIChat/           # AI chat interface components
│   │   ├── Assignment/       # Assignment management
│   │   ├── GoogleIntegration/ # Google services integration
│   │   ├── Layout/           # Layout components (Header, Sidebar)
│   │   ├── notifications/    # Notification system
│   │   ├── Session/          # Session management
│   │   ├── Student/          # Student-specific components
│   │   └── ui/               # Generic UI components
│   ├── contexts/             # React contexts for state management
│   ├── hooks/                # Custom React hooks
│   ├── lib/                  # Third-party library configurations
│   ├── pages/                # Page components
│   │   ├── shared/           # Shared pages (Help, Settings)
│   │   ├── student/          # Student-specific pages
│   │   └── teacher/          # Teacher-specific pages
│   ├── services/             # API and external service integrations
│   ├── types/                # TypeScript type definitions
│   ├── utils/                # Utility functions
│   └── test/                 # Test files and utilities
├── scripts/                   # Deployment and utility scripts
├── package.json              # Dependencies and scripts
├── vite.config.ts            # Vite configuration
├── tailwind.config.js        # Tailwind CSS configuration
└── tsconfig.json             # TypeScript configuration
```

## Key Features

### 🎓 Role-Based Dashboards
- **Student Dashboard**: Course progress, assignments, chat interface
- **Teacher Dashboard**: Class management, analytics, AI configuration

### 📚 Document Management
- Upload and process various document formats (PDF, DOCX, TXT)
- AI-powered document analysis and summarization
- Integration with AWS Textract for advanced text extraction

### 🤖 AI Chat Interface
- Real-time chat with Bedrock AI Agent
- Context-aware responses based on uploaded documents
- Support for voice interactions and interviews

### 📊 Learning Analytics
- Progress tracking and performance metrics
- Visual charts and reports
- Personalized learning recommendations

### 🧪 Quiz Generation
- AI-powered quiz creation from documents
- Multiple question types and difficulty levels
- Automated grading and feedback

### 🔔 Notification System
- Real-time notifications for assignments and updates
- Customizable notification preferences
- Mobile-optimized notification display

## Development

### Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build

# Testing
npm run test         # Run tests once
npm run test:watch   # Run tests in watch mode

# Linting
npm run lint         # Run ESLint
```

### Environment Modes

The application supports multiple environment modes:

- **Development**: Full mock data and testing features enabled
- **Staging**: Production-like environment with test data
- **Production**: Live environment with real AWS services

### Testing

The application includes comprehensive testing:

```bash
# Run all tests
npm run test

# Run specific test suites
npm run test -- --grep "component"
npm run test -- --grep "integration"
npm run test -- --grep "e2e"
```

Test coverage includes:
- Unit tests for components and utilities
- Integration tests for service interactions
- End-to-end tests for user workflows
- Accessibility tests for compliance

### Code Quality

- **ESLint**: Configured with React and TypeScript rules
- **TypeScript**: Strict type checking enabled
- **Prettier**: Code formatting (configured in package.json)
- **Husky**: Pre-commit hooks for quality checks

## Deployment

### Development Deployment

```bash
# Build the application
npm run build

# Preview the build locally
npm run preview
```

### Production Deployment

The application supports multiple deployment targets:

1. **Vercel** (Recommended):
   ```bash
   # Deploy to Vercel
   npm run deploy:vercel
   ```

2. **AWS S3 + CloudFront**:
   ```bash
   # Build and deploy to AWS
   ./scripts/deploy.sh
   ```

3. **Docker**:
   ```bash
   # Build Docker image
   docker build -t lms-frontend .
   
   # Run container
   docker run -p 3000:80 lms-frontend
   ```

### Environment Variables for Production

Ensure these environment variables are set in your production environment:

```env
VITE_AWS_REGION=us-east-1
VITE_BEDROCK_AGENT_ID=your-production-agent-id
VITE_BEDROCK_AGENT_ALIAS_ID=production
VITE_SUPABASE_URL=your-production-supabase-url
VITE_SUPABASE_ANON_KEY=your-production-supabase-key
VITE_API_BASE_URL=https://your-production-api-url
VITE_DEVELOPMENT_MODE=false
VITE_MOCK_DATA_ENABLED=false
```

## Architecture

### State Management
- **React Context**: Global state management for auth, notifications, and themes
- **Custom Hooks**: Encapsulated business logic and API interactions
- **Local State**: Component-level state with useState and useReducer

### API Integration
- **Bedrock Agent Service**: Direct integration with AWS Bedrock Agent Runtime
- **REST API**: Traditional REST endpoints for CRUD operations
- **WebSocket**: Real-time features for chat and notifications
- **Mock Services**: Development-time mock data and services

### Performance Optimization
- **Code Splitting**: Route-based code splitting with React.lazy
- **Lazy Loading**: Component-level lazy loading for better performance
- **Caching**: Service worker caching for offline functionality
- **Bundle Optimization**: Vite's built-in optimization and tree shaking

## Troubleshooting

### Common Issues

1. **Build Errors**:
   ```bash
   # Clear node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Environment Variables Not Loading**:
   - Ensure variables start with `VITE_`
   - Check `.env.local` file exists and is properly formatted
   - Restart the development server after changes

3. **AWS Integration Issues**:
   - Verify AWS credentials and permissions
   - Check Bedrock Agent ID and alias configuration
   - Ensure CORS is properly configured on API Gateway

4. **Authentication Problems**:
   - Verify Supabase project configuration
   - Check authentication redirect URLs
   - Ensure proper JWT token handling

### Development Tips

- Use the browser's developer tools for debugging
- Check the Network tab for API call issues
- Use React Developer Tools for component debugging
- Enable verbose logging in development mode

## Contributing

1. **Code Style**: Follow the existing TypeScript and React patterns
2. **Testing**: Add tests for new features and bug fixes
3. **Documentation**: Update documentation for significant changes
4. **Performance**: Consider performance implications of new features

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the existing documentation in the `docs/` directory
- Create an issue in the project repository

## License

This project is part of the LMS AI Agent system and follows the same licensing terms as the main project.
