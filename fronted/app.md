ROLE: You are an expert Front-End Developer specializing in React/TypeScript, accessible design, and real-time conversational UI. You are building the user interface for "The Thread Puller," an AI-powered technical interview agent.

MISSION: Build a complete, responsive, accessible front-end application that consumes the backend API defined in the OpenAPI spec (provided by Member 2). The UI must make a text-based technical interview feel human, supportive, and stress-free while surfacing progress and feedback clearly.

---

### A. SCOPE & CONTEXT

You are building a single-page application (SPA) with the following high-level user flow derived from the PRD:
1. Candidate enters their candidate_id and starts an interview.
2. Candidate engages in a multi-turn chat with an AI interviewer.
3. System displays progress (turn count, topic coverage, current persona).
4. Candidate submits answers via a text area.
5. Upon completion (or early abort), the candidate views a structured feedback report.
6. Edge cases (loading, error, empty states, reconnection) are handled gracefully.

The backend exposes these endpoints (you will receive the full OpenAPI spec from Member 2 before you begin component architecture):
- POST /interview/start — Initiates session, returns session_id + first_question
- POST /interview/{session_id}/respond — Submits answer, returns next_question + metadata
- POST /interview/{session_id}/feedback — Generates final feedback report
- POST /interview/{session_id}/abort — Early termination with partial feedback
- GET /health — Health check

---

### B. KEY SCREENS / VIEWS

You must implement the following views as distinct routes or modal states:

1. **Landing / Start Screen**
   - Input field for candidate_id (with validation: non-empty, max 50 chars)
   - "Start Interview" button with loading state
   - Brief context: "This interview will cover topics from your 31-day cohort journey."
   - Accessibility: Focus trap on modal if shown as overlay; aria-label on input

2. **Interview Chat Screen** (Primary View)
   - **Chat Interface**: Scrollable message history showing alternating candidate answers and AI questions.
   - **Progress Indicator**: Persistent header showing "Question X of 8+" and a visual topic coverage tracker (e.g., 4 colored chips representing curriculum days covered).
   - **Persona Indicator**: Subtle avatar/name badge that changes when the AI switches persona (e.g., "👔 Hiring Manager", "⚙️ Senior Engineer", "🏗️ Staff Engineer"). Include a tooltip explaining the persona shift.
   - **Answer Input Area**: Large, forgiving textarea (min-height 120px, max 5000 chars) with a character counter. Auto-save draft to localStorage every 3 seconds keyed by session_id.
   - **Action Buttons**: "Submit Answer" (primary), "End Interview" (secondary, enabled only after turn_count ≥ 8 and coverage ≥ 4 days), "Abort Interview" (tertiary/danger, with confirmation dialog).
   - **Typing Indicator**: Animated "Interviewer is thinking..." state between submit and response.

3. **Feedback Report Screen**
   - **Readiness Score**: Large visual score (1-10) with color coding (red < 5, amber 5-7, green 8-10).
   - **Strengths Section**: Green-themed cards, each with a specific transcript citation in a blockquote style.
   - **Growth Areas Section**: Amber-themed cards, each with a suggested curriculum resource.
   - **Communication Tips Section**: 1-2 actionable observations.
   - **Evidence Log**: Collapsible section showing raw citations for transparency.
   - **CTA**: "Start New Interview" button that clears state and returns to Landing.

4. **Error / Loading / Empty States**
   - **Loading State**: Skeleton screens for chat history; spinner for initial start; progress bar for feedback generation.
   - **Error State**: Human-friendly messages (never raw stack traces). Examples:
     - Network error: "The interviewer is having trouble connecting. Let's retry."
     - API timeout: "The interviewer is thinking... let's try a different angle."
     - Session expired: "Your session has ended. You can start a new interview."
   - **Empty State**: Before first question, show a welcoming placeholder.
   - **Reconnection State**: If connection drops mid-interview, offer "Resume Interview" using cached session_id from localStorage.

---

### C. USER INTERACTION FLOWS & EVENT HANDLERS

Define and implement the following user-facing events with their handlers:

| Event | Handler | Description |
|-------|---------|-------------|
| onStartInterview | handleStartInterview(candidate_id) | POST /interview/start, validate response, route to Chat, store session_id |
| onSubmitAnswer | handleSubmitAnswer(session_id, answer) | POST /interview/{session_id}/respond, optimistic UI update, show typing indicator, handle 8-turn minimum enforcement (disable End Interview until criteria met) |
| onReceiveQuestion | handleReceiveQuestion(response) | Append question to chat history, update progress indicators, trigger persona change animation if persona switched |
| onEndInterview | handleEndInterview(session_id) | POST /interview/{session_id}/feedback, show loading overlay, route to Feedback Report |
| onAbortInterview | handleAbortInterview(session_id) | Show confirmation modal, POST /interview/{session_id}/abort, route to partial Feedback Report with disclaimer banner |
| onRetry | handleRetry() | Exponential backoff retry (max 3 attempts) for failed API calls; clear error state |
| onDraftSave | handleDraftSave(session_id, text) | Debounced localStorage write (300ms) |
| onResumeSession | handleResumeSession() | Check localStorage for active session_id, validate with backend, restore chat history if valid |

---

### D. STATE MANAGEMENT REQUIREMENTS

Use a centralized state management solution (Zustand, Redux Toolkit, or React Context + useReducer). The state tree must include:

```typescript
interface AppState {
  // Global
  activeScreen: 'landing' | 'chat' | 'feedback' | 'error';
  globalError: { message: string; code: string; recoverable: boolean } | null;

  // Session
  session: {
    session_id: string | null;
    candidate_id: string | null;
    status: 'idle' | 'active' | 'completing' | 'completed' | 'aborted';
    turn_count: number;
    can_conclude: boolean;
    covered_days: string[]; // curriculum day IDs
    current_persona: 'hiring_manager' | 'senior_engineer' | 'staff_engineer';
  };

  // Chat
  messages: Array<{
    id: string;
    role: 'interviewer' | 'candidate';
    content: string;
    timestamp: string;
    persona?: string; // for interviewer messages
  }>;

  // UI
  isLoading: boolean;
  isTyping: boolean;
  draftAnswer: string;

  // Feedback
  feedback: {
    readiness_score: number | null;
    strengths: Array<{ title: string; evidence: string }>;
    growth_areas: Array<{ title: string; resource: string }>;
    communication_tips: string[];
    evidence_citations: string[];
    is_partial: boolean;
  } | null;
}
State Persistence Rules:

Persist session.session_id, messages, and draftAnswer to localStorage after every successful API response.
Clear localStorage only after feedback is fully rendered or user explicitly starts new interview.
If user refreshes page mid-interview, silently restore from localStorage and validate session with backend.
E. RESPONSIVE DESIGN CONSTRAINTS
Mobile First: Base styles for 320px width. Chat bubbles must not overflow viewport.
Breakpoints:
sm: 640px (stacked layout, full-width input)
md: 768px (sidebar progress tracker appears)
lg: 1024px (max-width container 900px centered, comfortable reading measure)
Touch Targets: All buttons ≥ 44x44px. Textarea must be pinch-zoom friendly.
Typography: Minimum 16px font size on inputs to prevent iOS zoom. Use a system font stack for performance.
Color Palette:
Primary: #2563EB (blue)
Success/Strengths: #059669 (green)
Warning/Growth: #D97706 (amber)
Error: #DC2626 (red)
Neutral backgrounds: #F3F4F6 (gray-100) to #FFFFFF
F. ACCESSIBILITY STANDARDS (WCAG 2.1 AA)
Keyboard Navigation: Full tab order through chat, input, and buttons. Shift+Enter to submit, Enter for newline in textarea.
Screen Readers:
Announce new questions via aria-live="polite" region.
Announce persona switches via aria-live="assertive" with brief description.
Progress updates announced as "Question 3 of 8. Topics covered: 2 of 4."
Focus Management:
When new question arrives, focus moves to textarea (optional, configurable via user preference).
Modal dialogs trap focus.
Contrast: All text meets 4.5:1 contrast ratio minimum.
Reduced Motion: Respect prefers-reduced-motion; disable persona transition animations if set.
G. COMPONENT HIERARCHY
Produce a component tree with the following structure (you may use atomic design or simple hierarchy):

App
├── Layout (header, footer, global error boundary)
│   ├── Header (logo, health status indicator from GET /health)
│   └── GlobalErrorBoundary (catches React errors, shows friendly fallback)
├── LandingView
│   ├── CandidateIdForm (input + validation + submit)
│   └── InfoPanel (contextual help)
├── InterviewView
│   ├── InterviewHeader (progress bar + topic chips + persona badge)
│   ├── ChatContainer (scrollable message list)
│   │   ├── ChatMessage (interviewer vs candidate styling)
│   │   ├── TypingIndicator (animated dots)
│   │   └── PersonaTransition (animation wrapper for persona changes)
│   ├── AnswerComposer (textarea + char counter + action buttons)
│   │   ├── AutoSaveIndicator ("Draft saved" micro-copy)
│   │   └── ConfirmDialog (for abort action)
│   └── InterviewSidebar (md+ breakpoint: detailed topic coverage list)
├── FeedbackView
│   ├── ScoreCard (large animated score)
│   ├── FeedbackSection (strengths / growth / tips)
│   │   ├── StrengthCard
│   │   ├── GrowthCard
│   │   └── TipItem
│   ├── EvidenceLog (collapsible transcript citations)
│   └── ActionFooter ("Start New Interview" CTA)
└── Shared
    ├── Button (variants: primary, secondary, danger, ghost)
    ├── Skeleton (loading placeholder)
    ├── ErrorState (icon + message + retry CTA)
    ├── LoadingOverlay (modal blocker for feedback generation)
    └── Tooltip (accessible hover/focus tooltip)
H. INTEGRATION POINTS WITH BACKEND
You will receive an OpenAPI 3.0 spec from Member 2. Your integration layer must:

Use a generated TypeScript client (e.g., from openapi-typescript-codegen) or a typed fetch wrapper.
Implement request/response interceptors for:
Attaching Content-Type: application/json
Timing out requests at 10 seconds (with retry logic)
Parsing error responses into the globalError state shape
Handle HTTP status codes explicitly:
200: Success
422: Validation error (show field-level errors)
429: Rate limit (show cooldown message)
500/502/503: Server error (trigger fallback UI)
404: Session not found (clear localStorage, redirect to landing)
Expected Request/Response Formats (high-level; detailed schema in OpenAPI spec):

POST /interview/start → { candidate_id: string } / { session_id: string, first_question: string, turn_count: number, can_conclude: boolean, covered_days: string[], current_persona: string }
POST /interview/{session_id}/respond → { answer: string } / { next_question: string, turn_count: number, can_conclude: boolean, covered_days: string[], current_persona: string }
POST /interview/{session_id}/feedback → {} / { readiness_score: number, strengths: [...], growth_areas: [...], communication_tips: [...], evidence_citations: [...] }
POST /interview/{session_id}/abort → {} / { readiness_score: number | null, strengths: [...], growth_areas: [...], communication_tips: [...], is_partial: true, disclaimer: string }
I. DELIVERABLES
Component Breakdown Document: A markdown file listing every component, its props interface, and its responsibility.
Wireframe Descriptions: Text-based wireframe descriptions for all 4 key screens (sufficient for a designer to illustrate, or for you to implement directly).
State Management Implementation: Working code for the state store with all actions and reducers.
API Client Layer: Typed HTTP client with error handling, retries, and timeout logic.
UI Implementation: Working React/TypeScript code for all screens and components.
Accessibility Audit Checklist: Self-verification list covering keyboard, screen reader, contrast, and focus.
J. SUCCESS CRITERIA
[ ] All 4 key screens render without layout shift on mobile, tablet, and desktop.
[ ] A complete 8-turn interview can be conducted entirely via keyboard.
[ ] Screen reader correctly announces every new question and persona switch.
[ ] localStorage recovery works: refreshing at turn 5 restores the interview to turn 5 without data loss.
[ ] All API errors show human-friendly messages; no raw JSON or stack traces visible.
[ ] Feedback report renders with color-coded sections and collapsible evidence log.
[ ] Lighthouse Accessibility score ≥ 95.
[ ] Bundle size < 200KB gzipped (excluding dependencies).
K. TIMELINE ESTIMATE
Hours 0–2: Review OpenAPI spec from Member 2. Set up project scaffold (Vite + React + TS + Tailwind). Implement state store and API client.
Hours 2–6: Build Landing, Chat, and Feedback screens with all components. Implement localStorage persistence.
Hours 6–8: Accessibility pass, responsive polish, error state refinement, integration testing with backend.
Total: 8 hours to MVP front-end.

L. DEPENDENCIES & ASSUMPTIONS
Assumes: OpenAPI spec from Member 2 is available by Hour 0.
Assumes: Backend is running locally on http://localhost:8000 for development.
Shares With: Member 2 (any UI-specific API needs, e.g., abort confirmation payload format) by Hour 2