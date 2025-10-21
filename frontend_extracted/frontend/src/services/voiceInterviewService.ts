/**
 * Voice Interview Service
 * Handles WebRTC audio recording and real-time transcription
 * Task 15: Voice Interview Practice Integration
 */

export interface VoiceInterviewConfig {
  sampleRate: number;
  channels: number;
  bitsPerSample: number;
  bufferSize: number;
}

export interface TranscriptionResult {
  text: string;
  confidence: number;
  isFinal: boolean;
  timestamp: string;
}

export interface InterviewQuestion {
  id: string;
  text: string;
  category: string;
  difficulty: string;
  timeLimit: number;
}

export interface InterviewAnalysis {
  overall_score: number;
  clarity_score: number;
  content_accuracy: number;
  response_time_avg: number;
  strengths: string[];
  areas_for_improvement: string[];
  recommendations: string[];
  session_summary: string;
}

export class VoiceInterviewService {
  private mediaStream: MediaStream | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private audioChunks: Blob[] = [];
  private isRecording = false;
  private config: VoiceInterviewConfig;
  
  // Event handlers
  private onTranscriptionUpdate?: (result: TranscriptionResult) => void;
  private onAudioLevelUpdate?: (level: number) => void;
  private onError?: (error: string) => void;

  constructor(config: VoiceInterviewConfig) {
    this.config = config;
  }

  /**
   * Initialize audio recording capabilities
   */
  async initialize(): Promise<boolean> {
    try {
      // Request microphone access with specific constraints
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.config.sampleRate,
          channelCount: this.config.channels,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          latency: 0.01 // Low latency for real-time processing
        }
      });

      // Set up audio context for level monitoring
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: this.config.sampleRate
      });

      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.8;

      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      source.connect(this.analyser);

      // Set up MediaRecorder for audio capture
      const mimeType = this.getSupportedMimeType();
      this.mediaRecorder = new MediaRecorder(this.mediaStream, {
        mimeType,
        audioBitsPerSecond: 16000
      });

      this.setupMediaRecorderEvents();

      return true;
    } catch (error) {
      console.error('Failed to initialize voice interview service:', error);
      this.onError?.('Failed to access microphone. Please check permissions.');
      return false;
    }
  }

  /**
   * Start recording audio
   */
  startRecording(): boolean {
    if (!this.mediaRecorder || this.isRecording) {
      return false;
    }

    try {
      this.audioChunks = [];
      this.mediaRecorder.start(1000); // Capture in 1-second chunks for real-time processing
      this.isRecording = true;
      
      // Start audio level monitoring
      this.startAudioLevelMonitoring();
      
      return true;
    } catch (error) {
      console.error('Failed to start recording:', error);
      this.onError?.('Failed to start recording');
      return false;
    }
  }

  /**
   * Stop recording audio
   */
  stopRecording(): void {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.isRecording = false;
    }
  }

  /**
   * Pause recording
   */
  pauseRecording(): void {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.pause();
    }
  }

  /**
   * Resume recording
   */
  resumeRecording(): void {
    if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
      this.mediaRecorder.resume();
    }
  }

  /**
   * Get current recording state
   */
  getRecordingState(): string {
    return this.mediaRecorder?.state || 'inactive';
  }

  /**
   * Check if currently recording
   */
  isCurrentlyRecording(): boolean {
    return this.isRecording && this.mediaRecorder?.state === 'recording';
  }

  /**
   * Set event handlers
   */
  setEventHandlers(handlers: {
    onTranscriptionUpdate?: (result: TranscriptionResult) => void;
    onAudioLevelUpdate?: (level: number) => void;
    onError?: (error: string) => void;
  }): void {
    this.onTranscriptionUpdate = handlers.onTranscriptionUpdate;
    this.onAudioLevelUpdate = handlers.onAudioLevelUpdate;
    this.onError = handlers.onError;
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    this.stopRecording();
    
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
    
    this.analyser = null;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
  }

  /**
   * Convert audio blob to base64 for transmission
   */
  async audioToBase64(audioBlob: Blob): Promise<string> {
    const arrayBuffer = await audioBlob.arrayBuffer();
    const uint8Array = new Uint8Array(arrayBuffer);
    let binary = '';
    for (let i = 0; i < uint8Array.length; i++) {
      binary += String.fromCharCode(uint8Array[i]);
    }
    return btoa(binary);
  }

  /**
   * Simulate transcription (replace with actual AWS Transcribe integration)
   */
  private simulateTranscription(audioBlob: Blob): TranscriptionResult {
    // This is a mock implementation
    // In production, this would send audio to AWS Transcribe
    const mockTexts = [
      "Thank you for the question.",
      "Let me think about this for a moment.",
      "I believe the key concepts are...",
      "From my understanding...",
      "The main points I would highlight are...",
      "In my experience...",
      "To answer your question..."
    ];
    
    const randomText = mockTexts[Math.floor(Math.random() * mockTexts.length)];
    
    return {
      text: randomText,
      confidence: 0.85 + Math.random() * 0.1,
      isFinal: Math.random() > 0.3, // 70% chance of being final
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Get supported MIME type for MediaRecorder
   */
  private getSupportedMimeType(): string {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/wav'
    ];
    
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    
    return 'audio/webm'; // Fallback
  }

  /**
   * Set up MediaRecorder event handlers
   */
  private setupMediaRecorderEvents(): void {
    if (!this.mediaRecorder) return;

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.audioChunks.push(event.data);
        
        // Process audio chunk for real-time transcription
        this.processAudioChunk(event.data);
      }
    };

    this.mediaRecorder.onstop = () => {
      // Process final audio
      const finalAudioBlob = new Blob(this.audioChunks, { 
        type: this.mediaRecorder?.mimeType || 'audio/webm' 
      });
      
      this.processFinalAudio(finalAudioBlob);
    };

    this.mediaRecorder.onerror = (event) => {
      console.error('MediaRecorder error:', event);
      this.onError?.('Recording error occurred');
    };
  }

  /**
   * Process audio chunk for real-time transcription
   */
  private async processAudioChunk(audioBlob: Blob): Promise<void> {
    try {
      // Simulate real-time transcription
      const result = this.simulateTranscription(audioBlob);
      
      // Call transcription update handler
      this.onTranscriptionUpdate?.(result);
      
    } catch (error) {
      console.error('Failed to process audio chunk:', error);
    }
  }

  /**
   * Process final audio when recording stops
   */
  private async processFinalAudio(audioBlob: Blob): Promise<void> {
    try {
      // Generate final transcription
      const finalResult: TranscriptionResult = {
        text: "Thank you for your response. I've recorded your answer and will now provide feedback.",
        confidence: 0.95,
        isFinal: true,
        timestamp: new Date().toISOString()
      };
      
      this.onTranscriptionUpdate?.(finalResult);
      
    } catch (error) {
      console.error('Failed to process final audio:', error);
    }
  }

  /**
   * Monitor audio levels for visual feedback
   */
  private startAudioLevelMonitoring(): void {
    if (!this.analyser) return;

    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    
    const updateAudioLevel = () => {
      if (this.analyser && this.isRecording) {
        this.analyser.getByteFrequencyData(dataArray);
        
        // Calculate average audio level
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        
        // Normalize to 0-100 range
        const normalizedLevel = Math.min(100, (average / 128) * 100);
        
        this.onAudioLevelUpdate?.(normalizedLevel);
        
        // Continue monitoring
        requestAnimationFrame(updateAudioLevel);
      }
    };
    
    updateAudioLevel();
  }
}

/**
 * Text-to-Speech utility for AI responses
 */
export class TextToSpeechService {
  private synth: SpeechSynthesis;
  private voice: SpeechSynthesisVoice | null = null;

  constructor() {
    this.synth = window.speechSynthesis;
    this.initializeVoice();
  }

  /**
   * Initialize preferred voice
   */
  private initializeVoice(): void {
    const setVoice = () => {
      const voices = this.synth.getVoices();
      
      // Prefer professional-sounding voices
      this.voice = voices.find(voice => 
        voice.name.includes('Google') || 
        voice.name.includes('Microsoft') ||
        voice.name.includes('Alex') ||
        voice.name.includes('Samantha')
      ) || voices[0] || null;
    };

    if (this.synth.getVoices().length > 0) {
      setVoice();
    } else {
      this.synth.onvoiceschanged = setVoice;
    }
  }

  /**
   * Speak text with natural voice
   */
  speak(text: string, options?: {
    rate?: number;
    pitch?: number;
    volume?: number;
  }): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!text.trim()) {
        resolve();
        return;
      }

      // Cancel any ongoing speech
      this.synth.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      
      // Set voice and parameters
      if (this.voice) {
        utterance.voice = this.voice;
      }
      
      utterance.rate = options?.rate || 0.9;
      utterance.pitch = options?.pitch || 1.0;
      utterance.volume = options?.volume || 0.8;
      
      // Set event handlers
      utterance.onend = () => resolve();
      utterance.onerror = (event) => reject(new Error(`Speech synthesis error: ${event.error}`));
      
      // Start speaking
      this.synth.speak(utterance);
    });
  }

  /**
   * Stop current speech
   */
  stop(): void {
    this.synth.cancel();
  }

  /**
   * Check if currently speaking
   */
  isSpeaking(): boolean {
    return this.synth.speaking;
  }
}

// Export factory functions
export const createVoiceInterviewService = (config: VoiceInterviewConfig): VoiceInterviewService => {
  return new VoiceInterviewService(config);
};

export const createTextToSpeechService = (): TextToSpeechService => {
  return new TextToSpeechService();
};