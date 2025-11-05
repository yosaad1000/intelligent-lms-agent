// Mock Data Service for Local Development
export interface MockClass {
  id: string;
  name: string;
  description: string;
  subject: string;
  teacher_id: string;
  teacher_name: string;
  invite_code: string;
  created_at: string;
  student_count: number;
  session_count: number;
  color: string;
}

export interface MockSession {
  id: string;
  class_id: string;
  title: string;
  description: string;
  date: string;
  duration: number; // minutes
  attendance_count: number;
  total_students: number;
  status: 'scheduled' | 'in-progress' | 'completed' | 'cancelled';
  materials?: string[];
}

export interface MockStudent {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  enrolled_classes: string[];
  attendance_rate: number;
  last_active: string;
}

export interface MockAssignment {
  id: string;
  class_id: string;
  title: string;
  description: string;
  due_date: string;
  type: 'quiz' | 'essay' | 'project' | 'reading';
  status: 'draft' | 'published' | 'closed';
  submissions: number;
  total_students: number;
}

export interface MockDocument {
  id: string;
  name: string;
  type: 'pdf' | 'docx' | 'pptx' | 'txt';
  size: number;
  uploaded_at: string;
  uploaded_by: string;
  class_id?: string;
  url: string;
  processed: boolean;
}

export class MockDataService {
  private static instance: MockDataService;

  // Mock Classes
  private mockClasses: MockClass[] = [
    {
      id: 'class-1',
      name: 'Introduction to Machine Learning',
      description: 'Fundamentals of ML algorithms and applications',
      subject: 'Computer Science',
      teacher_id: 'teacher-1',
      teacher_name: 'Dr. Sarah Johnson',
      invite_code: 'ML2024A',
      created_at: '2024-01-15T09:00:00Z',
      student_count: 28,
      session_count: 12,
      color: 'bg-blue-500'
    },
    {
      id: 'class-2', 
      name: 'Data Structures & Algorithms',
      description: 'Core programming concepts and problem-solving techniques',
      subject: 'Computer Science',
      teacher_id: 'teacher-1',
      teacher_name: 'Dr. Sarah Johnson',
      invite_code: 'DSA2024B',
      created_at: '2024-01-10T10:30:00Z',
      student_count: 35,
      session_count: 15,
      color: 'bg-green-500'
    },
    {
      id: 'class-3',
      name: 'Web Development Fundamentals',
      description: 'HTML, CSS, JavaScript, and modern web frameworks',
      subject: 'Computer Science',
      teacher_id: 'teacher-1',
      teacher_name: 'Dr. Sarah Johnson',
      invite_code: 'WEB2024C',
      created_at: '2024-01-08T14:00:00Z',
      student_count: 42,
      session_count: 18,
      color: 'bg-purple-500'
    }
  ];

  // Mock Sessions
  private mockSessions: MockSession[] = [
    {
      id: 'session-1',
      class_id: 'class-1',
      title: 'Introduction to Neural Networks',
      description: 'Understanding the basics of artificial neural networks',
      date: '2024-01-20T10:00:00Z',
      duration: 90,
      attendance_count: 26,
      total_students: 28,
      status: 'completed',
      materials: ['Neural Networks Slides.pdf', 'Practice Problems.docx']
    },
    {
      id: 'session-2',
      class_id: 'class-1', 
      title: 'Supervised Learning Algorithms',
      description: 'Linear regression, decision trees, and SVM',
      date: '2024-01-22T10:00:00Z',
      duration: 90,
      attendance_count: 24,
      total_students: 28,
      status: 'completed',
      materials: ['Supervised Learning.pdf', 'Code Examples.zip']
    },
    {
      id: 'session-3',
      class_id: 'class-1',
      title: 'Deep Learning Workshop',
      description: 'Hands-on experience with TensorFlow and PyTorch',
      date: '2024-01-25T10:00:00Z',
      duration: 120,
      attendance_count: 0,
      total_students: 28,
      status: 'scheduled',
      materials: ['Deep Learning Lab.pdf']
    },
    {
      id: 'session-4',
      class_id: 'class-2',
      title: 'Binary Trees and Traversals',
      description: 'Tree data structures and traversal algorithms',
      date: '2024-01-21T14:00:00Z',
      duration: 75,
      attendance_count: 32,
      total_students: 35,
      status: 'completed'
    },
    {
      id: 'session-5',
      class_id: 'class-2',
      title: 'Graph Algorithms',
      description: 'BFS, DFS, and shortest path algorithms',
      date: '2024-01-24T14:00:00Z',
      duration: 75,
      attendance_count: 0,
      total_students: 35,
      status: 'in-progress'
    }
  ];

  // Mock Students
  private mockStudents: MockStudent[] = [
    {
      id: 'student-1',
      name: 'Alex Chen',
      email: 'student@demo.com',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
      enrolled_classes: ['class-1', 'class-2'],
      attendance_rate: 92,
      last_active: '2024-01-20T15:30:00Z'
    },
    {
      id: 'student-2',
      name: 'Maria Rodriguez',
      email: 'student2@demo.com',
      avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150',
      enrolled_classes: ['class-1', 'class-3'],
      attendance_rate: 88,
      last_active: '2024-01-19T11:45:00Z'
    },
    {
      id: 'student-3',
      name: 'James Wilson',
      email: 'james.wilson@demo.com',
      avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
      enrolled_classes: ['class-2', 'class-3'],
      attendance_rate: 95,
      last_active: '2024-01-20T09:15:00Z'
    }
  ];

  // Mock Assignments
  private mockAssignments: MockAssignment[] = [
    {
      id: 'assignment-1',
      class_id: 'class-1',
      title: 'ML Algorithm Implementation',
      description: 'Implement a linear regression algorithm from scratch',
      due_date: '2024-01-28T23:59:00Z',
      type: 'project',
      status: 'published',
      submissions: 18,
      total_students: 28
    },
    {
      id: 'assignment-2',
      class_id: 'class-1',
      title: 'Neural Networks Quiz',
      description: 'Test your understanding of neural network concepts',
      due_date: '2024-01-26T23:59:00Z',
      type: 'quiz',
      status: 'published',
      submissions: 22,
      total_students: 28
    },
    {
      id: 'assignment-3',
      class_id: 'class-2',
      title: 'Tree Traversal Coding Challenge',
      description: 'Implement various tree traversal algorithms',
      due_date: '2024-01-30T23:59:00Z',
      type: 'project',
      status: 'draft',
      submissions: 0,
      total_students: 35
    }
  ];

  // Mock Documents
  private mockDocuments: MockDocument[] = [
    {
      id: 'doc-1',
      name: 'Machine Learning Fundamentals.pdf',
      type: 'pdf',
      size: 2048576, // 2MB
      uploaded_at: '2024-01-15T09:00:00Z',
      uploaded_by: 'teacher-1',
      class_id: 'class-1',
      url: '/mock-documents/ml-fundamentals.pdf',
      processed: true
    },
    {
      id: 'doc-2',
      name: 'Neural Networks Deep Dive.pdf',
      type: 'pdf',
      size: 3145728, // 3MB
      uploaded_at: '2024-01-18T14:30:00Z',
      uploaded_by: 'teacher-1',
      class_id: 'class-1',
      url: '/mock-documents/neural-networks.pdf',
      processed: true
    },
    {
      id: 'doc-3',
      name: 'Data Structures Reference.docx',
      type: 'docx',
      size: 1048576, // 1MB
      uploaded_at: '2024-01-12T11:15:00Z',
      uploaded_by: 'teacher-1',
      class_id: 'class-2',
      url: '/mock-documents/data-structures.docx',
      processed: true
    },
    {
      id: 'doc-4',
      name: 'Student Study Notes.pdf',
      type: 'pdf',
      size: 512000, // 500KB
      uploaded_at: '2024-01-19T16:45:00Z',
      uploaded_by: 'student-1',
      url: '/mock-documents/study-notes.pdf',
      processed: true
    }
  ];

  private constructor() {}

  public static getInstance(): MockDataService {
    if (!MockDataService.instance) {
      MockDataService.instance = new MockDataService();
    }
    return MockDataService.instance;
  }

  // Class methods
  public getClasses(teacherId?: string): MockClass[] {
    if (teacherId) {
      return this.mockClasses.filter(c => c.teacher_id === teacherId);
    }
    return [...this.mockClasses];
  }

  public getClassById(id: string): MockClass | null {
    return this.mockClasses.find(c => c.id === id) || null;
  }

  public getStudentClasses(studentId: string): MockClass[] {
    const student = this.mockStudents.find(s => s.id === studentId);
    if (!student) return [];
    
    return this.mockClasses.filter(c => student.enrolled_classes.includes(c.id));
  }

  // Session methods
  public getSessions(classId?: string): MockSession[] {
    if (classId) {
      return this.mockSessions.filter(s => s.class_id === classId);
    }
    return [...this.mockSessions];
  }

  public getSessionById(id: string): MockSession | null {
    return this.mockSessions.find(s => s.id === id) || null;
  }

  public getUpcomingSessions(limit: number = 5): MockSession[] {
    const now = new Date();
    return this.mockSessions
      .filter(s => new Date(s.date) > now && s.status === 'scheduled')
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .slice(0, limit);
  }

  // Student methods
  public getStudents(classId?: string): MockStudent[] {
    if (classId) {
      return this.mockStudents.filter(s => s.enrolled_classes.includes(classId));
    }
    return [...this.mockStudents];
  }

  public getStudentById(id: string): MockStudent | null {
    return this.mockStudents.find(s => s.id === id) || null;
  }

  // Assignment methods
  public getAssignments(classId?: string): MockAssignment[] {
    if (classId) {
      return this.mockAssignments.filter(a => a.class_id === classId);
    }
    return [...this.mockAssignments];
  }

  public getAssignmentById(id: string): MockAssignment | null {
    return this.mockAssignments.find(a => a.id === id) || null;
  }

  // Document methods
  public getDocuments(classId?: string, userId?: string): MockDocument[] {
    let docs = [...this.mockDocuments];
    
    if (classId) {
      docs = docs.filter(d => d.class_id === classId);
    }
    
    if (userId) {
      docs = docs.filter(d => d.uploaded_by === userId);
    }
    
    return docs;
  }

  public getDocumentById(id: string): MockDocument | null {
    return this.mockDocuments.find(d => d.id === id) || null;
  }

  // Analytics methods
  public getTeacherAnalytics(teacherId: string) {
    const teacherClasses = this.getClasses(teacherId);
    const totalStudents = teacherClasses.reduce((sum, c) => sum + c.student_count, 0);
    const totalSessions = teacherClasses.reduce((sum, c) => sum + c.session_count, 0);
    
    return {
      totalClasses: teacherClasses.length,
      totalStudents,
      totalSessions,
      averageAttendance: 89,
      activeStudents: Math.floor(totalStudents * 0.85),
      recentActivity: [
        { date: '2024-01-20', sessions: 3, attendance: 92 },
        { date: '2024-01-19', sessions: 2, attendance: 88 },
        { date: '2024-01-18', sessions: 4, attendance: 91 },
        { date: '2024-01-17', sessions: 1, attendance: 95 },
        { date: '2024-01-16', sessions: 2, attendance: 87 }
      ]
    };
  }

  public getStudentAnalytics(studentId: string) {
    const student = this.getStudentById(studentId);
    if (!student) return null;

    const enrolledClasses = this.getStudentClasses(studentId);
    
    return {
      enrolledClasses: enrolledClasses.length,
      attendanceRate: student.attendance_rate,
      completedAssignments: 12,
      pendingAssignments: 3,
      averageGrade: 87,
      studyStreak: 7,
      totalStudyTime: 45, // hours
      recentScores: [92, 88, 95, 87, 91, 89, 94],
      weeklyActivity: [
        { day: 'Mon', hours: 2.5 },
        { day: 'Tue', hours: 3.0 },
        { day: 'Wed', hours: 1.5 },
        { day: 'Thu', hours: 4.0 },
        { day: 'Fri', hours: 2.0 },
        { day: 'Sat', hours: 3.5 },
        { day: 'Sun', hours: 1.0 }
      ]
    };
  }

  // Utility methods
  public formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  public getRelativeTime(date: string): string {
    const now = new Date();
    const target = new Date(date);
    const diffMs = now.getTime() - target.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return target.toLocaleDateString();
  }
}

export const mockDataService = MockDataService.getInstance();