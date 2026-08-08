import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from './Button';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ message, onRetry }) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center space-y-4 bg-red-50 rounded-lg border border-red-100 dark:bg-red-900/20 dark:border-red-900">
      <div className="p-3 bg-red-100 rounded-full dark:bg-red-900/50">
        <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
      </div>
      <div className="max-w-md space-y-2">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Something went wrong</h3>
        <p className="text-sm text-gray-600 dark:text-gray-300">{message}</p>
      </div>
      {onRetry && (
        <Button onClick={onRetry} variant="primary">
          Try Again
        </Button>
      )}
    </div>
  );
};
