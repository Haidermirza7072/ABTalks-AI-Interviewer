import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { User, Play, Briefcase, GraduationCap, Timer, Lightbulb, Upload, FileText, X } from 'lucide-react';
import { Button } from '../../components/shared/Button';
import { useStore } from '../../store/useStore';
import { apiClient } from '../../api/client';
import { extractResumeText, type ResumeParseResult } from '../../utils/resumeParser';
import type { InterviewMode } from '../../types';

export const LandingView: React.FC = () => {
  const [candidateId, setCandidateId] = useState('');
  const [resume, setResume] = useState('');
  const [resumeFile, setResumeFile] = useState<ResumeParseResult | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [resumeError, setResumeError] = useState('');
  const [mode, setMode] = useState<InterviewMode>('exam');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { session, setSession, setActiveScreen, setIsLoading, setInterviewMode, setResumeText, clearTurnScores } = useStore();

  // Attempt to recover session if it exists and is active
  useEffect(() => {
    if (session.session_id && session.status !== 'completed' && session.status !== 'aborted') {
      // In a real app, we'd validate the session with the backend here.
      setActiveScreen('chat');
    }
  }, [session, setActiveScreen]);

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!candidateId.trim()) {
      setError('Please enter a Candidate ID');
      return;
    }
    if (candidateId.length > 50) {
      setError('Candidate ID must be less than 50 characters');
      return;
    }
    if (resume.length > 2000) {
      setError('Resume/experience must be less than 2000 characters');
      return;
    }
    
    setError('');
    setIsSubmitting(true);
    setIsLoading(true);
    setInterviewMode(mode);
    setResumeText(resume.trim());
    clearTurnScores();
    try {
      const response: any = await apiClient.startInterview(candidateId, resume.trim(), mode);
      
      setSession({
        session_id: response.session_id,
        candidate_id: candidateId,
        status: 'active',
        turn_count: response.turn_count,
        can_conclude: response.can_conclude,
        covered_days: response.covered_days,
        current_persona: response.current_persona as any,
      });

      // Add the first question
      useStore.getState().addMessage({
        role: 'interviewer',
        content: response.first_question,
        persona: response.current_persona as any,
      });

      setActiveScreen('chat');
    } catch (err) {
      setError('Failed to start interview. Please try again.');
    } finally {
      setIsSubmitting(false);
      setIsLoading(false);
    }
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;

    setResumeError('');
    setIsParsing(true);
    try {
      const parsed = await extractResumeText(file);
      setResumeFile(parsed);
      setResume(parsed.text);
      setResumeText(parsed.text);
    } catch (err) {
      setResumeFile(null);
      setResumeError(err instanceof Error ? err.message : 'Failed to parse the resume file.');
    } finally {
      setIsParsing(false);
    }
  };

  const clearResume = () => {
    setResumeFile(null);
    setResume('');
    setResumeError('');
  };

  const modeOptions: Array<{ value: InterviewMode; icon: React.ReactNode; title: string; desc: string }> = [
    {
      value: 'practice',
      icon: <Lightbulb className="w-5 h-5" />,
      title: 'Practice Mode',
      desc: 'No timer, hints allowed, can switch tabs',
    },
    {
      value: 'exam',
      icon: <Timer className="w-5 h-5" />,
      title: 'Exam Mode',
      desc: 'Per-question timer, no hints, tab-switch closes interview',
    },
  ];

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 dark:bg-gray-950">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-xl bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 dark:bg-gray-900 dark:border-gray-800"
      >
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 p-8 text-white text-center">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-6 backdrop-blur-sm">
            <Briefcase className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold mb-2 tracking-tight">The Thread Puller</h1>
          <p className="text-blue-100 font-medium">AI-Powered Technical Interview</p>
        </div>

        <div className="p-8">
          <div className="bg-blue-50 text-blue-800 p-4 rounded-xl mb-6 text-sm flex items-start gap-3 dark:bg-blue-900/30 dark:text-blue-200">
            <div className="mt-0.5">ℹ️</div>
            <p>This interview will cover topics from your 31-day cohort journey. Take a deep breath, and let's pull some threads!</p>
          </div>

          <form onSubmit={handleStart} className="space-y-6">
            <div>
              <label htmlFor="candidateId" className="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-300">
                Candidate ID
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  id="candidateId"
                  value={candidateId}
                  onChange={(e) => setCandidateId(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all sm:text-sm bg-gray-50 focus:bg-white dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100 dark:focus:bg-gray-800 dark:placeholder-gray-500"
                  placeholder="Enter your unique ID"
                  aria-invalid={!!error}
                  aria-describedby={error ? "candidateId-error" : undefined}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 dark:text-gray-300">
                Interview Mode
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {modeOptions.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setMode(opt.value)}
                    className={`text-left p-4 rounded-xl border-2 transition-all ${
                      mode === opt.value
                        ? 'border-blue-600 bg-blue-50 dark:border-blue-500 dark:bg-blue-900/40'
                        : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600'
                    }`}
                    aria-pressed={mode === opt.value}
                  >
                    <div className={`flex items-center gap-2 font-semibold mb-1 ${
                      mode === opt.value
                        ? 'text-blue-700 dark:text-blue-300'
                        : 'text-gray-800 dark:text-gray-200'
                    }`}>
                      <span className={mode === opt.value ? 'text-blue-600 dark:text-blue-400' : 'text-gray-400'}>
                        {opt.icon}
                      </span>
                      {opt.title}
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{opt.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="resume" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Resume / Experience <span className="text-gray-400 font-normal dark:text-gray-500">(optional)</span>
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.md,.pdf,.docx"
                  className="hidden"
                  onChange={handleResumeUpload}
                  aria-label="Upload resume"
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isParsing || isSubmitting}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
                    isParsing
                      ? 'bg-gray-100 text-gray-400 border-gray-200 cursor-wait dark:bg-gray-800 dark:text-gray-500 dark:border-gray-700'
                      : 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 dark:bg-blue-900/40 dark:text-blue-300 dark:border-blue-800 dark:hover:bg-blue-900/60'
                  }`}
                >
                  {isParsing ? (
                    <span className="w-3.5 h-3.5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin inline-block" />
                  ) : (
                    <Upload className="w-3.5 h-3.5" />
                  )}
                  {isParsing ? 'Parsing...' : 'Upload Resume'}
                </button>
              </div>

              {resumeFile && (
                <div className="flex items-center justify-between gap-2 mb-2 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-lg dark:bg-emerald-900/30 dark:border-emerald-800">
                  <span className="flex items-center gap-2 text-xs font-medium text-emerald-800 dark:text-emerald-300 min-w-0">
                    <FileText className="w-4 h-4 shrink-0" />
                    <span className="truncate">{resumeFile.fileName}</span>
                    <span className="text-emerald-600 dark:text-emerald-400 shrink-0">· {resumeFile.text.length} chars extracted</span>
                  </span>
                  <button
                    type="button"
                    onClick={clearResume}
                    className="p-1 rounded hover:bg-emerald-100 text-emerald-700 dark:hover:bg-emerald-800 dark:text-emerald-300"
                    title="Remove uploaded resume"
                    aria-label="Remove uploaded resume"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
              {resumeError && (
                <p className="mb-2 text-xs text-red-600 font-medium dark:text-red-400">{resumeError}</p>
              )}

              <div className="relative">
                <div className="absolute top-3 left-3 pointer-events-none">
                  <GraduationCap className="h-5 w-5 text-gray-400" />
                </div>
                <textarea
                  id="resume"
                  value={resume}
                  onChange={(e) => setResume(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all sm:text-sm bg-gray-50 focus:bg-white resize-none dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100 dark:focus:bg-gray-800 dark:placeholder-gray-500"
                  placeholder="Paste your skills, projects, or tech stack here, or upload a resume above. The AI will personalize the first question..."
                  rows={3}
                  maxLength={2000}
                />
              </div>
              <p className="mt-1 text-xs text-gray-400 dark:text-gray-500">{resume.length}/2000</p>
            </div>

            {error && (
              <p className="text-sm text-red-600 font-medium dark:text-red-400" id="candidateId-error">
                {error}
              </p>
            )}

            <Button 
              type="submit" 
              className="w-full h-12 text-base font-semibold"
              isLoading={isSubmitting}
            >
              Start Interview
              {!isSubmitting && <Play className="w-4 h-4 ml-2 fill-current" />}
            </Button>
          </form>
        </div>
      </motion.div>
    </div>
  );
};
