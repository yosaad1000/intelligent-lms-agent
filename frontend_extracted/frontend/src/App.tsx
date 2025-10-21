import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { MockAuthProvider, useMockAuth } from './contexts/MockAuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { ToastProvider } from './contexts/ToastContext';
import { ViewProvider } from './contexts/ViewContext';
import Layout from './components/Layout/Layout';
import AppErrorBoundary from './components/AppErrorBoundary';
import GlobalErrorBoundary from './components/ui/GlobalErrorBoundary';
import OfflineDetector from './components/OfflineDetector';
import { AccessibilityProvider, SkipToMain } from './components/ui/AccessibilityProvider';

// Core pages that definitely exist
import DevLogin from './pages/DevLogin';
import StudentDashboard from './pages/StudentDashboard';
import TeacherDashboard from './pages/TeacherDashboard';
import StudyChat from './pages/StudyChat';
import DocumentManager from './pages/DocumentManager';
import QuizCenter from './pages/QuizCenter';
import LearningAnalytics from './pages/LearningAnalytics';
import InterviewPractice from './pages/InterviewPractice';
import Profile from './pages/Profile';

// Teacher pages
import TeacherClasses from './pages/teacher/TeacherClasses';
import TeacherContent from './pages/teacher/TeacherContent';
import TeacherAssessments from './pages/teacher/TeacherAssessments';
import TeacherProgress from './pages/teacher/TeacherProgress';
import TeacherInterviews from './pages/teacher/TeacherInterviews';
import TeacherAnalytics from './pages/teacher/TeacherAnalytics';
import TeacherAIConfig from './pages/teacher/TeacherAIConfig';

import './App.css';

// Conditional hook usage based on environment
const useAuthHook = () => {
  const isDev = import.meta.env.VITE_USE_MOCK_AUTH === 'true';
  if (isDev) {
    return useMockAuth();
  } else {
    return useAuth();
  }
};

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuthHook();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-3 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

const DashboardRoute: React.FC = () => {
  const { user, loading, currentRole } = useAuthHook();
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-3 text-gray-600">Loading user profile...</p>
        </div>
      </div>
    );
  }
  
  // Route based on current role
  if (currentRole === 'teacher') {
    return <TeacherDashboard />;
  } else {
    return <StudentDashboard />;
  }
};

const AppRoutes: React.FC = () => {
  const { isAuthenticated } = useAuthHook();
  const isDev = import.meta.env.VITE_USE_MOCK_AUTH === 'true';

  return (
    <Routes>
      <Route 
        path="/" 
        element={isAuthenticated ? <Navigate to="/dashboard" /> : <DevLogin />} 
      />
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" /> : <DevLogin />} 
      />
      <Route 
        path="/dev-login" 
        element={<DevLogin />} 
      />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<DashboardRoute />} />
        
        {/* Core LMS Features */}
        <Route path="chat" element={<StudyChat />} />
        <Route path="documents" element={<DocumentManager />} />
        <Route path="quizzes" element={<QuizCenter />} />
        <Route path="analytics" element={<LearningAnalytics />} />
        <Route path="interview" element={<InterviewPractice />} />
        
        {/* User Settings */}
        <Route path="profile" element={<Profile />} />
        
        {/* Teacher Routes */}
        <Route path="teacher/classes" element={<TeacherClasses />} />
        <Route path="teacher/content" element={<TeacherContent />} />
        <Route path="teacher/assessments" element={<TeacherAssessments />} />
        <Route path="teacher/progress" element={<TeacherProgress />} />
        <Route path="teacher/interviews" element={<TeacherInterviews />} />
        <Route path="teacher/analytics" element={<TeacherAnalytics />} />
        <Route path="teacher/ai-config" element={<TeacherAIConfig />} />
        
        <Route path="" element={<Navigate to="/dashboard" />} />
      </Route>
    </Routes>
  );
};

function App() {
  const isDev = import.meta.env.VITE_USE_MOCK_AUTH === 'true';
  const AuthProviderComponent = isDev ? MockAuthProvider : AuthProvider;
  
  return (
    <GlobalErrorBoundary>
      <AccessibilityProvider>
        <ThemeProvider>
          <AuthProviderComponent>
            <NotificationProvider>
              <ToastProvider>
                <ViewProvider>
                  <Router>
                    <SkipToMain />
                    <OfflineDetector />
                    <AppRoutes />
                  </Router>
                </ViewProvider>
              </ToastProvider>
            </NotificationProvider>
          </AuthProviderComponent>
        </ThemeProvider>
      </AccessibilityProvider>
    </GlobalErrorBoundary>
  );
}

export default App;