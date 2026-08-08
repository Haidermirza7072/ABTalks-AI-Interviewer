import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Volume2, VolumeX, Lightbulb, Star, Mic } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '../../types';
import { useStore } from '../../store/useStore';
import { speakWithNaturalVoice, cancelSpeech } from '../../utils/speechUtils';

interface Props {
  message: ChatMessageType;
  isLatest?: boolean;
}

export const ChatMessage: React.FC<Props> = ({ message, isLatest }) => {
  const isInterviewer = message.role === 'interviewer';
  const isFeedback = message.kind === 'feedback';
  const isHint = message.kind === 'hint';
  const isSpecial = isFeedback || isHint;
  const { isTtsEnabled } = useStore();
  const [isPlaying, setIsPlaying] = useState(false);

  const speakMessage = () => {
    if (isPlaying) {
      cancelSpeech();
      setIsPlaying(false);
      return;
    }

    speakWithNaturalVoice(
      message.content,
      () => setIsPlaying(true),
      () => setIsPlaying(false),
      () => setIsPlaying(false)
    );
  };

  // Auto-speak new interviewer question if TTS is enabled & it's the latest question
  useEffect(() => {
    if (isInterviewer && isLatest && isTtsEnabled && !isSpecial) {
      speakMessage();
    }
  }, [message.id, isLatest, isTtsEnabled]);

  const headerLabel = isFeedback ? 'AI Feedback' : isHint ? 'AI Hint' : 'Interviewer';
  const headerColor = isFeedback
    ? 'text-emerald-600 dark:text-emerald-400'
    : isHint
    ? 'text-amber-600 dark:text-amber-400'
    : 'text-gray-500 dark:text-gray-400';

  const bubbleClass = isFeedback
    ? 'bg-emerald-50 border border-emerald-200 text-gray-800 rounded-tl-sm shadow-sm dark:bg-emerald-950/40 dark:border-emerald-900 dark:text-gray-100'
    : isHint
    ? 'bg-amber-50 border border-amber-200 text-gray-800 rounded-tl-sm shadow-sm dark:bg-amber-950/40 dark:border-amber-900 dark:text-gray-100'
    : isInterviewer
    ? 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100'
    : 'bg-blue-600 text-white rounded-tr-sm shadow-md';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex w-full ${isInterviewer ? 'justify-start' : 'justify-end'} mb-6`}
    >
      <div className={`flex flex-col max-w-[85%] sm:max-w-[75%] ${isInterviewer ? 'items-start' : 'items-end'}`}>
        
        {isInterviewer && (
          <div className="flex items-center justify-between w-full mb-1 px-1">
            <span className={`text-xs font-semibold flex items-center gap-1 ${headerColor}`}>
              <span className={`w-4 h-4 rounded flex items-center justify-center text-[10px] font-bold ${
                isFeedback
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300'
                  : isHint
                  ? 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300'
                  : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
              }`}>
                {isFeedback ? <Star className="w-2.5 h-2.5" /> : isHint ? <Lightbulb className="w-2.5 h-2.5" /> : 'AI'}
              </span>
              {headerLabel}
              {isFeedback && message.meta?.score != null && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-emerald-600 text-white text-[10px] font-bold dark:bg-emerald-500">
                  {message.meta.score}/10
                </span>
              )}
              {isFeedback && (message.meta?.fillers ?? 0) > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-red-100 text-red-700 text-[10px] font-semibold inline-flex items-center gap-1 dark:bg-red-900/50 dark:text-red-300">
                  <Mic className="w-2.5 h-2.5" /> {message.meta?.fillers} fillers
                </span>
              )}
            </span>

            <button
              onClick={speakMessage}
              className={`text-xs flex items-center gap-1 px-2 py-0.5 rounded transition-colors ${
                isPlaying 
                  ? 'text-blue-600 bg-blue-50 font-medium animate-pulse dark:text-blue-400 dark:bg-blue-900/40' 
                  : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
              }`}
              title={isPlaying ? "Stop audio" : "Read message out loud"}
            >
              {isPlaying ? <VolumeX className="w-3 h-3 text-blue-600 dark:text-blue-400" /> : <Volume2 className="w-3 h-3" />}
              <span>{isPlaying ? 'Speaking...' : 'Listen'}</span>
            </button>
          </div>
        )}
        
        <div 
          className={`px-5 py-3.5 rounded-2xl ${bubbleClass}`}
        >
          <p className="whitespace-pre-wrap leading-relaxed text-sm sm:text-base">
            {message.content}
          </p>
        </div>

        <span className="text-xs text-gray-400 mt-1 mx-1 dark:text-gray-500">
          {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
        
      </div>
    </motion.div>
  );
};
