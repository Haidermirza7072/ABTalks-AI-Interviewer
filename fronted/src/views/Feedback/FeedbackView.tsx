import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle2,
  TrendingUp,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  AlertTriangle,
  History as HistoryIcon,
  Download,
} from 'lucide-react';
import { useStore } from '../../store/useStore';
import { Button } from '../../components/shared/Button';
import { saveCurrentConversation, isCurrentConversationSaved } from '../../utils/conversationUtils';

export const FeedbackView: React.FC = () => {
  const { feedback, resetSession, session, setActiveScreen, messages, interviewMode } = useStore();
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const savedRef = useRef(false);

  // Persist the finished interview into the user's long-term history once
  useEffect(() => {
    if (savedRef.current || !feedback) return;
    if (session.session_id && !isCurrentConversationSaved(session.session_id)) {
      saveCurrentConversation();
    }
    savedRef.current = true;
  }, [feedback, session.session_id]);

  if (!feedback) return null;

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'text-gray-400 border-gray-200 dark:border-gray-700';
    if (score >= 8) return 'text-green-600 border-green-200 dark:border-green-700';
    if (score >= 5) return 'text-amber-500 border-amber-200 dark:border-amber-700';
    return 'text-red-500 border-red-200 dark:border-red-700';
  };

  const getScoreBg = (score: number | null) => {
    if (score === null) return 'bg-gray-50 dark:bg-gray-800';
    if (score >= 8) return 'bg-green-50 dark:bg-green-900/30';
    if (score >= 5) return 'bg-amber-50 dark:bg-amber-900/30';
    return 'bg-red-50 dark:bg-red-900/30';
  };

  const downloadReport = () => {
    const lines: string[] = [];
    lines.push('=== THREAD PULLER - INTERVIEW REPORT ===');
    lines.push('');
    lines.push(`Candidate: ${session.candidate_id ?? 'N/A'}`);
    lines.push(`Date: ${new Date().toLocaleString()}`);
    lines.push(`Mode: ${interviewMode === 'practice' ? 'Practice' : 'Exam'}`);
    lines.push(`Status: ${session.status === 'completed' ? 'Completed' : 'Aborted'}${session.endReason === 'tab_switch' ? ' (auto-closed: tab switch detected)' : ''}`);
    lines.push('');
    lines.push(`READINESS SCORE: ${feedback.readiness_score ?? 'N/A'} / 10`);
    lines.push('');
    lines.push('STRENGTHS:');
    feedback.strengths.forEach((s) => lines.push(`  - ${s.title}: ${s.evidence}`));
    lines.push('');
    lines.push('AREAS FOR GROWTH:');
    feedback.growth_areas.forEach((g) => lines.push(`  - ${g.title}: ${g.resource}`));
    lines.push('');
    lines.push('COMMUNICATION TIPS:');
    feedback.communication_tips.forEach((t) => lines.push(`  - ${t}`));
    if (feedback.evidence_citations.length > 0) {
      lines.push('');
      lines.push('EVIDENCE LOG:');
      feedback.evidence_citations.forEach((c) => lines.push(`  - ${c}`));
    }
    lines.push('');
    lines.push('FULL TRANSCRIPT:');
    lines.push('='.repeat(60));
    messages.forEach((m) => {
      const who = m.role === 'interviewer' ? 'Interviewer' : 'Candidate';
      const kind = m.kind === 'feedback' ? ' [Feedback]' : m.kind === 'hint' ? ' [Hint]' : '';
      const time = new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      lines.push(`[${time}] ${who}${kind}:`);
      lines.push(m.content);
      lines.push('');
    });

    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `thread-puller-report-${session.candidate_id ?? 'candidate'}-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-gray-50 dark:bg-gray-950 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header / Score */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center dark:bg-gray-900 dark:border-gray-800"
        >
          {feedback.is_partial && session.endReason === 'tab_switch' && (
            <div className="mb-6 inline-flex items-center gap-2 px-4 py-2 bg-amber-50 text-amber-800 border border-amber-200 rounded-lg text-sm font-medium dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800">
              <AlertTriangle className="w-4 h-4" />
              Interview closed automatically — you switched away from the interview tab.
            </div>
          )}
          {feedback.is_partial && session.endReason !== 'tab_switch' && (
            <div className="mb-6 inline-flex items-center gap-2 px-4 py-2 bg-red-50 text-red-700 rounded-lg text-sm font-medium dark:bg-red-900/30 dark:text-red-300 dark:border dark:border-red-800">
              <AlertTriangle className="w-4 h-4" />
              This is a partial report. The interview was aborted early.
            </div>
          )}
          
          <h1 className="text-3xl font-bold text-gray-900 mb-6 dark:text-white">Interview Feedback</h1>
          
          <div className="flex justify-center mb-4">
            <div className={`w-32 h-32 rounded-full border-4 flex items-center justify-center flex-col ${getScoreColor(feedback.readiness_score)} ${getScoreBg(feedback.readiness_score)}`}>
              <span className="text-4xl font-black">
                {feedback.readiness_score !== null ? feedback.readiness_score : 'N/A'}
              </span>
              {feedback.readiness_score !== null && <span className="text-sm font-semibold opacity-80 uppercase tracking-widest mt-1">/ 10</span>}
            </div>
          </div>
          <p className="text-gray-500 font-medium uppercase tracking-widest text-sm dark:text-gray-400">Readiness Score</p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Strengths */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="space-y-4"
          >
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2 dark:text-white">
              <CheckCircle2 className="text-green-600 w-6 h-6" />
              Strengths
            </h2>
            <div className="space-y-4">
              {feedback.strengths.map((item, i) => (
                <div key={i} className="bg-green-50 border border-green-100 rounded-xl p-5 shadow-sm dark:bg-green-900/20 dark:border-green-900">
                  <h3 className="font-semibold text-green-900 mb-2 dark:text-green-300">{item.title}</h3>
                  <blockquote className="border-l-4 border-green-300 pl-4 text-green-800 text-sm italic dark:border-green-700 dark:text-green-200">
                    {item.evidence}
                  </blockquote>
                </div>
              ))}
              {feedback.strengths.length === 0 && <p className="text-gray-500 italic dark:text-gray-400">No significant strengths recorded for this session.</p>}
            </div>
          </motion.div>

          {/* Growth Areas */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-4"
          >
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2 dark:text-white">
              <TrendingUp className="text-amber-600 w-6 h-6" />
              Areas for Growth
            </h2>
            <div className="space-y-4">
              {feedback.growth_areas.map((item, i) => (
                <div key={i} className="bg-amber-50 border border-amber-100 rounded-xl p-5 shadow-sm dark:bg-amber-900/20 dark:border-amber-900">
                  <h3 className="font-semibold text-amber-900 mb-2 dark:text-amber-300">{item.title}</h3>
                  <div className="bg-amber-100/50 rounded p-3 text-amber-800 text-sm font-medium dark:bg-amber-900/40 dark:text-amber-200">
                    📘 {item.resource}
                  </div>
                </div>
              ))}
              {feedback.growth_areas.length === 0 && <p className="text-gray-500 italic dark:text-gray-400">No specific growth areas identified.</p>}
            </div>
          </motion.div>
        </div>

        {/* Communication Tips */}
        {feedback.communication_tips.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 dark:bg-gray-900 dark:border-gray-800"
          >
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2 mb-4 dark:text-white">
              <MessageSquare className="text-blue-600 w-6 h-6" />
              Communication Tips
            </h2>
            <ul className="space-y-3">
              {feedback.communication_tips.map((tip, i) => (
                <li key={i} className="flex items-start gap-3 text-gray-700 dark:text-gray-300">
                  <div className="mt-1 w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        )}

        {/* Evidence Log */}
        {feedback.evidence_citations.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden dark:bg-gray-900 dark:border-gray-800"
          >
            <button 
              onClick={() => setEvidenceOpen(!evidenceOpen)}
              className="w-full px-8 py-5 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors dark:bg-gray-800 dark:hover:bg-gray-800/70"
            >
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Evidence Log</h2>
              {evidenceOpen ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
            </button>
            <AnimatePresence>
              {evidenceOpen && (
                <motion.div 
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="px-8 pb-8 pt-4"
                >
                  <ul className="space-y-4">
                    {feedback.evidence_citations.map((cite, i) => (
                      <li key={i} className="text-sm text-gray-600 bg-gray-50 p-4 rounded-lg font-mono dark:text-gray-300 dark:bg-gray-800">
                        {cite}
                      </li>
                    ))}
                  </ul>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Action Footer */}
        <div className="flex flex-wrap justify-center gap-4 pt-8">
          <Button 
            onClick={downloadReport}
            variant="secondary"
            className="h-14 px-8"
            title="Download the full feedback report and transcript as a text file"
          >
            <Download className="w-5 h-5 mr-3" />
            Download Report
          </Button>
          <Button 
            onClick={() => {
              resetSession();
              setActiveScreen('history');
            }}
            variant="secondary"
            className="h-14 px-8"
          >
            <HistoryIcon className="w-5 h-5 mr-3" />
            View History
          </Button>
          <Button 
            onClick={() => {
              resetSession();
              setActiveScreen('landing');
            }}
            className="h-14 px-8 text-lg shadow-lg hover:shadow-xl transition-shadow"
          >
            <RotateCcw className="w-5 h-5 mr-3" />
            Start New Interview
          </Button>
        </div>

      </div>
    </div>
  );
};
