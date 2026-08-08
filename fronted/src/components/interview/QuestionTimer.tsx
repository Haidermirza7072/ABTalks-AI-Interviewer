import React from 'react';
import { Timer, AlertCircle } from 'lucide-react';
import { Tooltip } from '../shared/Tooltip';

interface Props {
  duration: number; // Initial total duration in seconds
  timeLeft: number; // Remaining seconds
  isActive: boolean; // Is counting down
}

export const QuestionTimer: React.FC<Props> = ({ duration, timeLeft, isActive: _isActive }) => {
  const percentage = Math.max(0, Math.min(100, (timeLeft / duration) * 100));
  
  // Color calculation based on remaining time
  const isCritical = timeLeft <= 10;
  const isWarning = timeLeft > 10 && timeLeft <= 30;

  const strokeColor = isCritical 
    ? '#ef4444' // red-500
    : isWarning 
    ? '#f59e0b' // amber-500
    : '#3b82f6'; // blue-500

  const textColor = isCritical 
    ? 'text-red-600 font-bold animate-pulse dark:text-red-400' 
    : isWarning 
    ? 'text-amber-600 font-semibold dark:text-amber-400' 
    : 'text-gray-700 font-medium dark:text-gray-200';

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const radius = 14;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <Tooltip content="Time remaining for this turn. Auto-submits on timeout.">
      <div 
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all ${
          isCritical 
            ? 'bg-red-50 border-red-200 shadow-sm shadow-red-100 ring-2 ring-red-400/30 dark:bg-red-900/30 dark:border-red-800 dark:shadow-red-900/20' 
            : isWarning 
            ? 'bg-amber-50 border-amber-200 dark:bg-amber-900/30 dark:border-amber-800' 
            : 'bg-gray-50 border-gray-200 dark:bg-gray-800 dark:border-gray-700'
        }`}
      >
        <div className="relative w-7 h-7 flex items-center justify-center">
          <svg className="w-7 h-7 transform -rotate-90">
            <circle
              cx="14"
              cy="14"
              r={radius}
              className="stroke-gray-200 dark:stroke-gray-700"
              strokeWidth="2.5"
              fill="transparent"
            />
            <circle
              cx="14"
              cy="14"
              r={radius}
              stroke={strokeColor}
              strokeWidth="2.5"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-500 ease-linear"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            {isCritical ? (
              <AlertCircle className="w-3.5 h-3.5 text-red-500 animate-bounce" />
            ) : (
              <Timer className={`w-3.5 h-3.5 ${isWarning ? 'text-amber-500' : 'text-blue-500'}`} />
            )}
          </div>
        </div>

        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-wider text-gray-400 font-semibold leading-none dark:text-gray-500">
            Timer
          </span>
          <span className={`text-xs font-mono tracking-tight leading-tight ${textColor}`}>
            {formatTime(timeLeft)}
          </span>
        </div>
      </div>
    </Tooltip>
  );
};
