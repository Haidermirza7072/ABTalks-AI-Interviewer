import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useStore } from '../../store/useStore';
import { InterviewHeader } from './InterviewHeader';
import { ChatMessage } from './ChatMessage';
import { AnswerComposer, type AnswerComposerHandle } from './AnswerComposer';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, XCircle } from 'lucide-react';
import { apiClient } from '../../api/client';
import { cancelSpeech } from '../../utils/speechUtils';

export const InterviewView: React.FC = () => {
  const {
    session,
    messages,
    isTyping,
    timerDuration,
    interviewMode,
    setSession,
    setFeedback,
    setActiveScreen,
  } = useStore();
  const [timeLeft, setTimeLeft] = useState(timerDuration);
  const [isTerminating, setIsTerminating] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const composerRef = useRef<AnswerComposerHandle>(null);
  const sessionRef = useRef(session);
  sessionRef.current = session;
  const autoAbortHandledRef = useRef(false);
  const isExam = interviewMode === 'exam';

  // Auto-close the interview the moment the candidate switches away from the tab (exam mode only)
  const handleAutoAbort = useCallback(async () => {
    if (autoAbortHandledRef.current) return;
    const current = sessionRef.current;
    if (!current.session_id || current.status === 'completed' || current.status === 'aborted') return;

    autoAbortHandledRef.current = true;
    cancelSpeech(); // Instantly silence the AI voice
    setIsTerminating(true); // Show "exam closed" screen immediately

    try {
      const feedback = await apiClient.abortInterview(current.session_id);
      setSession({ status: 'aborted', endReason: 'tab_switch' });
      setFeedback(feedback as any);
      setActiveScreen('feedback');
    } catch (err) {
      console.error('Failed to auto-abort interview after tab switch:', err);
      setSession({ status: 'aborted', endReason: 'tab_switch' });
      setActiveScreen('feedback');
    }
  }, [setSession, setFeedback, setActiveScreen]);

  useEffect(() => {
    if (!isExam) return; // practice mode: tab switching is allowed
    const handleVisibilityChange = () => {
      if (document.hidden) {
        handleAutoAbort();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [handleAutoAbort, isExam]);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Reset timer whenever a new turn starts or turn_count updates
  useEffect(() => {
    setTimeLeft(timerDuration);
  }, [session.turn_count, messages.length, timerDuration]);

  // Per-second countdown timer interval (exam mode only)
  useEffect(() => {
    if (!isExam) return;
    if (isTyping || session.status !== 'idle' && session.status !== 'active') return;

    const timerId = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timerId);
          // Timeout reached: trigger auto-submit in AnswerComposer
          composerRef.current?.submitOnTimeout();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timerId);
  }, [isTyping, session.turn_count, session.status, isExam]);

  const handleManualSubmit = () => {
    setTimeLeft(timerDuration);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-gray-50 dark:bg-gray-950">
      <InterviewHeader 
        turnCount={session.turn_count} 
        coveredDays={session.covered_days} 
        currentPersona={session.current_persona} 
        interviewMode={interviewMode}
        timeLeft={isExam ? timeLeft : null}
      />
      
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8" aria-live="polite">
        <div className="max-w-4xl mx-auto flex flex-col">
          
          <AnimatePresence initial={false}>
            {messages.map((msg, index) => (
              <ChatMessage 
                key={msg.id} 
                message={msg} 
                isLatest={index === messages.length - 1} 
              />
            ))}
          </AnimatePresence>

          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start mb-6"
            >
              <div className="bg-white border border-gray-200 px-5 py-4 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-2 text-gray-500 dark:bg-gray-900 dark:border-gray-700 dark:text-gray-400">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span className="text-sm font-medium">Interviewer is thinking...</span>
              </div>
            </motion.div>
          )}
          
          <div ref={chatEndRef} />
        </div>
      </div>

      <AnswerComposer ref={composerRef} onManualSubmit={handleManualSubmit} />

      {/* Exam-style termination overlay: shown instantly on tab switch */}
      <AnimatePresence>
        {isTerminating && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-gray-900/95 flex items-center justify-center p-6"
            role="alertdialog"
            aria-label="Interview terminated"
          >
            <motion.div
              initial={{ scale: 0.9, y: 10 }}
              animate={{ scale: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="text-center max-w-md"
            >
              <div className="w-20 h-20 mx-auto rounded-full bg-red-600/20 border-4 border-red-600 flex items-center justify-center mb-6">
                <XCircle className="w-10 h-10 text-red-500" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Interview Terminated</h2>
              <p className="text-gray-300">
                Tab switching was detected. The interview has been closed automatically.
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
