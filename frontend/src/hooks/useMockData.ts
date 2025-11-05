import { useState, useEffect } from 'react';
import { mockDataService } from '../services/mockDataService';
import { useAuth } from '../contexts/AuthContext';
import { useMockAuth } from '../contexts/MockAuthContext';

// Hook to get the appropriate auth context based on environment
export const useAuthContext = () => {
  const isDev = import.meta.env.VITE_USE_MOCK_AUTH === 'true';
  if (isDev) {
    return useMockAuth();
  } else {
    return useAuth();
  }
};

// Hook for student data
export const useStudentData = () => {
  const { user } = useAuthContext();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    classes: [],
    sessions: [],
    assignments: [],
    documents: [],
    analytics: null
  });

  useEffect(() => {
    if (user && user.role === 'student') {
      try {
        const classes = mockDataService.getStudentClasses(user.id);
        const allSessions = mockDataService.getSessions();
        const sessions = allSessions.filter(s => 
          classes.some(c => c.id === s.class_id)
        );
        const assignments = mockDataService.getAssignments();
        const documents = mockDataService.getDocuments(undefined, user.id);
        const analytics = mockDataService.getStudentAnalytics(user.id);

        setData({
          classes,
          sessions,
          assignments,
          documents,
          analytics
        });
      } catch (error) {
        console.error('Error loading student data:', error);
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, [user]);

  return { ...data, loading };
};

// Hook for teacher data
export const useTeacherData = () => {
  const { user } = useAuthContext();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    classes: [],
    sessions: [],
    students: [],
    assignments: [],
    documents: [],
    analytics: null
  });

  useEffect(() => {
    if (user && user.role === 'teacher') {
      try {
        const classes = mockDataService.getClasses(user.id);
        const allSessions = mockDataService.getSessions();
        const sessions = allSessions.filter(s => 
          classes.some(c => c.id === s.class_id)
        );
        const students = mockDataService.getStudents();
        const assignments = mockDataService.getAssignments();
        const documents = mockDataService.getDocuments();
        const analytics = mockDataService.getTeacherAnalytics(user.id);

        setData({
          classes,
          sessions,
          students,
          assignments,
          documents,
          analytics
        });
      } catch (error) {
        console.error('Error loading teacher data:', error);
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, [user]);

  return { ...data, loading };
};

// Hook for class-specific data
export const useClassData = (classId: string) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    class: null,
    sessions: [],
    students: [],
    assignments: [],
    documents: []
  });

  useEffect(() => {
    if (classId) {
      try {
        const classData = mockDataService.getClassById(classId);
        const sessions = mockDataService.getSessions(classId);
        const students = mockDataService.getStudents(classId);
        const assignments = mockDataService.getAssignments(classId);
        const documents = mockDataService.getDocuments(classId);

        setData({
          class: classData,
          sessions,
          students,
          assignments,
          documents
        });
      } catch (error) {
        console.error('Error loading class data:', error);
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, [classId]);

  return { ...data, loading };
};

// Hook for upcoming sessions
export const useUpcomingSessions = (limit: number = 5) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const upcomingSessions = mockDataService.getUpcomingSessions(limit);
      setSessions(upcomingSessions);
    } catch (error) {
      console.error('Error loading upcoming sessions:', error);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  return { sessions, loading };
};

// Hook for document management
export const useDocuments = (classId?: string, userId?: string) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const docs = mockDataService.getDocuments(classId, userId);
      setDocuments(docs);
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  }, [classId, userId]);

  const uploadDocument = async (file: File, classId?: string) => {
    // Mock upload - in real app, this would upload to S3
    const mockDoc = {
      id: `doc-${Date.now()}`,
      name: file.name,
      type: file.name.split('.').pop() as 'pdf' | 'docx' | 'pptx' | 'txt',
      size: file.size,
      uploaded_at: new Date().toISOString(),
      uploaded_by: userId || 'current-user',
      class_id: classId,
      url: URL.createObjectURL(file),
      processed: false
    };

    setDocuments(prev => [mockDoc, ...prev]);
    
    // Simulate processing
    setTimeout(() => {
      setDocuments(prev => 
        prev.map(doc => 
          doc.id === mockDoc.id 
            ? { ...doc, processed: true }
            : doc
        )
      );
    }, 2000);

    return mockDoc;
  };

  return { documents, loading, uploadDocument };
};