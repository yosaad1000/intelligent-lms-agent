import React from 'react';
import { useMockAuth } from '../contexts/MockAuthContext';
import { useNavigate } from 'react-router-dom';
import { 
  AcademicCapIcon, 
  UserGroupIcon,
  ArrowRightIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';

const DevLogin: React.FC = () => {
  const { loginAsTeacher, loginAsStudent, getMockUsers } = useMockAuth();
  const navigate = useNavigate();
  const mockUsers = getMockUsers();

  const handleTeacherLogin = async () => {
    try {
      await loginAsTeacher();
      navigate('/dashboard');
    } catch (error) {
      console.error('Teacher login failed:', error);
    }
  };

  const handleStudentLogin = async () => {
    try {
      await loginAsStudent();
      navigate('/dashboard');
    } catch (error) {
      console.error('Student login failed:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="bg-blue-600 p-3 rounded-full">
              <BeakerIcon className="h-8 w-8 text-white" />
            </div>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Development Mode</h2>
          <p className="mt-2 text-sm text-gray-600">
            Quick login for testing the LMS platform
          </p>
        </div>

        {/* Login Options */}
        <div className="space-y-4">
          {/* Teacher Login */}
          <button
            onClick={handleTeacherLogin}
            className="w-full flex items-center justify-between p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border-2 border-transparent hover:border-blue-200"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-blue-100 p-3 rounded-full">
                <AcademicCapIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-900">Login as Teacher</h3>
                <p className="text-sm text-gray-500">Dr. Sarah Johnson</p>
                <p className="text-xs text-gray-400">teacher@demo.com</p>
              </div>
            </div>
            <ArrowRightIcon className="h-5 w-5 text-gray-400" />
          </button>

          {/* Student Login */}
          <button
            onClick={handleStudentLogin}
            className="w-full flex items-center justify-between p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border-2 border-transparent hover:border-green-200"
          >
            <div className="flex items-center space-x-4">
              <div className="bg-green-100 p-3 rounded-full">
                <UserGroupIcon className="h-6 w-6 text-green-600" />
              </div>
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-900">Login as Student</h3>
                <p className="text-sm text-gray-500">Alex Chen</p>
                <p className="text-xs text-gray-400">student@demo.com</p>
              </div>
            </div>
            <ArrowRightIcon className="h-5 w-5 text-gray-400" />
          </button>
        </div>

        {/* Available Mock Users */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Available Test Users</h4>
          <div className="space-y-2">
            {mockUsers.map((user) => (
              <div key={user.id} className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    user.role === 'teacher' ? 'bg-blue-400' : 'bg-green-400'
                  }`}></div>
                  <span className="text-gray-600">{user.name}</span>
                </div>
                <span className="text-gray-400">{user.role}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Features Available */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Available Features</h4>
          <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
            <div>✅ AI Study Chat</div>
            <div>✅ Document Manager</div>
            <div>✅ Quiz Generator</div>
            <div>✅ Learning Analytics</div>
            <div>✅ Voice Interview</div>
            <div>✅ Class Management</div>
            <div>✅ Student Progress</div>
            <div>✅ Mock Data</div>
          </div>
        </div>

        {/* Environment Info */}
        <div className="text-center text-xs text-gray-500">
          <p>Development Environment</p>
          <p>Mock Authentication & Bedrock Agent Integration</p>
        </div>
      </div>
    </div>
  );
};

export default DevLogin;