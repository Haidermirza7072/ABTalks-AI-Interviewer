import React from 'react';
import { Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';

interface LoadingOverlayProps {
  message?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ message = 'Loading...' }) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm dark:bg-gray-950/80">
      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center p-6 bg-white rounded-xl shadow-xl space-y-4 dark:bg-gray-900 dark:border dark:border-gray-800"
      >
        <Loader2 className="w-10 h-10 text-blue-600 animate-spin" />
        <p className="text-lg font-medium text-gray-900 dark:text-gray-100">{message}</p>
      </motion.div>
    </div>
  );
};
