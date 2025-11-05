import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { NotificationPreferences } from '../components/notifications';
import { 
  CameraIcon, 
  UserIcon, 
  CogIcon,
  MoonIcon,
  SunIcon,
  ComputerDesktopIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  BellIcon,
  PaintBrushIcon,
  KeyIcon,
  DevicePhoneMobileIcon
} from '@heroicons/react/24/outline';

const Profile: React.FC = () => {
  const { user, currentRole } = useAuth();
  const { theme, setTheme, actualTheme } = useTheme();
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'security' | 'notifications'>('profile');
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    bio: '',
    timezone: 'UTC',
    language: 'en',
    phoneNumber: '',
    institution: ''
  });

  const handleFaceRegistration = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setMessage('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const { apiCall } = await import('../lib/api');
      const response = await apiCall('/api/auth/register-face', {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        setMessage('Face registered successfully!');
        // Refresh the page to update user data
        window.location.reload();
      } else {
        const errorData = await response.json();
        setMessage(errorData.detail || 'Failed to register face');
      }
    } catch (error: any) {
      setMessage(error.message || 'Failed to register face');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 safe-area-padding">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="container-responsive">
          <div className="py-6">
            <div className="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0">
              <div className="flex items-center">
                <div className="h-16 w-16 sm:h-20 sm:w-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <UserIcon className="h-8 w-8 sm:h-10 sm:w-10 text-white" />
                </div>
                <div className="ml-4 sm:ml-6">
                  <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">{user?.name}</h1>
                  <p className="text-gray-600 dark:text-gray-300">{user?.email}</p>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-2 ${
                    currentRole === 'teacher' 
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' 
                      : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                  }`}>
                    {currentRole === 'teacher' ? 'Teacher' : 'Student'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container-responsive py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Navigation Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-4">Settings</h3>
              <nav className="space-y-2">
                <button
                  onClick={() => setActiveTab('profile')}
                  className={`w-full flex items-center px-3 py-2 text-sm rounded-lg transition-colors ${
                    activeTab === 'profile'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <UserIcon className="h-4 w-4 mr-3" />
                  Profile
                </button>
                <button
                  onClick={() => setActiveTab('preferences')}
                  className={`w-full flex items-center px-3 py-2 text-sm rounded-lg transition-colors ${
                    activeTab === 'preferences'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <CogIcon className="h-4 w-4 mr-3" />
                  Preferences
                </button>
                <button
                  onClick={() => setActiveTab('notifications')}
                  className={`w-full flex items-center px-3 py-2 text-sm rounded-lg transition-colors ${
                    activeTab === 'notifications'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <BellIcon className="h-4 w-4 mr-3" />
                  Notifications
                </button>
                <button
                  onClick={() => setActiveTab('security')}
                  className={`w-full flex items-center px-3 py-2 text-sm rounded-lg transition-colors ${
                    activeTab === 'security'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <ShieldCheckIcon className="h-4 w-4 mr-3" />
                  Security
                </button>
              </nav>
            </div>
          </div>

          {/* Content Area */}
          <div className="lg:col-span-3">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              {activeTab === 'profile' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">Profile Information</h3>
                  
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Full Name
                        </label>
                        <input
                          type="text"
                          value={profileData.name}
                          onChange={(e) => setProfileData(prev => ({ ...prev, name: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Email Address
                        </label>
                        <input
                          type="email"
                          value={profileData.email}
                          onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Bio
                      </label>
                      <textarea
                        value={profileData.bio}
                        onChange={(e) => setProfileData(prev => ({ ...prev, bio: e.target.value }))}
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Tell us about yourself..."
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Phone Number
                        </label>
                        <input
                          type="tel"
                          value={profileData.phoneNumber}
                          onChange={(e) => setProfileData(prev => ({ ...prev, phoneNumber: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Institution
                        </label>
                        <input
                          type="text"
                          value={profileData.institution}
                          onChange={(e) => setProfileData(prev => ({ ...prev, institution: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                        Save Changes
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'preferences' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">Preferences</h3>
                  
                  <div className="space-y-6">
                    {/* Theme Selection */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        <PaintBrushIcon className="h-4 w-4 inline mr-2" />
                        Theme
                      </label>
                      <div className="grid grid-cols-3 gap-3">
                        <button
                          onClick={() => setTheme('light')}
                          className={`flex flex-col items-center p-4 border-2 rounded-lg transition-colors ${
                            theme === 'light'
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                              : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                          }`}
                        >
                          <SunIcon className="h-6 w-6 text-yellow-500 mb-2" />
                          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Light</span>
                        </button>
                        <button
                          onClick={() => setTheme('dark')}
                          className={`flex flex-col items-center p-4 border-2 rounded-lg transition-colors ${
                            theme === 'dark'
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                              : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                          }`}
                        >
                          <MoonIcon className="h-6 w-6 text-blue-500 mb-2" />
                          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Dark</span>
                        </button>
                        <button
                          onClick={() => setTheme('system')}
                          className={`flex flex-col items-center p-4 border-2 rounded-lg transition-colors ${
                            theme === 'system'
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                              : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                          }`}
                        >
                          <ComputerDesktopIcon className="h-6 w-6 text-gray-500 mb-2" />
                          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">System</span>
                        </button>
                      </div>
                    </div>

                    {/* Language & Region */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          <GlobeAltIcon className="h-4 w-4 inline mr-2" />
                          Language
                        </label>
                        <select
                          value={profileData.language}
                          onChange={(e) => setProfileData(prev => ({ ...prev, language: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        >
                          <option value="en">English</option>
                          <option value="es">Spanish</option>
                          <option value="fr">French</option>
                          <option value="de">German</option>
                          <option value="zh">Chinese</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Timezone
                        </label>
                        <select
                          value={profileData.timezone}
                          onChange={(e) => setProfileData(prev => ({ ...prev, timezone: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        >
                          <option value="UTC">UTC</option>
                          <option value="America/New_York">Eastern Time</option>
                          <option value="America/Chicago">Central Time</option>
                          <option value="America/Denver">Mountain Time</option>
                          <option value="America/Los_Angeles">Pacific Time</option>
                          <option value="Europe/London">London</option>
                          <option value="Europe/Paris">Paris</option>
                          <option value="Asia/Tokyo">Tokyo</option>
                        </select>
                      </div>
                    </div>

                    {/* Accessibility Options */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        <DevicePhoneMobileIcon className="h-4 w-4 inline mr-2" />
                        Accessibility
                      </h4>
                      <div className="space-y-3">
                        <label className="flex items-center">
                          <input type="checkbox" className="rounded border-gray-300 dark:border-gray-600" />
                          <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                            High contrast mode
                          </span>
                        </label>
                        <label className="flex items-center">
                          <input type="checkbox" className="rounded border-gray-300 dark:border-gray-600" />
                          <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                            Reduce motion
                          </span>
                        </label>
                        <label className="flex items-center">
                          <input type="checkbox" className="rounded border-gray-300 dark:border-gray-600" />
                          <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                            Large text
                          </span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'notifications' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">Notification Settings</h3>
                  <NotificationPreferences showHeader={false} />
                </div>
              )}

              {activeTab === 'security' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">Security Settings</h3>
                  
                  <div className="space-y-6">
                    {/* Password Change */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        <KeyIcon className="h-4 w-4 inline mr-2" />
                        Change Password
                      </h4>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Current Password
                          </label>
                          <input
                            type="password"
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            New Password
                          </label>
                          <input
                            type="password"
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Confirm New Password
                          </label>
                          <input
                            type="password"
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                          />
                        </div>
                        <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                          Update Password
                        </button>
                      </div>
                    </div>

                    {/* Face Recognition for Students */}
                    {currentRole === 'student' && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                          <CameraIcon className="h-4 w-4 inline mr-2" />
                          Face Recognition
                        </h4>
                        
                        {message && (
                          <div className={`mb-4 p-4 rounded-md ${
                            message.includes('successfully') 
                              ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800' 
                              : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
                          }`}>
                            {message}
                          </div>
                        )}

                        <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
                          <div className="flex items-center">
                            <CameraIcon className="h-8 w-8 text-gray-400 dark:text-gray-500 mr-3" />
                            <div>
                              <div className="font-medium text-gray-900 dark:text-gray-100">
                                {user?.is_face_registered ? 'Face Registered' : 'Register Your Face'}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                {user?.is_face_registered 
                                  ? 'Your face is registered for attendance' 
                                  : 'Upload a clear photo of your face for attendance tracking'
                                }
                              </div>
                            </div>
                          </div>
                          
                          {!user?.is_face_registered && (
                            <div className="space-y-3">
                              <Link
                                to="/register-face"
                                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                              >
                                <CameraIcon className="h-4 w-4 mr-2" />
                                Register Face
                              </Link>
                              <div className="text-xs text-gray-500 dark:text-gray-400">
                                Or upload directly:
                              </div>
                              <div>
                                <input
                                  type="file"
                                  accept="image/*"
                                  onChange={handleFaceRegistration}
                                  className="hidden"
                                  id="face-upload"
                                  disabled={uploading}
                                />
                                <label
                                  htmlFor="face-upload"
                                  className={`cursor-pointer inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                                    uploading ? 'opacity-50 cursor-not-allowed' : ''
                                  }`}
                                >
                                  {uploading ? 'Uploading...' : 'Quick Upload'}
                                </label>
                              </div>
                            </div>
                          )}
                        </div>

                        {!user?.is_face_registered && (
                          <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                            <p className="font-medium mb-2">Tips for a good photo:</p>
                            <ul className="list-disc list-inside space-y-1">
                              <li>Face the camera directly</li>
                              <li>Ensure good lighting</li>
                              <li>Remove glasses if possible</li>
                              <li>Keep a neutral expression</li>
                              <li>Make sure your face is clearly visible</li>
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Two-Factor Authentication */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Two-Factor Authentication
                      </h4>
                      <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
                        <div>
                          <div className="font-medium text-gray-900 dark:text-gray-100">
                            2FA Status: <span className="text-red-600 dark:text-red-400">Disabled</span>
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            Add an extra layer of security to your account
                          </div>
                        </div>
                        <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                          Enable 2FA
                        </button>
                      </div>
                    </div>

                    {/* Active Sessions */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Active Sessions
                      </h4>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
                          <div>
                            <div className="font-medium text-gray-900 dark:text-gray-100">Current Session</div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">Chrome on Windows • Active now</div>
                          </div>
                          <span className="text-green-600 dark:text-green-400 text-sm">Current</span>
                        </div>
                        <div className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
                          <div>
                            <div className="font-medium text-gray-900 dark:text-gray-100">Mobile Session</div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">Safari on iPhone • 2 hours ago</div>
                          </div>
                          <button className="text-red-600 dark:text-red-400 text-sm hover:underline">
                            Revoke
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;