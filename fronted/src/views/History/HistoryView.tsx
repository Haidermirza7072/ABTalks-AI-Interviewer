import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { History, Trash2, MessageSquare, CheckCircle2, XCircle, Calendar, User as UserIcon } from 'lucide-react';
import { Button } from '../../components/shared/Button';
import { useStore } from '../../store/useStore';
import { openConversation } from '../../utils/conversationUtils';
import type { ConversationRecord } from '../../types';

export const HistoryView: React.FC = () => {
  const { history, deleteConversation, setActiveScreen, resetSession } = useStore();
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  const handleDelete = (id: string) => {
    if (confirmDelete === id) {
      deleteConversation(id);
      setConfirmDelete(null);
    } else {
      setConfirmDelete(id);
      setTimeout(() => setConfirmDelete(null), 3000);
    }
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });

  const goToLanding = () => {
    resetSession();
    setActiveScreen('landing');
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-gray-50 dark:bg-gray-950 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-wrap items-center justify-between gap-4 mb-8"
        >
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center dark:bg-blue-900 dark:text-blue-300">
              <History className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Interview History</h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {history.length} saved {history.length === 1 ? 'conversation' : 'conversations'}
              </p>
            </div>
          </div>
          <Button variant="secondary" onClick={goToLanding} className="h-10 px-4">
            Start New Interview
          </Button>
        </motion.div>

        {history.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-12 text-center"
          >
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-8 h-8 text-gray-400" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">No interviews yet</h2>
            <p className="text-gray-500 dark:text-gray-400 text-sm mb-6">
              Complete an interview and your conversation will be saved here automatically.
            </p>
            <Button onClick={goToLanding}>Take Your First Interview</Button>
          </motion.div>
        ) : (
          <div className="space-y-4">
            {history.map((record: ConversationRecord, index) => (
              <motion.div
                key={record.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.04 }}
                className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                        {record.candidateId}
                      </span>
                      {record.status === 'completed' ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 dark:text-green-400 dark:bg-green-900/40 px-2 py-0.5 rounded-full">
                          <CheckCircle2 className="w-3 h-3" /> Completed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-red-700 bg-red-50 dark:text-red-400 dark:bg-red-900/40 px-2 py-0.5 rounded-full">
                          <XCircle className="w-3 h-3" /> Aborted
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
                      <span className="inline-flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" /> {formatDate(record.startedAt)}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <MessageSquare className="w-3.5 h-3.5" /> {Math.floor(record.messages.length / 2)} turns
                      </span>
                      {record.feedback?.readiness_score != null && (
                        <span className="inline-flex items-center gap-1 font-semibold text-blue-700 dark:text-blue-400">
                          Score: {record.feedback.readiness_score}/10
                        </span>
                      )}
                      <span className="inline-flex items-center gap-1">
                        <UserIcon className="w-3.5 h-3.5" /> {record.persona.replace('_', ' ')}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant="secondary"
                      onClick={() => openConversation(record)}
                      className="h-9 px-4 text-xs"
                    >
                      View Feedback
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => handleDelete(record.id)}
                      className={`h-9 px-3 text-xs ${
                        confirmDelete === record.id
                          ? 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/30'
                          : 'text-gray-400 hover:text-red-600 dark:text-gray-500 dark:hover:text-red-400'
                      }`}
                      title={confirmDelete === record.id ? 'Click again to confirm delete' : 'Delete interview'}
                    >
                      <Trash2 className="w-4 h-4" />
                      {confirmDelete === record.id && <span className="ml-1">Confirm?</span>}
                    </Button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
