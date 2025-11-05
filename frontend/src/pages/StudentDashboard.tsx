import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useMockAuth } from '../contexts/MockAuthContext';
import { mockDataService } from '../services/mockDataService';
import { 
  BookOpenIcon, 
  CalendarIcon,
  UserGroupIcon,
  ClockIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  ClipboardDocumentListIcon,
  MicrophoneIcon,
  ChartBarIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline';

// Hook to get the appropriate auth context
const useAuthContext = () => {
  const isDev = import.meta.env.VITE_USE_MOCK_AUTH === 'true';
  if (isDev) {
    return useMockAuth();
  } else {
    return useAuth();
  }
};

const StudentDashboard: React.FC = () => {
  const { user } = useAuthContext();
  const [classes, setClasses] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      try {
        // Load student data using mock service
        const studentClasses = mockDataService.getStudentClasses(user.id);
        const allSessions = mockDataService.getSessions();
        const studentSessions = allSessions.filter(s => 
          studentClasses.some(c => c.id === s.class_id)
        );
        const studentAnalytics = mockDataService.getStudentAnalytics(user.id);

        setClasses(studentClasses);
        setSessions(studentSessions);
        setAnalytics(studentAnalytics);
      } catch (error) {
        console.error('Error loading student data:', error);
      } finally {
        setLoading(false);
      }
    }
  }, [user]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-3 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const upcomingSessions = sessions
    .filter(s => new Date(s.date) > new Date() && s.status === 'scheduled')
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .slice(0, 3);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.name || 'Student'}!
          </h1>
          <p className="text-gray-600 mt-2">
            Ready to continue your learning journey?
          </p>
        </div>

        {/* Quick Stats */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <BookOpenIcon className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Enrolled Classes</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.enrolledClasses}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircleIcon className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Attendance Rate</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.attendanceRate}%</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <ClipboardDocumentListIcon className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Assignments</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.completedAssignments}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <AcademicCapIcon className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Average Grade</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.averageGrade}%</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* AI Learning Tools */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">AI Learning Assistant</h2>
                <p className="text-gray-600 mt-1">Enhance your learning with AI-powered tools</p>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Link
                    to="/chat"
                    className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all"
                  >
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <ChatBubbleLeftRightIcon className="h-6 w-6 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <h3 className="font-medium text-gray-900">Study Chat</h3>
                      <p className="text-sm text-gray-600">Ask questions about your materials</p>
                    </div>
                  </Link>

                  <Link
                    to="/quizzes"
                    className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:shadow-md transition-all"
                  >
                    <div className="p-2 bg-green-100 rounded-lg">
                      <ClipboardDocumentListIcon className="h-6 w-6 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <h3 className="font-medium text-gray-900">Quiz Generator</h3>
                      <p className="text-sm text-gray-600">Create practice quizzes</p>
                    </div>
                  </Link>

                  <Link
                    to="/interview"
                    className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-purple-300 hover:shadow-md transition-all"
                  >
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <MicrophoneIcon className="h-6 w-6 text-purple-600" />
                    </div>
                    <div className="ml-4">
                      <h3 className="font-medium text-gray-900">Interview Practice</h3>
                      <p className="text-sm text-gray-600">Practice with AI interviewer</p>
                    </div>
                  </Link>

                  <Link
                    to="/analytics"
                    className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-orange-300 hover:shadow-md transition-all"
                  >
                    <div className="p-2 bg-orange-100 rounded-lg">
                      <ChartBarIcon className="h-6 w-6 text-orange-600" />
                    </div>
                    <div className="ml-4">
                      <h3 className="font-medium text-gray-900">Learning Analytics</h3>
                      <p className="text-sm text-gray-600">Track your progress</p>
                    </div>
                  </Link>
                </div>
              </div>
            </div>

            {/* Enrolled Classes */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">My Classes</h2>
              </div>
              <div className="p-6">
                {classes.length === 0 ? (
                  <div className="text-center py-8">
                    <BookOpenIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No classes yet</h3>
                    <p className="mt-1 text-sm text-gray-500">Join a class to get started</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {classes.map((cls) => (
                      <div key={cls.id} className="border border-gray-200 rounded-lg p-4">
                        <div className={`w-full h-2 ${cls.color} rounded-full mb-3`}></div>
                        <h3 className="font-medium text-gray-900">{cls.name}</h3>
                        <p className="text-sm text-gray-600 mt-1">{cls.description}</p>
                        <div className="flex items-center justify-between mt-3">
                          <span className="text-sm text-gray-500">{cls.teacher_name}</span>
                          <span className="text-sm text-gray-500">{cls.student_count} students</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Upcoming Sessions */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Upcoming Sessions</h3>
              </div>
              <div className="p-6">
                {upcomingSessions.length === 0 ? (
                  <div className="text-center py-4">
                    <CalendarIcon className="mx-auto h-8 w-8 text-gray-400" />
                    <p className="mt-2 text-sm text-gray-500">No upcoming sessions</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {upcomingSessions.map((session) => (
                      <div key={session.id} className="flex items-center p-3 bg-gray-50 rounded-lg">
                        <div className="p-2 bg-blue-100 rounded-lg">
                          <ClockIcon className="h-4 w-4 text-blue-600" />
                        </div>
                        <div className="ml-3 flex-1">
                          <p className="text-sm font-medium text-gray-900">{session.title}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(session.date).toLocaleDateString()} at{' '}
                            {new Date(session.date).toLocaleTimeString([], { 
                              hour: '2-digit', 
                              minute: '2-digit' 
                            })}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
              </div>
              <div className="p-6 space-y-3">
                <Link
                  to="/documents"
                  className="flex items-center p-3 text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <DocumentTextIcon className="h-5 w-5 text-gray-400" />
                  <span className="ml-3">Upload Documents</span>
                </Link>
                <Link
                  to="/profile"
                  className="flex items-center p-3 text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <UserGroupIcon className="h-5 w-5 text-gray-400" />
                  <span className="ml-3">View Profile</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;