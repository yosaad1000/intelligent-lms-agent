# Frontend Component Architecture

This document outlines the component architecture and organization of the LMS AI Agent frontend application.

## Architecture Overview

The frontend follows a modular, component-based architecture with clear separation of concerns:

```
src/
├── components/          # Reusable UI components
├── pages/              # Route-level page components
├── contexts/           # React context providers
├── hooks/              # Custom React hooks
├── services/           # API and external service integrations
├── utils/              # Utility functions
└── types/              # TypeScript type definitions
```

## Component Organization

### Core UI Components (`src/components/ui/`)

**Purpose**: Generic, reusable UI components that can be used throughout the application.

- `AccessibilityProvider.tsx` - Accessibility context and utilities
- `ErrorBoundary.tsx` - Error boundary for component error handling
- `GlobalErrorBoundary.tsx` - Application-level error boundary
- `GlobalLoadingState.tsx` - Global loading indicator
- `LoadingSpinner.tsx` - Generic loading spinner component
- `ResponsiveWrapper.tsx` - Responsive layout wrapper
- `Toast.tsx` - Toast notification component
- `ConfirmationDialog.tsx` - Modal confirmation dialogs
- `EmptyState.tsx` - Empty state placeholder component

**Usage Pattern**:
```tsx
import { LoadingSpinner, Toast } from '@/components/ui'

function MyComponent() {
  return (
    <div>
      <LoadingSpinner size="lg" />
      <Toast message="Success!" type="success" />
    </div>
  )
}
```

### Layout Components (`src/components/Layout/`)

**Purpose**: Application layout and navigation components.

- `Layout.tsx` - Main application layout wrapper
- `Header.tsx` - Application header with navigation and user menu
- `Sidebar.tsx` - Collapsible sidebar navigation

**Features**:
- Responsive design with mobile-first approach
- Role-based navigation (student vs teacher views)
- Theme switching and accessibility controls
- Notification indicators

### Feature-Specific Components

#### AI Chat (`src/components/AIChat/`)
- `AIChatInterface.tsx` - Main chat interface
- `AIChatMessage.tsx` - Individual chat message component
- `AIChatToggle.tsx` - Chat toggle button
- `AIChatDemo.tsx` - Demo/testing interface

#### Assignment Management (`src/components/Assignment/`)
- `AssignmentCard.tsx` - Assignment display card
- `AssignmentList.tsx` - List of assignments
- `CreateAssignment.tsx` - Assignment creation form

#### Session Management (`src/components/Session/`)
- `SessionCard.tsx` - Session display card
- `SessionList.tsx` - List of sessions
- `CreateSession.tsx` - Session creation form
- `EditSession.tsx` - Session editing interface
- `SessionDetail.tsx` - Detailed session view

#### Notification System (`src/components/notifications/`)
- `NotificationBell.tsx` - Notification bell icon with count
- `NotificationDropdown.tsx` - Notification dropdown menu
- `NotificationItem.tsx` - Individual notification component
- `NotificationList.tsx` - List of notifications
- `NotificationPreferences.tsx` - User notification settings

#### Google Integration (`src/components/GoogleIntegration/`)
- `GoogleAuthButton.tsx` - Google OAuth authentication
- `GoogleCalendarWidget.tsx` - Calendar integration
- `GoogleDriveWidget.tsx` - Drive file integration
- `GoogleErrorHandler.tsx` - Error handling for Google services

## Page Components (`src/pages/`)

### Shared Pages (`src/pages/shared/`)
- `Help.tsx` - Help and documentation page
- `Settings.tsx` - User settings and preferences

### Student Pages (`src/pages/student/`)
- `StudentAnalytics.tsx` - Student learning analytics
- `StudentChat.tsx` - Student chat interface
- `StudentDocuments.tsx` - Document management for students
- `StudentInterview.tsx` - Interview practice interface
- `StudentQuizzes.tsx` - Quiz taking interface
- `StudentSchedule.tsx` - Student schedule view

### Teacher Pages (`src/pages/teacher/`)
- `TeacherAIConfig.tsx` - AI agent configuration
- `TeacherAnalytics.tsx` - Teacher analytics dashboard
- `TeacherAssessments.tsx` - Assessment management
- `TeacherClasses.tsx` - Class management
- `TeacherContent.tsx` - Content management
- `TeacherInterviews.tsx` - Interview management
- `TeacherProgress.tsx` - Student progress tracking

### Main Pages
- `Dashboard.tsx` - Role-based dashboard
- `StudentDashboard.tsx` - Student-specific dashboard
- `TeacherDashboard.tsx` - Teacher-specific dashboard
- `DocumentManager.tsx` - Document upload and management
- `QuizCenter.tsx` - Quiz creation and taking
- `LearningAnalytics.tsx` - Analytics and reporting
- `StudyChat.tsx` - AI-powered study chat
- `InterviewPractice.tsx` - Voice interview practice

## State Management

### React Contexts (`src/contexts/`)

- `AuthContext.tsx` - Authentication state and user management
- `NotificationContext.tsx` - Notification state management
- `ThemeContext.tsx` - Theme and appearance settings
- `ToastContext.tsx` - Toast notification management
- `ViewContext.tsx` - View state and navigation
- `MockAuthContext.tsx` - Development authentication mock

### Custom Hooks (`src/hooks/`)

- `useAIChat.ts` - AI chat functionality
- `useAssignments.ts` - Assignment management
- `useHybridMode.ts` - Hybrid mode state management
- `useMockData.ts` - Mock data for development
- `useNetworkStatus.ts` - Network connectivity monitoring
- `useSessions.ts` - Session management
- `useCamera.ts` - Camera access for face recognition
- `useGoogleAuth.ts` - Google authentication integration

## Service Layer (`src/services/`)

### Core Services
- `bedrockAgentService.ts` - AWS Bedrock Agent integration
- `directAgentService.ts` - Direct agent communication
- `apiBedrockAgentService.ts` - API Gateway Bedrock integration
- `hybridModeService.ts` - Hybrid mode management

### Feature Services
- `documentService.ts` - Document upload and processing
- `analyticsService.ts` - Learning analytics
- `voiceInterviewService.ts` - Voice interview functionality
- `websocketService.ts` - Real-time communication
- `notificationApiService.ts` - Notification management

### Integration Services
- `googleService.ts` - Google services integration
- `googleCalendarService.ts` - Google Calendar API
- `googleDriveService.ts` - Google Drive API
- `mockDataService.ts` - Mock data for development
- `mockAuthService.ts` - Mock authentication

### Utility Services
- `performanceMonitor.ts` - Performance monitoring
- `errorHandlingService.ts` - Error handling and reporting
- `configurationService.ts` - Configuration management
- `realtimeConnectionManager.ts` - WebSocket connection management

## Component Patterns

### 1. Container/Presentational Pattern

```tsx
// Container Component (handles logic)
function StudentDashboardContainer() {
  const { user } = useAuth()
  const { assignments } = useAssignments(user.id)
  const { analytics } = useAnalytics(user.id)

  return (
    <StudentDashboardPresentation
      user={user}
      assignments={assignments}
      analytics={analytics}
    />
  )
}

// Presentational Component (handles UI)
function StudentDashboardPresentation({ user, assignments, analytics }) {
  return (
    <div className="dashboard">
      <WelcomeSection user={user} />
      <AssignmentList assignments={assignments} />
      <AnalyticsOverview analytics={analytics} />
    </div>
  )
}
```

### 2. Compound Component Pattern

```tsx
// Notification system using compound components
function NotificationSystem() {
  return (
    <NotificationProvider>
      <NotificationBell />
      <NotificationDropdown>
        <NotificationList />
        <NotificationPreferences />
      </NotificationDropdown>
    </NotificationProvider>
  )
}
```

### 3. Render Props Pattern

```tsx
// Error boundary with render props
function ErrorBoundary({ children, fallback }) {
  return (
    <ErrorBoundaryComponent
      fallback={({ error, retry }) => 
        fallback ? fallback(error, retry) : <DefaultErrorUI error={error} retry={retry} />
      }
    >
      {children}
    </ErrorBoundaryComponent>
  )
}
```

## Styling Architecture

### Tailwind CSS Organization

- **Utility-first approach** with Tailwind CSS
- **Component-specific styles** in CSS modules when needed
- **Responsive design** with mobile-first breakpoints
- **Dark mode support** with CSS custom properties

### Style Patterns

```tsx
// Consistent spacing and sizing
const cardStyles = "p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"
const buttonStyles = "px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500"

// Responsive design
const responsiveGrid = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
```

## Testing Strategy

### Component Testing
- **Unit tests** for individual components
- **Integration tests** for component interactions
- **Accessibility tests** for WCAG compliance
- **Visual regression tests** for UI consistency

### Test Organization
```
src/test/
├── components/          # Component-specific tests
├── hooks/              # Custom hook tests
├── services/           # Service layer tests
├── integration/        # Integration tests
├── e2e/               # End-to-end tests
└── utils/             # Test utilities and helpers
```

## Performance Considerations

### Code Splitting
- **Route-based splitting** with React.lazy
- **Component-level splitting** for heavy components
- **Service worker caching** for offline functionality

### Optimization Techniques
- **Memoization** with React.memo and useMemo
- **Lazy loading** for images and heavy components
- **Bundle optimization** with Vite's built-in features
- **Tree shaking** to eliminate unused code

## Accessibility

### WCAG Compliance
- **Semantic HTML** structure
- **ARIA labels** and roles
- **Keyboard navigation** support
- **Screen reader** compatibility
- **Color contrast** compliance

### Accessibility Components
- `AccessibilityProvider` - Global accessibility context
- `ScreenReaderOnly` - Screen reader only content
- `FocusTrap` - Focus management for modals
- `SkipLink` - Skip navigation links

## Development Guidelines

### Component Creation Checklist
- [ ] Follow naming conventions (PascalCase for components)
- [ ] Include TypeScript interfaces for props
- [ ] Add JSDoc comments for complex components
- [ ] Implement error boundaries where appropriate
- [ ] Add accessibility attributes
- [ ] Include responsive design considerations
- [ ] Write unit tests
- [ ] Update documentation

### Code Quality
- **ESLint** configuration for React and TypeScript
- **Prettier** for consistent code formatting
- **Husky** pre-commit hooks for quality checks
- **TypeScript strict mode** for type safety

This architecture ensures maintainable, scalable, and accessible frontend code that follows React best practices and modern development standards.