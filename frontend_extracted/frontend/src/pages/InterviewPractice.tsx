import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useMockAuth } from '../contexts/MockAuthContext';
import { 
  MicrophoneIcon,
  StopIcon,
  PlayIcon,
  DocumentTextIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  SpeakerWaveIcon,
  ChartBarIcon,
  ArrowPathIcon,
  PauseIcon,
  SignalIcon
} from '@heroicons/react/24/outline';
import { WebSocketService } from '../services/websocketService';
import type { WebSocketMessage } from '../services/websocketService';
import { bedrockAgentService } from '../services/bedrockAgentService';
import { directAgentService } from '../services/directAgentService';
import { useHybridMode, useAgentService } from '../hooks/useHybridMode';
import HybridModeIndicator from '../components/HybridModeIndicator';

interface InterviewSession {
  id: string;
  title: string;
  subject: string;
  duration: number;
  questionsAsked: number;
  score: number;
  completedAt: string;
  feedback: string[];
  analysis?: {
    overall_score: number;
    strengths: string[];
    areas_for_improvement: string[];
    recommendations: string[];
  };
}

interface Question {
  id: string;
  text: string;
  category: string;
  difficulty: 'easy' | 'medium' | 'hard';
  timeLimit: number; // in seconds
}

interface VoiceInterviewState {
  sessionId: string | null;
  status: 'idle' | 'starting' | 'active' | 'paused' | 'processing' | 'completed';
  currentQuestion: string | null;
  transcription: string;
  interimTranscription: string;
  audioLevel: number;
  connectionStatus: 'disconnected' | 'connecting' | 'connected';
  error: string | null;
}

interface AudioRecorderConfig {
  sampleRate: number;
  channels: number;
  bitsPerSample: number;
  bufferSize: number;
}

// Hook to get the appropriate auth context
const useAuthContext = () => {
  const isDev = import.meta.env.VITE_USE_MOCK_AUTH === 'true';
  if (isDev) {
    return useMockAuth();
  } else {
    return useAuth();
  }
};

// Hook to detect hybrid testing mode (keeping for backward compatibility)
const useHybridModeCompat = () => {
  return import.meta.env.VITE_USE_MOCK_AUTH === 'true' && 
         import.meta.env.VITE_USE_MOCK_AGENT === 'false';
};

const InterviewPractice: React.FC = () => {
  const { user } = useAuthContext();
  const { isHybridMode, isAgentConnected } = useHybridMode();
  const { agentService, agentServiceType } = useAgentService();
  
  // Voice interview state
  const [voiceState, setVoiceState] = useState<VoiceInterviewState>({
    sessionId: null,
    status: 'idle',
    currentQuestion: null,
    transcription: '',
    interimTranscription: '',
    audioLevel: 0,
    connectionStatus: 'disconnected',
    error: null
  });
  
  // UI state
  const [sessions, setSessions] = useState<InterviewSession[]>([]);
  const [selectedSubject, setSelectedSubject] = useState('general');
  const [selectedDifficulty, setSelectedDifficulty] = useState('intermediate');
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  
  // Audio recording refs
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioLevelRef = useRef<NodeJS.Timeout | null>(null);
  
  // WebSocket and services
  const wsServiceRef = useRef<WebSocketService | null>(null);
  
  // Audio configuration
  const audioConfig: AudioRecorderConfig = {
    sampleRate: 16000,
    channels: 1,
    bitsPerSample: 16,
    bufferSize: 4096
  };

  // Initialize WebSocket service
  useEffect(() => {
    const initializeServices = async () => {
      try {

        // Initialize WebSocket for voice processing
        const wsUrl = process.env.REACT_APP_WEBSOCKET_URL || 'wss://your-api-gateway.execute-api.us-east-1.amazonaws.com/dev';
        
        // Note: WebSocketService constructor is private, this would need to be fixed in the service
        // For now, we'll skip WebSocket initialization in direct agent mode
        if (agentServiceType !== 'direct') {
          wsServiceRef.current = new (WebSocketService as any)({
            url: wsUrl,
            userId: user?.id || 'anonymous'
          });
        }
        
        // Set up message handlers
        if (wsServiceRef.current) {
          wsServiceRef.current.onMessage('voice_interview_response', handleVoiceInterviewMessage);
          wsServiceRef.current.onMessage('transcription_update', handleTranscriptionUpdate);
          wsServiceRef.current.onMessage('interview_question', handleNewQuestion);
          wsServiceRef.current.onMessage('interview_complete', handleInterviewComplete);
          wsServiceRef.current.onMessage('error', handleWebSocketError);
        }
        
      } catch (error) {
        console.error('Failed to initialize services:', error);
        setVoiceState(prev => ({ ...prev, error: 'Failed to connect to services' }));
      }
    };
    
    initializeServices();
    
    return () => {
      if (wsServiceRef.current) {
        wsServiceRef.current.disconnect();
      }
      cleanupAudioResources();
    };
  }, [user, agentServiceType]);

  // Load previous sessions
  useEffect(() => {
    loadInterviewSessions();
  }, []);

  // Timer management
  useEffect(() => {
    if (voiceState.status === 'active' && timeRemaining > 0 && !isPaused) {
      timerRef.current = setTimeout(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            handleTimeUp();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [voiceState.status, timeRemaining, isPaused]);

  // WebSocket message handlers
  const handleVoiceInterviewMessage = useCallback((message: WebSocketMessage) => {
    console.log('Voice interview message:', message);
    
    if (message.content) {
      setVoiceState(prev => ({
        ...prev,
        transcription: prev.transcription + (message.content || '')
      }));
    }
  }, []);

  const handleTranscriptionUpdate = useCallback((message: WebSocketMessage) => {
    if (message.content) {
      setVoiceState(prev => ({
        ...prev,
        interimTranscription: message.content || ''
      }));
    }
  }, []);

  const handleNewQuestion = useCallback((message: WebSocketMessage) => {
    if (message.content) {
      setVoiceState(prev => ({
        ...prev,
        currentQuestion: message.content || null,
        transcription: '',
        interimTranscription: ''
      }));
      
      // Set timer for question (default 3 minutes)
      setTimeRemaining(180);
      setIsPaused(false);
      
      // Speak the question using text-to-speech
      speakText(message.content);
    }
  }, []);

  const handleInterviewComplete = useCallback((message: WebSocketMessage) => {
    setVoiceState(prev => ({
      ...prev,
      status: 'completed'
    }));
    
    stopRecording();
    
    // Process final analysis if provided
    if (message.content) {
      try {
        const analysis = JSON.parse(message.content);
        // Save session with analysis
        saveInterviewSession(analysis);
      } catch (error) {
        console.error('Failed to parse interview analysis:', error);
      }
    }
  }, []);

  const handleWebSocketError = useCallback((message: WebSocketMessage) => {
    setVoiceState(prev => ({
      ...prev,
      error: message.error || 'WebSocket error occurred'
    }));
  }, []);

  // Audio recording functions
  const initializeAudioRecording = async (): Promise<boolean> => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: audioConfig.sampleRate,
          channelCount: audioConfig.channels,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      mediaStreamRef.current = stream;

      // Set up audio context for level monitoring
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      analyserRef.current.fftSize = 256;
      
      // Set up MediaRecorder
      const options = {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 16000
      };
      
      mediaRecorderRef.current = new MediaRecorder(stream, options);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          
          // Send audio chunk for real-time transcription
          sendAudioChunk(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        // Process final audio
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        processFinalAudio(audioBlob);
      };

      return true;
    } catch (error) {
      console.error('Failed to initialize audio recording:', error);
      setVoiceState(prev => ({
        ...prev,
        error: 'Failed to access microphone. Please check permissions.'
      }));
      return false;
    }
  };

  const startAudioLevelMonitoring = () => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    
    const updateAudioLevel = () => {
      if (analyserRef.current && voiceState.status === 'active') {
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        
        setVoiceState(prev => ({
          ...prev,
          audioLevel: average
        }));
        
        audioLevelRef.current = setTimeout(updateAudioLevel, 100);
      }
    };
    
    updateAudioLevel();
  };

  const sendAudioChunk = async (audioBlob: Blob) => {
    try {
      // Convert audio blob to base64
      const arrayBuffer = await audioBlob.arrayBuffer();
      const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
      
      // Send via WebSocket for real-time processing
      if (wsServiceRef.current && wsServiceRef.current.isWebSocketConnected()) {
        wsServiceRef.current.sendMessage(JSON.stringify({
          action: 'process_audio',
          session_id: voiceState.sessionId,
          audio_data: base64Audio,
          is_final: false
        }), voiceState.sessionId || 'default');
      }
    } catch (error) {
      console.error('Failed to send audio chunk:', error);
    }
  };

  const processFinalAudio = async (audioBlob: Blob) => {
    try {
      const arrayBuffer = await audioBlob.arrayBuffer();
      const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));
      
      // Send final audio for processing
      if (wsServiceRef.current && wsServiceRef.current.isWebSocketConnected()) {
        wsServiceRef.current.sendMessage(JSON.stringify({
          action: 'process_audio',
          session_id: voiceState.sessionId,
          audio_data: base64Audio,
          is_final: true
        }), voiceState.sessionId || 'default');
      }
    } catch (error) {
      console.error('Failed to process final audio:', error);
    }
  };

  const cleanupAudioResources = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
      mediaStreamRef.current = null;
    }
    
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    if (audioLevelRef.current) {
      clearTimeout(audioLevelRef.current);
      audioLevelRef.current = null;
    }
    
    analyserRef.current = null;
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
  };

  // Text-to-speech function
  const speakText = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 0.8;
      
      // Use a professional voice if available
      const voices = speechSynthesis.getVoices();
      const preferredVoice = voices.find(voice => 
        voice.name.includes('Google') || voice.name.includes('Microsoft')
      );
      
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
      
      speechSynthesis.speak(utterance);
    }
  };

  // Main interview control functions
  const startInterview = async () => {
    try {
      setVoiceState(prev => ({ ...prev, status: 'starting', error: null }));
      
      // Connect to WebSocket if not connected
      if (wsServiceRef.current && !wsServiceRef.current.isWebSocketConnected()) {
        setVoiceState(prev => ({ ...prev, connectionStatus: 'connecting' }));
        const connected = await wsServiceRef.current.connect();
        
        if (!connected) {
          throw new Error('Failed to connect to voice service');
        }
        
        setVoiceState(prev => ({ ...prev, connectionStatus: 'connected' }));
      }
      
      // Initialize audio recording
      const audioInitialized = await initializeAudioRecording();
      if (!audioInitialized) {
        throw new Error('Failed to initialize audio recording');
      }
      
      // Start interview session via appropriate agent service
      let response: any;
      let sessionId: string;

      if (agentServiceType === 'direct' && isAgentConnected) {
        // Use DirectAgentService for hybrid mode
        console.log('🔄 Starting interview using DirectAgentService...');
        
        const interviewSession = await directAgentService.startInterview(
          `${selectedSubject} interview at ${selectedDifficulty} level`
        );
        
        sessionId = interviewSession.sessionId;
        const firstQuestion = interviewSession.questions[0]?.question || 'Let\'s begin the interview. Please introduce yourself.';
        
        setVoiceState(prev => ({
          ...prev,
          sessionId,
          status: 'active',
          currentQuestion: firstQuestion,
          transcription: '',
          interimTranscription: ''
        }));
        
        // Set initial timer (3 minutes per question)
        setTimeRemaining(180);
        setIsPaused(false);
        
        // Speak the first question
        speakText(firstQuestion);
        
        // Start audio level monitoring
        startAudioLevelMonitoring();
      } else if (agentServiceType === 'api') {
        // Use existing Bedrock Agent service for normal mode
        response = await bedrockAgentService.sendMessage(
          `Start a voice interview about ${selectedSubject} for ${selectedDifficulty} level. 
           This is a practice interview session. Please provide the first question.`,
          `interview-${Date.now()}`
        );
        
        if (response && (response as any).success && (response as any).response) {
          sessionId = `interview-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
          
          setVoiceState(prev => ({
            ...prev,
            sessionId,
            status: 'active',
            currentQuestion: (response as any).response,
            transcription: '',
            interimTranscription: ''
          }));
          
          // Set initial timer (3 minutes per question)
          setTimeRemaining(180);
          setIsPaused(false);
          
          // Speak the first question
          speakText((response as any).response);
          
          // Start audio level monitoring
          startAudioLevelMonitoring();
          
        } else {
          throw new Error('Failed to start interview session');
        }
      } else {
        // Mock mode
        console.log('🔄 Starting mock interview...');
        
        sessionId = `mock-interview-${Date.now()}`;
        const mockQuestion = `This is a mock ${selectedSubject} interview question at ${selectedDifficulty} level. Please tell me about your experience with this topic.`;
        
        setVoiceState(prev => ({
          ...prev,
          sessionId,
          status: 'active',
          currentQuestion: mockQuestion,
          transcription: '',
          interimTranscription: ''
        }));
        
        // Set initial timer (3 minutes per question)
        setTimeRemaining(180);
        setIsPaused(false);
        
        // Speak the mock question
        speakText(mockQuestion);
        
        // Start audio level monitoring
        startAudioLevelMonitoring();
      }
      
    } catch (error) {
      console.error('Failed to start interview:', error);
      setVoiceState(prev => ({
        ...prev,
        status: 'idle',
        error: error instanceof Error ? error.message : 'Failed to start interview'
      }));
    }
  };

  const startRecording = async () => {
    if (voiceState.status !== 'active' || !mediaRecorderRef.current) {
      return;
    }
    
    try {
      // Clear previous transcription
      setVoiceState(prev => ({
        ...prev,
        transcription: '',
        interimTranscription: ''
      }));
      
      // Start recording with time slicing for real-time processing
      mediaRecorderRef.current.start(1000); // 1 second chunks
      
      setVoiceState(prev => ({ ...prev, status: 'active' }));
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      setVoiceState(prev => ({
        ...prev,
        error: 'Failed to start recording'
      }));
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    
    setVoiceState(prev => ({
      ...prev,
      status: 'processing',
      audioLevel: 0
    }));
    
    if (audioLevelRef.current) {
      clearTimeout(audioLevelRef.current);
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
    }
  };

  const nextQuestion = async () => {
    try {
      setVoiceState(prev => ({ ...prev, status: 'processing' }));
      
      let nextQuestionText;

      if (agentServiceType === 'direct' && isAgentConnected) {
        // Use DirectAgentService for hybrid mode
        const sessionId = voiceState.sessionId || directAgentService.createSession();
        const response = await directAgentService.sendMessage(
          'Please provide the next interview question. Continue with the same difficulty level and topic.',
          sessionId
        );
        
        nextQuestionText = response.content;
      } else if (agentServiceType === 'api') {
        // Use existing Bedrock Agent service for normal mode
        const response = await bedrockAgentService.sendMessage(
          'Please provide the next interview question. Continue with the same difficulty level and topic.',
          voiceState.sessionId || 'default'
        );
        
        if (response && (response as any).success && (response as any).response) {
          nextQuestionText = (response as any).response;
        } else {
          throw new Error('Failed to get next question from agent');
        }
      } else {
        // Mock mode
        const mockQuestions = [
          'Can you describe a challenging project you worked on?',
          'How do you handle working under pressure?',
          'What are your greatest strengths and weaknesses?',
          'Where do you see yourself in 5 years?'
        ];
        nextQuestionText = mockQuestions[Math.floor(Math.random() * mockQuestions.length)];
      }
      
      if (nextQuestionText) {
        setVoiceState(prev => ({
          ...prev,
          status: 'active',
          currentQuestion: nextQuestionText,
          transcription: '',
          interimTranscription: ''
        }));
        
        // Reset timer
        setTimeRemaining(180);
        setIsPaused(false);
        
        // Speak the new question
        speakText(nextQuestionText);
      }
      
    } catch (error) {
      console.error('Failed to get next question:', error);
      setVoiceState(prev => ({
        ...prev,
        error: 'Failed to get next question'
      }));
    }
  };

  const endSession = async () => {
    try {
      // Stop recording
      stopRecording();
      
      // Request interview analysis
      if (voiceState.sessionId) {
        let analysisData;

        if (agentServiceType === 'direct' && isAgentConnected) {
          // Use DirectAgentService for hybrid mode
          try {
            const feedback = await directAgentService.conductInterview(
              voiceState.sessionId,
              voiceState.transcription || 'Interview session completed'
            );
            
            analysisData = {
              overall_score: feedback.score * 10, // Convert to percentage
              feedback: [feedback.feedback],
              strengths: feedback.strengths,
              areas_for_improvement: feedback.improvements,
              recommendations: feedback.suggestions
            };
          } catch (error) {
            console.warn('Failed to get detailed analysis, using basic feedback');
            analysisData = {
              overall_score: 75,
              feedback: ['Interview session completed successfully'],
              strengths: ['Completed interview session'],
              areas_for_improvement: ['Continue practicing'],
              recommendations: ['Keep practicing regularly']
            };
          }
        } else if (agentServiceType === 'api') {
          // Use existing Bedrock Agent service for normal mode
          const response = await bedrockAgentService.sendMessage(
            'End the interview session and provide a comprehensive performance analysis with feedback.',
            voiceState.sessionId
          );
          
          if (response && (response as any).success && (response as any).response) {
            try {
              analysisData = JSON.parse((response as any).response);
            } catch {
              // If not JSON, create basic analysis
              analysisData = {
                overall_score: 75,
                feedback: [(response as any).response],
                strengths: ['Completed interview session'],
                areas_for_improvement: ['Continue practicing'],
                recommendations: ['Keep practicing regularly']
              };
            }
          }
        } else {
          // Mock mode
          analysisData = {
            overall_score: 70 + Math.floor(Math.random() * 25), // Random score 70-95
            feedback: ['Mock interview completed successfully', 'This is simulated feedback'],
            strengths: ['Good communication', 'Clear responses'],
            areas_for_improvement: ['Practice more technical questions', 'Work on confidence'],
            recommendations: ['Continue practicing regularly', 'Review common interview questions']
          };
        }

        if (analysisData) {
          saveInterviewSession(analysisData);
        }
      }
      
      // Reset state
      setVoiceState({
        sessionId: null,
        status: 'idle',
        currentQuestion: null,
        transcription: '',
        interimTranscription: '',
        audioLevel: 0,
        connectionStatus: 'disconnected',
        error: null
      });
      
      setTimeRemaining(0);
      setIsPaused(false);
      
      // Cleanup audio resources
      cleanupAudioResources();
      
    } catch (error) {
      console.error('Failed to end session:', error);
      setVoiceState(prev => ({
        ...prev,
        error: 'Failed to end session properly'
      }));
    }
  };

  const handleTimeUp = () => {
    // Auto-stop recording when time is up
    stopRecording();
    
    // Automatically move to next question after a brief pause
    setTimeout(() => {
      nextQuestion();
    }, 3000);
  };

  // Utility functions
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'text-green-600 bg-green-100 dark:bg-green-900/20';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20';
      case 'hard': return 'text-red-600 bg-red-100 dark:bg-red-900/20';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-700';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600';
      case 'processing': return 'text-blue-600';
      case 'starting': return 'text-yellow-600';
      case 'completed': return 'text-gray-600';
      default: return 'text-gray-500';
    }
  };

  const getConnectionStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return <SignalIcon className="h-4 w-4 text-green-500" />;
      case 'connecting': return <ArrowPathIcon className="h-4 w-4 text-yellow-500 animate-spin" />;
      default: return <SignalIcon className="h-4 w-4 text-red-500" />;
    }
  };

  // Session management
  const loadInterviewSessions = async () => {
    try {
      // Load from localStorage for now (could be replaced with API call)
      const savedSessions = localStorage.getItem('interview_sessions');
      if (savedSessions) {
        setSessions(JSON.parse(savedSessions));
      }
    } catch (error) {
      console.error('Failed to load interview sessions:', error);
    }
  };

  const saveInterviewSession = (analysis: any) => {
    const newSession: InterviewSession = {
      id: Date.now().toString(),
      title: `${selectedSubject} Interview Practice`,
      subject: selectedSubject,
      duration: Math.floor((180 - timeRemaining) / 60), // Calculate actual duration
      questionsAsked: 1, // Could be tracked more accurately
      score: analysis.overall_score || 75,
      completedAt: new Date().toISOString(),
      feedback: analysis.feedback || analysis.strengths || ['Interview completed successfully'],
      analysis: {
        overall_score: analysis.overall_score || 75,
        strengths: analysis.strengths || ['Completed interview session'],
        areas_for_improvement: analysis.areas_for_improvement || ['Continue practicing'],
        recommendations: analysis.recommendations || ['Keep practicing regularly']
      }
    };
    
    const updatedSessions = [newSession, ...sessions];
    setSessions(updatedSessions);
    
    // Save to localStorage
    try {
      localStorage.setItem('interview_sessions', JSON.stringify(updatedSessions));
    } catch (error) {
      console.error('Failed to save interview session:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 safe-area-padding transition-colors">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="container-responsive">
          <div className="py-4 sm:py-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                    Interview Practice
                  </h1>
                  <HybridModeIndicator />
                </div>
                <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300 mt-1">
                  {agentServiceType === 'direct' 
                    ? 'Practice interviews with direct AI agent integration and real-time feedback'
                    : agentServiceType === 'api'
                    ? 'Practice interviews with AI-powered questions and feedback'
                    : 'Practice interviews with mock AI responses (demo mode)'
                  }
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container-responsive py-6 sm:py-8">
        {voiceState.status === 'idle' ? (
          /* Setup Screen */
          <div className="max-w-4xl mx-auto">
            {/* Session Setup */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Start New Interview Session
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Interview Type
                  </label>
                  <select
                    value={selectedSubject}
                    onChange={(e) => setSelectedSubject(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
                  >
                    <option value="general">General Interview</option>
                    <option value="technical">Technical Interview</option>
                    <option value="behavioral">Behavioral Interview</option>
                    <option value="computer-science">Computer Science</option>
                    <option value="data-science">Data Science</option>
                    <option value="physics">Physics</option>
                    <option value="mathematics">Mathematics</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Difficulty Level
                  </label>
                  <select
                    value={selectedDifficulty}
                    onChange={(e) => setSelectedDifficulty(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-gray-100"
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
                
                <div className="flex items-end">
                  <button
                    onClick={startInterview}
                    disabled={(voiceState.status as string) === 'starting' || (agentServiceType !== 'mock' && !isAgentConnected)}
                    className="w-full px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                  >
                    {(voiceState.status as string) === 'starting' ? (
                      <>
                        <ArrowPathIcon className="h-5 w-5 mr-2 animate-spin" />
                        Starting...
                      </>
                    ) : (agentServiceType !== 'mock' && !isAgentConnected) ? (
                      <>
                        <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
                        AI Agent Offline
                      </>
                    ) : (
                      <>
                        <PlayIcon className="h-5 w-5 mr-2" />
                        Start {agentServiceType === 'mock' ? 'Mock' : 'Voice'} Interview
                      </>
                    )}
                  </button>
                </div>
              </div>
              
              {/* Connection Status */}
              <div className="mt-4 flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  {getConnectionStatusIcon(voiceState.connectionStatus)}
                  <span className="text-gray-600 dark:text-gray-300">
                    Voice Service: {voiceState.connectionStatus}
                  </span>
                </div>
                
                {voiceState.error && (
                  <div className="flex items-center space-x-2 text-red-600">
                    <ExclamationTriangleIcon className="h-4 w-4" />
                    <span>{voiceState.error}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Recent Sessions */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Recent Sessions
                </h2>
              </div>
              
              {sessions.length === 0 ? (
                <div className="p-8 text-center">
                  <MicrophoneIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                    No sessions yet
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400">
                    Start your first interview practice session
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {sessions.map((session) => (
                    <div key={session.id} className="p-6">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h3 className="font-medium text-gray-900 dark:text-gray-100">
                            {session.title}
                          </h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {session.subject} • {session.duration} minutes • {session.questionsAsked} questions
                          </p>
                        </div>
                        <div className="text-right">
                          <div className={`text-lg font-semibold ${
                            session.score >= 80 ? 'text-green-600' : 
                            session.score >= 60 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            {session.score}%
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {new Date(session.completedAt).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      
                      {/* Feedback and Analysis */}
                      <div className="space-y-3">
                        {session.feedback && session.feedback.length > 0 && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Feedback:</h4>
                            <div className="space-y-1">
                              {session.feedback.map((item, index) => (
                                <div key={index} className="text-sm text-gray-600 dark:text-gray-300 flex items-start">
                                  <span className="text-blue-500 mr-2">•</span>
                                  {item}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {session.analysis && (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                            {session.analysis.strengths && session.analysis.strengths.length > 0 && (
                              <div>
                                <h4 className="text-sm font-medium text-green-700 dark:text-green-300 mb-1 flex items-center">
                                  <CheckCircleIcon className="h-4 w-4 mr-1" />
                                  Strengths:
                                </h4>
                                <ul className="text-xs text-gray-600 dark:text-gray-300 space-y-1">
                                  {session.analysis.strengths.slice(0, 2).map((strength, index) => (
                                    <li key={index} className="flex items-start">
                                      <span className="text-green-500 mr-1">✓</span>
                                      {strength}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {session.analysis.areas_for_improvement && session.analysis.areas_for_improvement.length > 0 && (
                              <div>
                                <h4 className="text-sm font-medium text-yellow-700 dark:text-yellow-300 mb-1 flex items-center">
                                  <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                                  Improve:
                                </h4>
                                <ul className="text-xs text-gray-600 dark:text-gray-300 space-y-1">
                                  {session.analysis.areas_for_improvement.slice(0, 2).map((area, index) => (
                                    <li key={index} className="flex items-start">
                                      <span className="text-yellow-500 mr-1">→</span>
                                      {area}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Active Session */
          <div className="max-w-4xl mx-auto">
            {/* Session Status */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      voiceState.status === 'active' ? 'bg-green-500 animate-pulse' : 
                      voiceState.status === 'processing' ? 'bg-blue-500 animate-pulse' : 
                      'bg-gray-400'
                    }`} />
                    <span className={`font-medium ${getStatusColor(voiceState.status)}`}>
                      {voiceState.status.charAt(0).toUpperCase() + voiceState.status.slice(1)}
                    </span>
                  </div>
                  
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    Session: {voiceState.sessionId?.slice(-8) || 'None'}
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="flex items-center text-lg font-mono">
                    <ClockIcon className="h-5 w-5 mr-2 text-gray-500" />
                    <span className={timeRemaining <= 30 ? 'text-red-500' : 'text-gray-900 dark:text-gray-100'}>
                      {formatTime(timeRemaining)}
                    </span>
                  </div>
                  
                  <button
                    onClick={endSession}
                    className="px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                  >
                    End Session
                  </button>
                </div>
              </div>
            </div>
            
            {/* Question Display */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(selectedDifficulty)}`}>
                    {selectedDifficulty}
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {selectedSubject}
                  </span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <SpeakerWaveIcon className="h-5 w-5 text-blue-500" />
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    AI Interviewer
                  </span>
                </div>
              </div>
              
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Current Question:
                </h2>
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                    {voiceState.currentQuestion || 'Waiting for question...'}
                  </p>
                </div>
              </div>
              
              {/* Recording Controls */}
              <div className="flex items-center justify-center space-x-4">
                {voiceState.status === 'active' && mediaRecorderRef.current?.state !== 'recording' ? (
                  <button
                    onClick={startRecording}
                    className="px-8 py-4 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors flex items-center space-x-3 text-lg"
                  >
                    <MicrophoneIcon className="h-6 w-6" />
                    <span>Start Recording</span>
                  </button>
                ) : voiceState.status === 'active' && mediaRecorderRef.current?.state === 'recording' ? (
                  <div className="flex items-center space-x-4">
                    {!isPaused ? (
                      <button
                        onClick={pauseRecording}
                        className="px-6 py-3 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors flex items-center space-x-2"
                      >
                        <PauseIcon className="h-5 w-5" />
                        <span>Pause</span>
                      </button>
                    ) : (
                      <button
                        onClick={resumeRecording}
                        className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center space-x-2"
                      >
                        <PlayIcon className="h-5 w-5" />
                        <span>Resume</span>
                      </button>
                    )}
                    
                    <button
                      onClick={stopRecording}
                      className="px-8 py-4 bg-gray-600 text-white rounded-full hover:bg-gray-700 transition-colors flex items-center space-x-3 text-lg"
                    >
                      <StopIcon className="h-6 w-6" />
                      <span>Stop Recording</span>
                    </button>
                  </div>
                ) : (
                  <div className="px-8 py-4 bg-gray-300 text-gray-600 rounded-full flex items-center space-x-3 text-lg">
                    <MicrophoneIcon className="h-6 w-6" />
                    <span>
                      {voiceState.status === 'processing' ? 'Processing...' : 'Waiting...'}
                    </span>
                  </div>
                )}
                
                <button
                  onClick={nextQuestion}
                  disabled={voiceState.status === 'processing'}
                  className="px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                >
                  <ArrowPathIcon className="h-5 w-5" />
                  <span>Next Question</span>
                </button>
              </div>
              
              {/* Audio Level Indicator */}
              {voiceState.status === 'active' && mediaRecorderRef.current?.state === 'recording' && (
                <div className="mt-4 flex items-center justify-center">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${isPaused ? 'bg-yellow-500' : 'bg-red-500 animate-pulse'}`} />
                    <SpeakerWaveIcon className="h-5 w-5 text-red-500" />
                    <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-red-500 transition-all duration-100"
                        style={{ width: `${Math.min(voiceState.audioLevel * 2, 100)}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-500">
                      {isPaused ? 'Paused' : 'Recording...'}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Transcription */}
            {(voiceState.transcription || voiceState.interimTranscription) && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                  <DocumentTextIcon className="h-5 w-5 mr-2" />
                  Live Transcription
                  {voiceState.status === 'processing' && (
                    <ArrowPathIcon className="h-4 w-4 ml-2 animate-spin text-blue-500" />
                  )}
                </h3>
                
                <div className="space-y-3">
                  {/* Final transcription */}
                  {voiceState.transcription && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Final:</div>
                      <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                        {voiceState.transcription}
                      </p>
                    </div>
                  )}
                  
                  {/* Interim transcription */}
                  {voiceState.interimTranscription && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border-l-4 border-blue-500">
                      <div className="text-xs text-blue-600 dark:text-blue-400 mb-2">Processing:</div>
                      <p className="text-blue-700 dark:text-blue-300 leading-relaxed italic">
                        {voiceState.interimTranscription}
                      </p>
                    </div>
                  )}
                </div>
                
                {/* Transcription tips */}
                <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                  <p>💡 Speak clearly and at a moderate pace for best transcription accuracy</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default InterviewPractice;