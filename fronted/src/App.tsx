import { Header } from './components/layout/Header';
import { GlobalErrorBoundary } from './components/layout/GlobalErrorBoundary';
import { LandingView } from './views/Landing/LandingView';
import { InterviewView } from './views/Interview/InterviewView';
import { FeedbackView } from './views/Feedback/FeedbackView';
import { HistoryView } from './views/History/HistoryView';
import { DashboardView } from './views/Dashboard/DashboardView';
import { LoadingOverlay } from './components/shared/LoadingOverlay';
import { useStore } from './store/useStore';

function AppContent() {
  const { activeScreen, isLoading } = useStore();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col font-sans">
      <Header />

      <main className="flex-1 relative">
        {activeScreen === 'landing' && <LandingView />}
        {activeScreen === 'chat' && <InterviewView />}
        {activeScreen === 'feedback' && <FeedbackView />}
        {activeScreen === 'history' && <HistoryView />}
        {activeScreen === 'dashboard' && <DashboardView />}
      </main>

      {isLoading && <LoadingOverlay />}
    </div>
  );
}

function App() {
  return (
    <GlobalErrorBoundary>
      <AppContent />
    </GlobalErrorBoundary>
  );
}

export default App;
