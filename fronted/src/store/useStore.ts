import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { AppState, ConversationRecord, ScreenState } from '../types';

const initialState = {
  activeScreen: 'landing' as ScreenState,
  globalError: null,
  session: {
    session_id: null,
    candidate_id: null,
    status: 'idle' as const,
    turn_count: 0,
    can_conclude: false,
    covered_days: [],
    current_persona: 'hiring_manager' as const,
  },
  messages: [],
  isLoading: false,
  isTyping: false,
  draftAnswer: '',
  feedback: null,
  timerDuration: 90, // default 90s timer per question
  isTtsEnabled: true, // TTS auto-read on by default
  isMicActive: false,
  darkMode: false,
  interviewMode: 'exam' as const,
  resumeText: '',
  turnScores: [] as number[],
  history: [] as ConversationRecord[],
};

// Apply the saved theme to the DOM immediately on load (before React renders)
try {
  const persisted = JSON.parse(localStorage.getItem('thread-puller-storage') ?? '{}');
  if (persisted?.state?.darkMode) {
    document.documentElement.classList.add('dark');
  }
} catch {
  // ignore
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      ...initialState,
      setActiveScreen: (screen) => set({ activeScreen: screen }),
      setGlobalError: (error) => set({ globalError: error }),
      setSession: (sessionUpdate) => set((state) => ({ session: { ...state.session, ...sessionUpdate } })),
      addMessage: (msg) => set((state) => ({
        messages: [
          ...state.messages,
          {
            ...msg,
            id: crypto.randomUUID(),
            timestamp: new Date().toISOString()
          }
        ]
      })),
      setIsLoading: (isLoading) => set({ isLoading }),
      setIsTyping: (isTyping) => set({ isTyping }),
      setDraftAnswer: (draft) => set({ draftAnswer: draft }),
      setFeedback: (feedback) => set({ feedback }),
      setTimerDuration: (seconds) => set({ timerDuration: seconds }),
      setIsTtsEnabled: (enabled) => set({ isTtsEnabled: enabled }),
      setIsMicActive: (active) => set({ isMicActive: active }),
      setDarkMode: (enabled) => {
        set({ darkMode: enabled });
        if (enabled) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      },
      setInterviewMode: (mode) => set({ interviewMode: mode }),
      setResumeText: (text) => set({ resumeText: text }),
      addTurnScore: (score) => set((state) => ({ turnScores: [...state.turnScores, score] })),
      clearTurnScores: () => set({ turnScores: [] }),
      saveConversation: (record) => set((state) => ({
        history: [record, ...state.history.filter((c) => c.id !== record.id)].slice(0, 100),
      })),
      deleteConversation: (conversationId) => set((state) => ({
        history: state.history.filter((c) => c.id !== conversationId),
      })),
      resetSession: () => set((state) => ({
        ...initialState,
        darkMode: state.darkMode, // preserve theme preference across sessions
        history: state.history, // preserve long-term history across sessions
      })),
    }),
    {
      name: 'thread-puller-storage', // name of item in the storage (must be unique)
      storage: createJSONStorage(() => localStorage), // (optional) by default the 'localStorage' is used
      partialize: (state) => ({
        // only persist these fields
        session: state.session,
        messages: state.messages,
        draftAnswer: state.draftAnswer,
        activeScreen: state.activeScreen === 'chat' ? 'chat' : 'landing', // only recover chat or landing
        history: state.history,
        darkMode: state.darkMode,
      }),
    }
  )
);
