import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Volume2, VolumeX } from 'lucide-react';
import { Tooltip } from '../../components/shared/Tooltip';
import type { InterviewMode, Persona } from '../../types';
import { QuestionTimer } from '../../components/interview/QuestionTimer';
import { useStore } from '../../store/useStore';
import { cancelSpeech } from '../../utils/speechUtils';

interface Props {
  turnCount: number;
  coveredDays: string[];
  currentPersona: Persona;
  interviewMode: InterviewMode;
  timeLeft: number | null;
}

const personaConfig = {
  hiring_manager: { icon: '👔', name: 'Hiring Manager', color: 'bg-blue-100 text-blue-800 border-blue-200' },
  senior_engineer: { icon: '⚙️', name: 'Senior Engineer', color: 'bg-purple-100 text-purple-800 border-purple-200' },
  staff_engineer: { icon: '🏗️', name: 'Staff Engineer', color: 'bg-amber-100 text-amber-800 border-amber-200' },
};

export const InterviewHeader: React.FC<Props> = ({ turnCount, coveredDays, currentPersona, interviewMode, timeLeft }) => {
  const config = personaConfig[currentPersona];
  const { timerDuration, isTtsEnabled, setIsTtsEnabled, isTyping } = useStore();
  const isPractice = interviewMode === 'practice';

  const toggleTts = () => {
    if (isTtsEnabled) {
      cancelSpeech();
    }
    setIsTtsEnabled(!isTtsEnabled);
  };

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-3 sticky top-0 z-10 shadow-sm flex flex-wrap items-center justify-between gap-3 dark:bg-gray-900 dark:border-gray-800">
      
      <div className="flex items-center gap-3 sm:gap-4">
        <div className="flex flex-col">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider dark:text-gray-400">Progress</span>
          <span className="font-bold text-gray-900 dark:text-white">Question {turnCount} of 8+</span>
        </div>
        
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide border ${
          isPractice
            ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/40 dark:text-emerald-300 dark:border-emerald-800'
            : 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/40 dark:text-red-300 dark:border-red-800'
        }`}>
          {isPractice ? 'Practice' : 'Exam'}
        </span>
        
        <div className="h-8 w-px bg-gray-200 hidden sm:block dark:bg-gray-700"></div>
        
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider mr-1 hidden sm:inline-block dark:text-gray-400">Topics:</span>
          {coveredDays.slice(0, 4).map((day) => (
            <div key={day} className="w-2.5 h-2.5 rounded-full bg-green-500 shadow-sm" title={`Covered: ${day}`} />
          ))}
          {coveredDays.length < 4 && Array.from({ length: 4 - coveredDays.length }).map((_, i) => (
            <div key={`empty-${i}`} className="w-2.5 h-2.5 rounded-full bg-gray-200" />
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Per-Question Timer (exam mode only) */}
        {timeLeft !== null && (
          <QuestionTimer 
            duration={timerDuration} 
            timeLeft={timeLeft} 
            isActive={!isTyping} 
          />
        )}

        {/* Text to Speech Voice Toggle */}
        <Tooltip content={isTtsEnabled ? "Mute interviewer voice" : "Enable interviewer voice readout"}>
          <button
            onClick={toggleTts}
            className={`p-2 rounded-full border transition-all ${
              isTtsEnabled 
                ? 'bg-blue-50 border-blue-200 text-blue-600 hover:bg-blue-100 dark:bg-blue-900/40 dark:border-blue-800 dark:text-blue-400 dark:hover:bg-blue-900/60' 
                : 'bg-gray-100 border-gray-200 text-gray-400 hover:bg-gray-200 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-500 dark:hover:bg-gray-700'
            }`}
            aria-label={isTtsEnabled ? "Disable Text to Speech" : "Enable Text to Speech"}
          >
            {isTtsEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
          </button>
        </Tooltip>

        {/* Persona Indicator */}
        <Tooltip content="The AI switches personas to evaluate different skills.">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentPersona}
              initial={{ opacity: 0, scale: 0.8, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: 10 }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${config.color}`}
            >
              <span className="text-lg" aria-hidden="true">{config.icon}</span>
              <span className="text-sm font-semibold hidden md:inline">{config.name}</span>
            </motion.div>
          </AnimatePresence>
        </Tooltip>
      </div>

    </div>
  );
};
