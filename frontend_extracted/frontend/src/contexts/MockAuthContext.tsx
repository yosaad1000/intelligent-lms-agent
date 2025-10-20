import React, { createContext, useContext, useState, useEffect } from 'react';
import { mockAuthService, MockUser, MockSession } from '../services/mockAuthService';

interface MockAuthContextType {
  user: MockUser | null;
  session: MockSession | null;
  isAuthenticated: boolean;
  loading: boolean;
  userRoles: string[];
  currentRole: string;
  signUp: (email: string, password: string, name: string, userType: 'teacher' | 'student') => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signInWithGoogle: (userType: 'teacher' | 'student') => Promise<void>;
  signOut: () => Promise<void>;
  switchRole: (role: 'teacher' | 'student') => Promise<void>;
  addRole: (role: 'teacher' | 'student') => Promise<void>;
  isTeacher: boolean;
  isStudent: boolean;
  // Mock-specific methods for testing
  loginAsTeacher: () => Promise<void>;
  loginAsStudent: () => Promise<void>;
  getMockUsers: () => MockUser[];
}

const MockAuthContext = createContext<MockAuthContextType | undefined>(undefined);

export const MockAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<MockUser | null>(null);
  const [session, setSession] = useState<MockSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [userRoles, setUserRoles] = useState<string[]>(['student']);
  const [currentRole, setCurrentRole] = useState<string>('student');

  useEffect(() => {
    // Initialize mock auth
    const initAuth = async () => {
      try {
        const currentSession = mockAuthService.getCurrentSession();
        const currentUser = mockAuthService.getCurrentUser();

        if (currentSession && currentUser) {
          setSession(currentSession);
          setUser(currentUser);
          setCurrentRole(currentUser.role);
          setUserRoles([currentUser.role]);
        }
      } catch (error) {
        console.error('Mock auth initialization error:', error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const signUp = async (email: string, password: string, name: string, userType: 'teacher' | 'student') => {
    try {
      const session = await mockAuthService.signUp(email, password, name, userType);
      setSession(session);
      setUser(session.user);
      setCurrentRole(session.user.role);
      setUserRoles([session.user.role]);
    } catch (error) {
      console.error('Mock sign up error:', error);
      throw error;
    }
  };

  const signIn = async (email: string, password: string) => {
    try {
      const session = await mockAuthService.signIn(email, password);
      setSession(session);
      setUser(session.user);
      setCurrentRole(session.user.role);
      setUserRoles([session.user.role]);
    } catch (error) {
      console.error('Mock sign in error:', error);
      throw error;
    }
  };

  const signInWithGoogle = async (userType: 'teacher' | 'student') => {
    // For mock, just sign in as the appropriate user type
    try {
      const session = await mockAuthService.switchRole(userType);
      setSession(session);
      setUser(session.user);
      setCurrentRole(session.user.role);
      setUserRoles([session.user.role]);
    } catch (error) {
      console.error('Mock Google sign in error:', error);
      throw error;
    }
  };

  const switchRole = async (role: 'teacher' | 'student') => {
    try {
      const session = await mockAuthService.switchRole(role);
      setSession(session);
      setUser(session.user);
      setCurrentRole(session.user.role);
      setUserRoles([session.user.role]);
    } catch (error) {
      console.error('Mock role switch error:', error);
      throw error;
    }
  };

  const addRole = async (role: 'teacher' | 'student') => {
    // For mock, just switch to the role
    await switchRole(role);
  };

  const signOut = async () => {
    await mockAuthService.signOut();
    setUser(null);
    setSession(null);
    setUserRoles(['student']);
    setCurrentRole('student');
  };

  // Mock-specific convenience methods
  const loginAsTeacher = async () => {
    try {
      const session = await mockAuthService.loginAsTeacher();
      setSession(session);
      setUser(session.user);
      setCurrentRole(session.user.role);
      setUserRoles([session.user.role]);
    } catch (error) {
      console.error('Mock teacher login error:', error);
      throw error;
    }
  };

  const loginAsStudent = async () => {
    try {
      const session = await mockAuthService.loginAsStudent();
      setSession(session);
      setUser(session.user);
      setCurrentRole(session.user.role);
      setUserRoles([session.user.role]);
    } catch (error) {
      console.error('Mock student login error:', error);
      throw error;
    }
  };

  const getMockUsers = () => {
    return mockAuthService.getMockUsers();
  };

  return (
    <MockAuthContext.Provider
      value={{
        user,
        session,
        isAuthenticated: mockAuthService.isAuthenticated(),
        loading,
        userRoles,
        currentRole,
        signUp,
        signIn,
        signInWithGoogle,
        signOut,
        switchRole,
        addRole,
        isTeacher: currentRole === 'teacher',
        isStudent: currentRole === 'student',
        loginAsTeacher,
        loginAsStudent,
        getMockUsers,
      }}
    >
      {children}
    </MockAuthContext.Provider>
  );
};

export const useMockAuth = () => {
  const context = useContext(MockAuthContext);
  if (context === undefined) {
    throw new Error('useMockAuth must be used within a MockAuthProvider');
  }
  return context;
};