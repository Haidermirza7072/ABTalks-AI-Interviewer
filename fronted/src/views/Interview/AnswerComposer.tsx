import React, { useState, useEffect, useRef, useImperativeHandle, forwardRef } from 'react';
import { Send, Square, Mic, MicOff, Lightbulb, Code2, PenLine } from 'lucide-react';
import { Button } from '../../components/shared/Button';
import { useStore } from '../../store/useStore';
import { apiClient } from '../../api/client';
import { Tooltip } from '../../components/shared/Tooltip';
import { cancelSpeech } from '../../utils/speechUtils';
import { analyzeFillers, fillerTip } from '../../utils/fillerWords';

export interface AnswerComposerHandle {
  submitOnTimeout: () => void;
}

interface Props {
  onManualSubmit?: () => void;
}

export const AnswerComposer = forwardRef<AnswerComposerHandle, Props>(({ onManualSubmit }, ref) => {
  const { session, setSession, draftAnswer, setDraftAnswer, addMessage, setIsTyping, setActiveScreen, setFeedback, setIsMicActive, messages, turnScores, addTurnScore, interviewMode } = useStore();
  const [localDraft, setLocalDraft] = useState(draftAnswer);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAborting, setIsAborting] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [isHintLoading, setIsHintLoading] = useState(false);
  const [codeMode, setCodeMode] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);
  const baseTextRef = useRef<string>('');
  const latestTranscriptRef = useRef<string>('');
  const autoSubmitOnEndRef = useRef<boolean>(false);
  const handleSubmitRef = useRef<(customAnswer?: string) => void>(() => {});
  const currentQuestionRef = useRef<string>('');

  const currentQuestion = [...messages].reverse().find((m) => m.role === 'interviewer' && m.kind !== 'feedback' && m.kind !== 'hint')?.content ?? '';
  currentQuestionRef.current = currentQuestion;

  // Initialize Web Speech Recognition API if available
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      let speechAccumulated = '';
      for (let i = 0; i < event.results.length; i++) {
        speechAccumulated += event.results[i][0].transcript + ' ';
      }

      const trimmedSpeech = speechAccumulated.trim();
      const updatedText = baseTextRef.current 
        ? `${baseTextRef.current.trim()} ${trimmedSpeech}` 
        : trimmedSpeech;

      latestTranscriptRef.current = updatedText;
      setLocalDraft(updatedText);
      setDraftAnswer(updatedText);
    };

    recognition.onerror = (event: any) => {
      console.warn('Speech recognition error:', event.error);
      autoSubmitOnEndRef.current = false;
      setIsListening(false);
      setIsMicActive(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      setIsMicActive(false);

      // Auto-send the spoken answer to the chat when the mic is stopped
      if (autoSubmitOnEndRef.current) {
        autoSubmitOnEndRef.current = false;
        const transcript = latestTranscriptRef.current.trim();
        if (transcript) {
          baseTextRef.current = '';
          latestTranscriptRef.current = '';
          handleSubmitRef.current(transcript);
        } else {
          setTimeout(() => textareaRef.current?.focus(), 100);
        }
      } else {
        setTimeout(() => textareaRef.current?.focus(), 100);
      }
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.stop();
      } catch (err) {
        // ignore
      }
    };
  }, [setIsMicActive, setDraftAnswer]);

  const toggleListening = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      autoSubmitOnEndRef.current = true; // Auto-send recognized speech once recording stops
      try {
        recognitionRef.current.stop();
      } catch (err) {
        console.warn('Error stopping recognition:', err);
      }
      setIsListening(false);
      setIsMicActive(false);
    } else {
      try {
        baseTextRef.current = localDraft; // Save baseline text before speech
        recognitionRef.current.start();
        setIsListening(true);
        setIsMicActive(true);
      } catch (err) {
        console.error('Failed to start speech recognition:', err);
      }
    }
  };

  // Debounced auto-save to global store
  useEffect(() => {
    const timer = setTimeout(() => {
      setDraftAnswer(localDraft);
    }, 500);
    return () => clearTimeout(timer);
  }, [localDraft, setDraftAnswer]);

  const handleSubmit = async (e?: React.FormEvent, customAnswer?: string) => {
    e?.preventDefault();
    
    // Stop speech recognition if listening
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
      setIsMicActive(false);
    }

    const answerToSubmit = customAnswer ?? localDraft;
    if (!answerToSubmit.trim() || !session.session_id || isSubmitting) return;

    setLocalDraft('');
    setIsSubmitting(true);
    onManualSubmit?.();
    
    // Optimistic UI update
    addMessage({
      role: 'candidate',
      content: answerToSubmit,
    });
    
    setIsTyping(true);

    try {
      const response: any = await apiClient.submitAnswer(session.session_id, answerToSubmit, session.turn_count);
      
      setSession({
        turn_count: response.turn_count,
        can_conclude: response.can_conclude,
        covered_days: response.covered_days,
        current_persona: response.current_persona as any,
      });

      if (response.answer_feedback) {
        addTurnScore(response.answer_feedback.score);
        const fillers = analyzeFillers(answerToSubmit);
        const extraLines: string[] = [];
        const tip = fillerTip(fillers.count);
        if (tip) extraLines.push(tip);

        addMessage({
          role: 'interviewer',
          kind: 'feedback',
          meta: { score: response.answer_feedback.score, fillers: fillers.count },
          content: [response.answer_feedback.comment, ...extraLines].filter(Boolean).join('\n'),
        });
      }

      addMessage({
        role: 'interviewer',
        content: response.next_question,
        persona: response.current_persona as any,
      });

      setCodeMode(!!response.is_coding);
      
      // Focus textarea after receiving new question
      setTimeout(() => textareaRef.current?.focus(), 100);
    } catch (error) {
      console.error('Failed to submit answer', error);
      setLocalDraft(answerToSubmit); 
    } finally {
      setIsSubmitting(false);
      setIsTyping(false);
    }
  };

  // Always point to the latest submit handler so speech callbacks use fresh state
  handleSubmitRef.current = (customAnswer?: string) => handleSubmit(undefined, customAnswer);

  // Expose timeout submit handler to parent InterviewView
  useImperativeHandle(ref, () => ({
    submitOnTimeout: () => {
      const textToSubmit = localDraft.trim() 
        ? localDraft 
        : '[Time Out - No response submitted in time]';
      handleSubmit(undefined, textToSubmit);
    }
  }));

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
    if (codeMode && e.key === 'Tab') {
      e.preventDefault();
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const next = `${target.value.slice(0, start)}  ${target.value.slice(end)}`;
      setLocalDraft(next);
      requestAnimationFrame(() => {
        target.selectionStart = target.selectionEnd = start + 2;
      });
    }
  };

  const handleHint = async () => {
    if (!session.session_id || isHintLoading || !currentQuestionRef.current) return;
    setIsHintLoading(true);
    try {
      const response: any = await apiClient.getHint(session.session_id, currentQuestionRef.current);
      addMessage({ role: 'interviewer', kind: 'hint', content: response.hint });
    } catch (err) {
      console.error('Failed to get hint', err);
    } finally {
      setIsHintLoading(false);
    }
  };

  const buildFeedback = (feedback: any) => {
    const avgScore = turnScores.length > 0
      ? Math.round((turnScores.reduce((a, b) => a + b, 0) / turnScores.length) * 10) / 10
      : null;

    const totalFillers = messages
      .filter((m) => m.role === 'candidate')
      .reduce((sum, m) => sum + analyzeFillers(m.content).count, 0);
    const tip = fillerTip(totalFillers);

    const merged = {
      ...feedback,
      readiness_score: avgScore ?? feedback.readiness_score,
      communication_tips: tip
        ? [...(feedback.communication_tips ?? []), tip]
        : feedback.communication_tips,
    };
    return merged;
  };

  const handleEndInterview = async () => {
    if (!session.session_id) return;
    cancelSpeech();
    setIsSubmitting(true);
    try {
      const feedback = await apiClient.getFeedback(session.session_id);
      setSession({ status: 'completed', endReason: 'manual' });
      setFeedback(buildFeedback(feedback));
      setActiveScreen('feedback');
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAbortInterview = async () => {
    if (!session.session_id) return;
    if (window.confirm("Are you sure you want to abort the interview? You will only receive partial feedback.")) {
      cancelSpeech();
      setIsAborting(true);
      try {
        const feedback = await apiClient.abortInterview(session.session_id);
        setSession({ status: 'aborted', endReason: 'manual' });
        setFeedback(buildFeedback(feedback));
        setActiveScreen('feedback');
      } catch (err) {
        console.error(err);
      } finally {
        setIsAborting(false);
      }
    }
  };

  const charsLeft = 5000 - localDraft.length;
  const hintDisabled = interviewMode === 'exam';

  return (
    <div className="bg-white border-t border-gray-200 p-4 shadow-lg dark:bg-gray-900 dark:border-gray-800">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={(e) => handleSubmit(e)}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setCodeMode((v) => !v)}
                disabled={isSubmitting || isAborting}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
                  codeMode
                    ? 'bg-indigo-600 text-white border-indigo-700 shadow-sm dark:bg-indigo-500 dark:border-indigo-600'
                    : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700 dark:hover:bg-gray-700'
                }`}
              >
                <Code2 className="w-4 h-4" />
                Code
              </button>
              <button
                type="button"
                onClick={() => setCodeMode(false)}
                disabled={isSubmitting || isAborting}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
                  !codeMode
                    ? 'bg-blue-600 text-white border-blue-700 shadow-sm dark:bg-blue-500 dark:border-blue-600'
                    : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700 dark:hover:bg-gray-700'
                }`}
              >
                <PenLine className="w-4 h-4" />
                Text
              </button>
            </div>

            <Tooltip content={hintDisabled ? "Hints are disabled in exam mode — try practice mode" : "Get a hint from the interviewer"}>
              <button
                type="button"
                onClick={handleHint}
                disabled={hintDisabled || isHintLoading || isSubmitting || isAborting}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
                  hintDisabled
                    ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed dark:bg-gray-800 dark:text-gray-600 dark:border-gray-700'
                    : 'bg-amber-50 text-amber-700 border-amber-300 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800 dark:hover:bg-amber-900/50'
                }`}
              >
                <Lightbulb className="w-4 h-4" />
                {isHintLoading ? 'Thinking...' : 'Hint'}
              </button>
            </Tooltip>
          </div>

          <div className="relative">
            <textarea
              ref={textareaRef}
              value={localDraft}
              onChange={(e) => setLocalDraft(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isListening ? "Listening... Speak your answer into the microphone..." : codeMode ? "Write your code here... (Tab indents)" : "Type your answer or click the mic and speak (auto-sends to chat when you stop)"}
              className={`w-full min-h-[120px] max-h-[300px] p-4 bg-gray-50 border rounded-xl resize-y focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all text-gray-900 placeholder-gray-400 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500 ${
                codeMode
                  ? 'font-mono text-sm bg-gray-950 text-emerald-300 placeholder-gray-600 border-gray-700 whitespace-pre overflow-x-auto dark:bg-black'
                  : 'sm:text-sm'
              } ${
                isListening ? 'border-red-400 bg-red-50/20 ring-2 ring-red-300 dark:bg-red-900/20 dark:border-red-700' : 'border-gray-300 dark:border-gray-700'
              }`}
              maxLength={5000}
              disabled={isSubmitting || isAborting}
              aria-label="Your answer"
            />

            <div className="absolute bottom-3 right-4 flex items-center gap-3">
              {/* Mic Toggle Button */}
              {speechSupported && !codeMode && (
                <Tooltip content={isListening ? "Stop & send your answer to chat" : "Click to speak your answer (auto-sends to chat when you stop)"}>
                  <button
                    type="button"
                    onClick={toggleListening}
                    disabled={isSubmitting || isAborting}
                    className={`p-2 rounded-full border transition-all flex items-center gap-1.5 text-xs font-semibold ${
                      isListening
                        ? 'bg-red-600 text-white border-red-700 animate-pulse shadow-md shadow-red-200 dark:shadow-red-900/40'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100 hover:text-blue-600 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700 dark:hover:bg-gray-700'
                    }`}
                  >
                    {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4 text-blue-600 dark:text-blue-400" />}
                    {isListening && <span className="pr-1 text-xs">Listening...</span>}
                  </button>
                </Tooltip>
              )}

              <span className={`text-xs ${charsLeft < 100 ? 'text-red-500 font-bold dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`}>
                {charsLeft}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between mt-3 gap-3">
            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              {isListening && (
                <span className="flex items-center text-red-600 font-medium dark:text-red-400">
                  <span className="w-2 h-2 rounded-full bg-red-600 animate-ping mr-1.5"></span>
                  Microphone active - Speaking...
                </span>
              )}
              {!isListening && draftAnswer === localDraft && localDraft.length > 0 && (
                <span className="flex items-center text-emerald-600 dark:text-emerald-400">✓ Draft saved</span>
              )}
            </div>
            
            <div className="flex items-center gap-2 ml-auto">
              <Button
                type="button"
                variant="ghost"
                onClick={handleAbortInterview}
                disabled={isSubmitting || isAborting}
                className="text-gray-500 hover:text-red-600 h-10 px-4 dark:text-gray-400 dark:hover:text-red-400"
              >
                Abort
              </Button>
              
              <Button
                type="button"
                variant="secondary"
                onClick={handleEndInterview}
                disabled={(interviewMode === 'exam' && !session.can_conclude) || isSubmitting || isAborting}
                className="h-10 px-4"
                title={interviewMode === 'exam' && !session.can_conclude ? "Complete at least 8 turns to end the interview (practice mode lets you end anytime)" : "End interview and get feedback"}
              >
                <Square className="w-4 h-4 mr-2" />
                End Interview
              </Button>
              
              <Button
                type="submit"
                variant="primary"
                disabled={!localDraft.trim() || isSubmitting || isAborting}
                isLoading={isSubmitting && !isAborting}
                className="h-10 px-6"
              >
                Submit Answer
                {!isSubmitting && <Send className="w-4 h-4 ml-2" />}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
});
