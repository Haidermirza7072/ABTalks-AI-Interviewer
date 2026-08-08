import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Trophy, TrendingUp, BarChart3, ArrowLeft, RotateCcw } from 'lucide-react';
import { Button } from '../../components/shared/Button';
import { useStore } from '../../store/useStore';
import { analyzeFillers } from '../../utils/fillerWords';

export const DashboardView: React.FC = () => {
  const { history, setActiveScreen } = useStore();

  const stats = useMemo(() => {
    const scored = history.filter((c) => c.feedback?.readiness_score != null);
    const completed = history.filter((c) => c.status === 'completed').length;
    const aborted = history.filter((c) => c.status === 'aborted').length;
    const totalFillers = history.reduce((sum, c) => {
      return sum + c.messages.filter((m) => m.role === 'candidate').reduce((s, m) => s + analyzeFillers(m.content).count, 0);
    }, 0);
    const avg = scored.length > 0
      ? Math.round((scored.reduce((a, b) => a + (b.feedback?.readiness_score ?? 0), 0) / scored.length) * 10) / 10
      : null;
    const best = scored.length > 0
      ? Math.max(...scored.map((c) => c.feedback?.readiness_score ?? 0))
      : null;
    return { total: history.length, completed, aborted, totalFillers, avg, best };
  }, [history]);

  const chartData = useMemo(() => {
    return history
      .filter((c) => c.feedback?.readiness_score != null)
      .slice(0, 12)
      .reverse()
      .map((c) => ({
        id: c.id,
        label: new Date(c.startedAt).toLocaleDateString([], { month: 'short', day: 'numeric' }),
        score: c.feedback?.readiness_score ?? 0,
        status: c.status,
      }));
  }, [history]);

  const maxScore = 10;

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-gray-50 p-4 sm:p-8 dark:bg-gray-950">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl mx-auto"
      >
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 dark:text-white">
              <BarChart3 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              Performance Dashboard
            </h1>
            <p className="text-sm text-gray-500 mt-1 dark:text-gray-400">
              Track your interview practice over time
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button type="button" variant="secondary" onClick={() => setActiveScreen('history')}>
              <ArrowLeft className="w-4 h-4 mr-2" /> History
            </Button>
            <Button type="button" onClick={() => setActiveScreen('landing')}>
              <RotateCcw className="w-4 h-4 mr-2" /> New Interview
            </Button>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl border border-gray-200 dark:bg-gray-900 dark:border-gray-800">
            <Trophy className="w-12 h-12 text-gray-300 mx-auto mb-4 dark:text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200">No interviews yet</h2>
            <p className="text-sm text-gray-500 mt-1 dark:text-gray-400">
              Complete an interview and your stats will show up here.
            </p>
            <Button type="button" className="mt-6" onClick={() => setActiveScreen('landing')}>
              Start your first interview
            </Button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Stat cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white rounded-2xl border border-gray-200 p-5 dark:bg-gray-900 dark:border-gray-800">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide dark:text-gray-400">Interviews</p>
                <p className="text-3xl font-bold text-gray-900 mt-2 dark:text-white">{stats.total}</p>
                <p className="text-xs text-gray-400 mt-1 dark:text-gray-500">{stats.completed} completed · {stats.aborted} aborted</p>
              </div>
              <div className="bg-white rounded-2xl border border-gray-200 p-5 dark:bg-gray-900 dark:border-gray-800">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide dark:text-gray-400">Avg Score</p>
                <p className="text-3xl font-bold text-blue-600 mt-2 dark:text-blue-400">{stats.avg ?? '—'}</p>
                <p className="text-xs text-gray-400 mt-1 dark:text-gray-500">out of 10</p>
              </div>
              <div className="bg-white rounded-2xl border border-gray-200 p-5 dark:bg-gray-900 dark:border-gray-800">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide dark:text-gray-400">Best Score</p>
                <p className="text-3xl font-bold text-emerald-600 mt-2 dark:text-emerald-400">{stats.best ?? '—'}</p>
                <p className="text-xs text-gray-400 mt-1 dark:text-gray-500">personal record</p>
              </div>
              <div className="bg-white rounded-2xl border border-gray-200 p-5 dark:bg-gray-900 dark:border-gray-800">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide dark:text-gray-400">Filler Words</p>
                <p className="text-3xl font-bold text-amber-600 mt-2 dark:text-amber-400">{stats.totalFillers}</p>
                <p className="text-xs text-gray-400 mt-1 dark:text-gray-500">total um / uh / like</p>
              </div>
            </div>

            {/* Score trend chart */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 dark:bg-gray-900 dark:border-gray-800">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-900 flex items-center gap-2 dark:text-white">
                  <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  Score Trend
                </h2>
                {chartData.length > 0 && (
                  <span className="text-xs text-gray-400 dark:text-gray-500">last {chartData.length} scored interviews</span>
                )}
              </div>

              {chartData.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-8 dark:text-gray-400">
                  No scored interviews yet. Complete one to see your trend.
                </p>
              ) : (
                <div className="flex items-end justify-between gap-2 h-40">
                  {chartData.map((d) => (
                    <div key={d.id} className="flex-1 flex flex-col items-center gap-1 min-w-0">
                      <span className="text-[10px] font-semibold text-gray-500 dark:text-gray-400">{d.score}</span>
                      <div
                        className={`w-full max-w-[40px] rounded-t-lg transition-all ${
                          d.score >= 8
                            ? 'bg-emerald-500'
                            : d.score >= 6
                            ? 'bg-blue-500'
                            : d.score >= 4
                            ? 'bg-amber-500'
                            : 'bg-red-500'
                        }`}
                        style={{ height: `${Math.max((d.score / maxScore) * 100, 4)}%` }}
                        title={`${d.score}/10`}
                      />
                      <span className="text-[10px] text-gray-400 truncate w-full text-center dark:text-gray-500">{d.label}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};
