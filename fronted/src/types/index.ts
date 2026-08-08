export type ScreenState = 'landing' | 'chat' | 'feedback' | 'history' | 'dashboard' | 'error';

export interface GlobalError {
  message: string;
  code: string;
  recoverable: boolean;
}

export type Persona = 'hiring_manager' | 'senior_engineer' | 'staff_engineer';
export type MessageRole = 'interviewer' | 'candidate';
export type MessageKind = 'question' | 'answer' | 'feedback' | 'hint';
export type InterviewMode = 'practice' | 'exam';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  persona?: Persona;
  kind?: MessageKind;
  meta?: {
    score?: number | null;
    fillers?: number;
  };
}

export interface ConversationRecord {
  id: string;
  session_id: string;
  candidateId: string;
  startedAt: string;
  endedAt: string;
  status: 'completed' | 'aborted';
  endReason?: 'manual' | 'tab_switch';
  turnCount: number;
  persona: Persona;
  messages: ChatMessage[];
  feedback: FeedbackData | null;
}

export interface FeedbackData {
  readiness_score: number | null;
  strengths: Array<{ title: string; evidence: string }>;
  growth_areas: Array<{ title: string; resource: string }>;
  communication_tips: string[];
  evidence_citations: string[];
  is_partial: boolean;
}

export interface AppState {
  // Global
  activeScreen: ScreenState;
  globalError: GlobalError | null;

  // Session
  session: {
    session_id: string | null;
    candidate_id: string | null;
    status: 'idle' | 'active' | 'completing' | 'completed' | 'aborted';
    endReason?: 'manual' | 'tab_switch';
    turn_count: number;
    can_conclude: boolean;
    covered_days: string[]; // curriculum day IDs
    current_persona: Persona;
  };

  // Chat
  messages: ChatMessage[];

  // UI
  isLoading: boolean;
  isTyping: boolean;
  draftAnswer: string;

  // Feedback
  feedback: FeedbackData | null;
  
  // Settings & Voice
  timerDuration: number; // in seconds, default 90
  isTtsEnabled: boolean; // text-to-speech auto-read
  isMicActive: boolean; // speech-to-text recording state
  darkMode: boolean; // dark theme preference

  // Interview configuration
  interviewMode: InterviewMode;
  resumeText: string;
  turnScores: number[]; // per-answer AI scores

  // History
  history: ConversationRecord[]; // long-term conversation history
  
  // Actions
  setActiveScreen: (screen: ScreenState) => void;
  setGlobalError: (error: GlobalError | null) => void;
  setSession: (session: Partial<AppState['session']>) => void;
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setIsLoading: (isLoading: boolean) => void;
  setIsTyping: (isTyping: boolean) => void;
  setDraftAnswer: (draft: string) => void;
  setFeedback: (feedback: FeedbackData | null) => void;
  setTimerDuration: (seconds: number) => void;
  setIsTtsEnabled: (enabled: boolean) => void;
  setIsMicActive: (active: boolean) => void;
  setDarkMode: (enabled: boolean) => void;
  setInterviewMode: (mode: InterviewMode) => void;
  setResumeText: (text: string) => void;
  addTurnScore: (score: number) => void;
  clearTurnScores: () => void;
  saveConversation: (record: ConversationRecord) => void;
  deleteConversation: (conversationId: string) => void;
  resetSession: () => void;
}
