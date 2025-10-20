// Mock Authentication Service for Local Development
export interface MockUser {
  id: string;
  email: string;
  name: string;
  role: 'student' | 'teacher';
  avatar?: string;
  created_at: string;
}

export interface MockSession {
  access_token: string;
  user: MockUser;
  expires_at: number;
}

export class MockAuthService {
  private static instance: MockAuthService;
  private currentUser: MockUser | null = null;
  private currentSession: MockSession | null = null;

  // Mock users for testing
  private mockUsers: MockUser[] = [
    {
      id: 'teacher-1',
      email: 'teacher@demo.com',
      name: 'Dr. Sarah Johnson',
      role: 'teacher',
      avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150',
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 'student-1', 
      email: 'student@demo.com',
      name: 'Alex Chen',
      role: 'student',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 'student-2',
      email: 'student2@demo.com', 
      name: 'Maria Rodriguez',
      role: 'student',
      avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150',
      created_at: '2024-01-01T00:00:00Z'
    }
  ];

  private constructor() {
    // Load saved session from localStorage
    this.loadSession();
  }

  public static getInstance(): MockAuthService {
    if (!MockAuthService.instance) {
      MockAuthService.instance = new MockAuthService();
    }
    return MockAuthService.instance;
  }

  public async signIn(email: string, password: string): Promise<MockSession> {
    // Find user by email
    const user = this.mockUsers.find(u => u.email === email);
    
    if (!user) {
      throw new Error('User not found');
    }

    // Create mock session
    const session: MockSession = {
      access_token: `mock-token-${user.id}-${Date.now()}`,
      user: user,
      expires_at: Date.now() + (24 * 60 * 60 * 1000) // 24 hours
    };

    this.currentUser = user;
    this.currentSession = session;
    
    // Save to localStorage
    this.saveSession();
    
    return session;
  }

  public async signUp(email: string, password: string, name: string, role: 'student' | 'teacher'): Promise<MockSession> {
    // Check if user already exists
    if (this.mockUsers.find(u => u.email === email)) {
      throw new Error('User already exists');
    }

    // Create new user
    const newUser: MockUser = {
      id: `${role}-${Date.now()}`,
      email,
      name,
      role,
      created_at: new Date().toISOString()
    };

    this.mockUsers.push(newUser);

    // Create session
    const session: MockSession = {
      access_token: `mock-token-${newUser.id}-${Date.now()}`,
      user: newUser,
      expires_at: Date.now() + (24 * 60 * 60 * 1000)
    };

    this.currentUser = newUser;
    this.currentSession = session;
    
    this.saveSession();
    
    return session;
  }

  public async signOut(): Promise<void> {
    this.currentUser = null;
    this.currentSession = null;
    localStorage.removeItem('mock-auth-session');
  }

  public getCurrentUser(): MockUser | null {
    return this.currentUser;
  }

  public getCurrentSession(): MockSession | null {
    return this.currentSession;
  }

  public isAuthenticated(): boolean {
    return this.currentSession !== null && this.currentSession.expires_at > Date.now();
  }

  // Quick login methods for testing
  public async loginAsTeacher(): Promise<MockSession> {
    return this.signIn('teacher@demo.com', 'password');
  }

  public async loginAsStudent(): Promise<MockSession> {
    return this.signIn('student@demo.com', 'password');
  }

  public async switchRole(role: 'student' | 'teacher'): Promise<MockSession> {
    const targetUser = this.mockUsers.find(u => u.role === role);
    if (!targetUser) {
      throw new Error(`No ${role} user available`);
    }
    
    return this.signIn(targetUser.email, 'password');
  }

  private saveSession(): void {
    if (this.currentSession) {
      localStorage.setItem('mock-auth-session', JSON.stringify(this.currentSession));
    }
  }

  private loadSession(): void {
    try {
      const saved = localStorage.getItem('mock-auth-session');
      if (saved) {
        const session: MockSession = JSON.parse(saved);
        
        // Check if session is still valid
        if (session.expires_at > Date.now()) {
          this.currentSession = session;
          this.currentUser = session.user;
        } else {
          // Session expired, remove it
          localStorage.removeItem('mock-auth-session');
        }
      }
    } catch (error) {
      console.warn('Failed to load mock auth session:', error);
      localStorage.removeItem('mock-auth-session');
    }
  }

  // Get all available mock users (for testing UI)
  public getMockUsers(): MockUser[] {
    return [...this.mockUsers];
  }
}

export const mockAuthService = MockAuthService.getInstance();