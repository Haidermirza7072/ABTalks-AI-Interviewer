import React from 'react';
import { Sun, Moon, History, BarChart3 } from 'lucide-react';
import { useStore } from '../../store/useStore';
import { cancelSpeech } from '../../utils/speechUtils';

export const Header: React.FC = () => {
  const { darkMode, setDarkMode, setActiveScreen, resetSession } = useStore();

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const goToHistory = () => {
    cancelSpeech();
    resetSession();
    setActiveScreen('history');
  };

  const goToDashboard = () => {
    cancelSpeech();
    resetSession();
    setActiveScreen('dashboard');
  };

  const goToLanding = () => {
    cancelSpeech();
    resetSession();
    setActiveScreen('landing');
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-white/80 backdrop-blur-md border-b border-gray-200 dark:bg-gray-900/80 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <button onClick={goToLanding} className="flex items-center gap-2" aria-label="Go to home">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-xl">
            T
          </div>
          <span className="font-semibold text-lg text-gray-900 hidden sm:block dark:text-white">
            The Thread Puller
          </span>
        </button>

        <div className="flex items-center gap-2 text-sm">
          <button
            onClick={goToDashboard}
            className="p-2.5 rounded-full border border-gray-200 text-gray-600 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
            title="Performance dashboard"
            aria-label="Performance dashboard"
          >
            <BarChart3 className="w-4 h-4" />
          </button>

          <button
            onClick={goToHistory}
            className="p-2.5 rounded-full border border-gray-200 text-gray-600 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
            title="Interview history"
            aria-label="Interview history"
          >
            <History className="w-4 h-4" />
          </button>

          <button
            onClick={toggleDarkMode}
            className="p-2.5 rounded-full border border-gray-200 text-gray-600 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </header>
  );
};
