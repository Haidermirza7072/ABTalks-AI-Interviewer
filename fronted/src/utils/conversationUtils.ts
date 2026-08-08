import type { ConversationRecord } from '../types';
import { useStore } from '../store/useStore';

/** Build a history record from the current interview state and persist it. */
export const saveCurrentConversation = (): void => {
  const state = useStore.getState();
  const { session, messages, feedback } = state;
  if (!session.session_id || messages.length === 0) return;

  const firstMessage = messages[0];
  const record: ConversationRecord = {
    id: session.session_id,
    session_id: session.session_id,
    candidateId: session.candidate_id ?? 'guest',
    startedAt: firstMessage?.timestamp ?? new Date().toISOString(),
    endedAt: new Date().toISOString(),
    status: session.status === 'aborted' ? 'aborted' : 'completed',
    endReason: session.endReason,
    turnCount: session.turn_count,
    persona: session.current_persona,
    messages,
    feedback,
  };

  useStore.getState().saveConversation(record);
};

/** Check whether a conversation for the current session has already been saved. */
export const isCurrentConversationSaved = (sessionId: string | null): boolean => {
  if (!sessionId) return false;
  return useStore.getState().history.some((c) => c.session_id === sessionId);
};

/** Load a past conversation into the app store and show its feedback report. */
export const openConversation = (record: ConversationRecord): void => {
  const store = useStore.getState();

  store.setSession({
    session_id: record.session_id,
    candidate_id: record.candidateId,
    status: record.status,
    endReason: record.endReason,
    turn_count: record.turnCount,
    can_conclude: true,
    covered_days: [],
    current_persona: record.persona,
  });
  store.setFeedback(record.feedback);
  store.setActiveScreen('feedback');
};
