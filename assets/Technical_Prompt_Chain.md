# Technical Prompt Chain: AI Interview Agent — "The Thread Puller"
**Document Version**: 1.0  
**Date**: 2026-08-08  
**Prepared By**: Technical Project Manager / Prompt Engineering Specialist  
**Project**: AI Cohort Hackathon — Interview Agent  
**Format**: 3-Part Atomic Prompt Chain + Coordination Matrix

---

## Overview

This document breaks the PRD into three **atomic, sequential, and actionable** prompts—one per team member. Each prompt is **self-contained** (can be executed independently by feeding it to an AI coding assistant or used as a technical specification) and **sequentially aware** (references the outputs expected from other streams). 

**Execution Model**: Each team member uses their prompt as a master instruction set. Deliverables are shared at defined integration gates.

---

## PART 1 — Member 1: Front-End Developer Prompt

```
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
```

**State Persistence Rules**:
- Persist `session.session_id`, `messages`, and `draftAnswer` to localStorage after every successful API response.
- Clear localStorage only after feedback is fully rendered or user explicitly starts new interview.
- If user refreshes page mid-interview, silently restore from localStorage and validate session with backend.

---

### E. RESPONSIVE DESIGN CONSTRAINTS

- **Mobile First**: Base styles for 320px width. Chat bubbles must not overflow viewport.
- **Breakpoints**: 
  - sm: 640px (stacked layout, full-width input)
  - md: 768px (sidebar progress tracker appears)
  - lg: 1024px (max-width container 900px centered, comfortable reading measure)
- **Touch Targets**: All buttons ≥ 44x44px. Textarea must be pinch-zoom friendly.
- **Typography**: Minimum 16px font size on inputs to prevent iOS zoom. Use a system font stack for performance.
- **Color Palette**: 
  - Primary: #2563EB (blue)
  - Success/Strengths: #059669 (green)
  - Warning/Growth: #D97706 (amber)
  - Error: #DC2626 (red)
  - Neutral backgrounds: #F3F4F6 (gray-100) to #FFFFFF

---

### F. ACCESSIBILITY STANDARDS (WCAG 2.1 AA)

- **Keyboard Navigation**: Full tab order through chat, input, and buttons. Shift+Enter to submit, Enter for newline in textarea.
- **Screen Readers**: 
  - Announce new questions via `aria-live="polite"` region.
  - Announce persona switches via `aria-live="assertive"` with brief description.
  - Progress updates announced as "Question 3 of 8. Topics covered: 2 of 4."
- **Focus Management**: 
  - When new question arrives, focus moves to textarea (optional, configurable via user preference).
  - Modal dialogs trap focus.
- **Contrast**: All text meets 4.5:1 contrast ratio minimum.
- **Reduced Motion**: Respect `prefers-reduced-motion`; disable persona transition animations if set.

---

### G. COMPONENT HIERARCHY

Produce a component tree with the following structure (you may use atomic design or simple hierarchy):

```
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
```

---

### H. INTEGRATION POINTS WITH BACKEND

You will receive an OpenAPI 3.0 spec from Member 2. Your integration layer must:
- Use a generated TypeScript client (e.g., from openapi-typescript-codegen) or a typed fetch wrapper.
- Implement request/response interceptors for:
  - Attaching `Content-Type: application/json`
  - Timing out requests at 10 seconds (with retry logic)
  - Parsing error responses into the `globalError` state shape
- Handle HTTP status codes explicitly:
  - 200: Success
  - 422: Validation error (show field-level errors)
  - 429: Rate limit (show cooldown message)
  - 500/502/503: Server error (trigger fallback UI)
  - 404: Session not found (clear localStorage, redirect to landing)

**Expected Request/Response Formats** (high-level; detailed schema in OpenAPI spec):
- `POST /interview/start` → `{ candidate_id: string }` / `{ session_id: string, first_question: string, turn_count: number, can_conclude: boolean, covered_days: string[], current_persona: string }`
- `POST /interview/{session_id}/respond` → `{ answer: string }` / `{ next_question: string, turn_count: number, can_conclude: boolean, covered_days: string[], current_persona: string }`
- `POST /interview/{session_id}/feedback` → `{}` / `{ readiness_score: number, strengths: [...], growth_areas: [...], communication_tips: [...], evidence_citations: [...] }`
- `POST /interview/{session_id}/abort` → `{}` / `{ readiness_score: number | null, strengths: [...], growth_areas: [...], communication_tips: [...], is_partial: true, disclaimer: string }`

---

### I. DELIVERABLES

1. **Component Breakdown Document**: A markdown file listing every component, its props interface, and its responsibility.
2. **Wireframe Descriptions**: Text-based wireframe descriptions for all 4 key screens (sufficient for a designer to illustrate, or for you to implement directly).
3. **State Management Implementation**: Working code for the state store with all actions and reducers.
4. **API Client Layer**: Typed HTTP client with error handling, retries, and timeout logic.
5. **UI Implementation**: Working React/TypeScript code for all screens and components.
6. **Accessibility Audit Checklist**: Self-verification list covering keyboard, screen reader, contrast, and focus.

---

### J. SUCCESS CRITERIA

- [ ] All 4 key screens render without layout shift on mobile, tablet, and desktop.
- [ ] A complete 8-turn interview can be conducted entirely via keyboard.
- [ ] Screen reader correctly announces every new question and persona switch.
- [ ] localStorage recovery works: refreshing at turn 5 restores the interview to turn 5 without data loss.
- [ ] All API errors show human-friendly messages; no raw JSON or stack traces visible.
- [ ] Feedback report renders with color-coded sections and collapsible evidence log.
- [ ] Lighthouse Accessibility score ≥ 95.
- [ ] Bundle size < 200KB gzipped (excluding dependencies).

---

### K. TIMELINE ESTIMATE

- **Hours 0–2**: Review OpenAPI spec from Member 2. Set up project scaffold (Vite + React + TS + Tailwind). Implement state store and API client.
- **Hours 2–6**: Build Landing, Chat, and Feedback screens with all components. Implement localStorage persistence.
- **Hours 6–8**: Accessibility pass, responsive polish, error state refinement, integration testing with backend.

**Total**: 8 hours to MVP front-end.

---

### L. DEPENDENCIES & ASSUMPTIONS

- **Assumes**: OpenAPI spec from Member 2 is available by Hour 0.
- **Assumes**: Backend is running locally on `http://localhost:8000` for development.
- **Shares With**: Member 2 (any UI-specific API needs, e.g., abort confirmation payload format) by Hour 2.
```

---

## PART 2 — Member 2: Back-End Developer Prompt

```
ROLE: You are an expert Back-End Developer specializing in FastAPI, Python, Pydantic, and LLM-integrated microservices. You are building the server, API, and data layer for "The Thread Puller," an AI-powered technical interview agent.

MISSION: Build a robust, performant, and well-documented backend that serves the front-end (Member 1), orchestrates the AI agent (Member 3), and exposes a compliant HTTP API per the hackathon technical specification. The system must handle stateful multi-turn conversations, validate all inputs, degrade gracefully under failure, and return structured JSON feedback.

---

### A. SCOPE & CONTEXT

You own the entire server-side stack:
- API layer (FastAPI) with full OpenAPI documentation
- Data models and validation (Pydantic v2)
- Session state management (in-memory + Redis fallback)
- LLM service integration (OpenRouter API)
- Curriculum and candidate profile data loading
- Request validation, rate limiting, error handling
- Fallback mechanisms for LLM failures
- Background session cleanup

The AI Agent Developer (Member 3) will provide you with:
- Prompt templates for question generation, follow-ups, and feedback synthesis
- Expected LLM output schemas (JSON structures)
- Guardrail logic for hallucination prevention

The Front-End Developer (Member 1) will consume your API. You must deliver an OpenAPI spec to them by Hour 2.

---

### B. DATA MODELS & ENTITIES

Define the following Pydantic models. These models are the contract between backend, frontend, and AI agent.

#### Entity 1: CandidateProfile
```python
class CandidateProfile(BaseModel):
    candidate_id: str
    completed_missions: List[str]  # mission IDs from curriculum
    skipped_topics: List[str]      # curriculum day IDs
    attempts: Dict[str, int]       # mission_id -> attempt count
    tools_used: List[str]          # e.g., ["ChromaDB", "LangChain"]
    learning_signals: Dict[str, Any]  # e.g., confidence scores, time spent
```

#### Entity 2: CurriculumDay
```python
class CurriculumDay(BaseModel):
    day_id: str
    title: str
    topics: List[str]
    learning_objectives: List[str]
    tools: List[str]
    prerequisites: List[str]
```

#### Entity 3: InterviewSession
```python
class InterviewSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    candidate_id: str
    status: Literal["active", "completed", "aborted"]
    created_at: datetime
    updated_at: datetime
    turn_count: int = 0
    can_conclude: bool = False
    covered_days: Set[str] = Field(default_factory=set)
    current_persona: Literal["hiring_manager", "senior_engineer", "staff_engineer"] = "hiring_manager"
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)  # [{"role": "interviewer|candidate", "content": "..."}]
    evidence_log: List[Dict[str, Any]] = Field(default_factory=list)
    question_types_used: Deque[str] = Field(default_factory=lambda: deque(maxlen=3))
```

#### Entity 4: FeedbackReport
```python
class FeedbackReport(BaseModel):
    readiness_score: int = Field(..., ge=1, le=10)
    strengths: List[Dict[str, str]]  # [{"title": "...", "evidence": "..."}]
    growth_areas: List[Dict[str, str]]  # [{"title": "...", "resource": "..."}]
    communication_tips: List[str]
    evidence_citations: List[str]
    is_partial: bool = False
    disclaimer: Optional[str] = None
```

#### Entity 5: API Request/Response Models
```python
class StartInterviewRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1, max_length=50)

class StartInterviewResponse(BaseModel):
    session_id: str
    first_question: str
    turn_count: int
    can_conclude: bool
    covered_days: List[str]
    current_persona: str

class RespondRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=5000)

class RespondResponse(BaseModel):
    next_question: str
    turn_count: int
    can_conclude: bool
    covered_days: List[str]
    current_persona: str

class FeedbackResponse(BaseModel):
    readiness_score: int
    strengths: List[Dict[str, str]]
    growth_areas: List[Dict[str, str]]
    communication_tips: List[str]
    evidence_citations: List[str]
    is_partial: bool
    disclaimer: Optional[str]
```

---

### C. DATABASE SCHEMA & STATE MANAGEMENT

**Primary Store**: In-memory Python dictionary (`Dict[str, InterviewSession]`)
- Key: session_id
- Value: InterviewSession object
- Rationale: Hackathon scope; ephemeral sessions; <50 concurrent users

**Persistence Strategy**:
- Write session state to `/tmp/sessions/{session_id}.json` asynchronously every 2 turns.
- On application startup, scan `/tmp/sessions/` and reload sessions with `updated_at` < 1 hour ago.
- Purge files older than 1 hour via background job.

**Redis Fallback (Optional P1)**:
- If Redis is available (environment variable `REDIS_URL` set), mirror session writes to Redis with 2-hour TTL.
- On read, check in-memory first, then Redis, then filesystem.

**Static Data Loading**:
- Load `curriculum.json` and `candidate_profiles.json` into memory at startup.
- Validate JSON schemas using Pydantic models. Fail fast with descriptive error if schema mismatch.
- Refresh endpoint: `POST /admin/reload-data` (no auth required for hackathon, but document as insecure).

---

### D. API ENDPOINTS (REST)

Implement the following endpoints with full CRUD-like semantics for session lifecycle:

| Method | Path | Description | Request Body | Response Body | Status Codes |
|--------|------|-------------|--------------|---------------|--------------|
| GET | /health | Health check + LLM connectivity status | — | `{ "status": "ok", "llm_ready": bool }` | 200 |
| POST | /interview/start | Initialize interview | `StartInterviewRequest` | `StartInterviewResponse` | 200, 404 (candidate not found), 422 |
| POST | /interview/{session_id}/respond | Submit answer, get next question | `RespondRequest` | `RespondResponse` | 200, 404 (session not found), 422, 429 |
| POST | /interview/{session_id}/feedback | Generate final feedback | — | `FeedbackResponse` | 200, 404, 400 (interview too short) |
| POST | /interview/{session_id}/abort | Early termination | — | `FeedbackResponse` (with is_partial=true) | 200, 404 |
| POST | /admin/reload-data | Reload static JSON data | — | `{ "status": "reloaded", "days": int, "candidates": int }` | 200 |

**Additional Requirements**:
- All endpoints must auto-generate OpenAPI 3.0 documentation via FastAPI.
- Request validation: Use Pydantic. Return 422 with detailed field errors.
- Rate limiting: 30 requests/minute per IP. Return 429 with `Retry-After` header.
- CORS: Allow all origins for hackathon demo (`allow_origins=["*"]`).

---

### E. AUTHENTICATION / AUTHORIZATION

**Hackathon Scope**: No user authentication required. Sessions are identified by `session_id` only.
- `session_id` is a UUIDv4 generated by the backend.
- No JWT, no API keys, no OAuth.
- Document clearly: "Authentication is out of scope for this release. All endpoints are public."

---

### F. REQUEST VALIDATION & ERROR HANDLING

**Validation Rules**:
- `candidate_id`: Must exist in loaded `candidate_profiles.json`. If not, return 404 with message: "Candidate profile not found."
- `answer`: 1–5000 characters. If empty or >5000, return 422.
- `session_id`: Must exist in active sessions. If not, return 404.
- `answer` semantic check: If answer is nonsensical (e.g., < 5 chars, random alphanumeric), do NOT reject at API layer—pass to AI agent and let it handle redirection.

**Error Response Schema** (consistent across all errors):
```json
{
  "error_code": "SESSION_NOT_FOUND",
  "message": "The interview session has expired or does not exist.",
  "recoverable": true,
  "timestamp": "2026-08-08T14:30:00Z"
}
```

**Global Exception Handler**:
- Catch all unhandled exceptions.
- Log full traceback server-side.
- Return 500 with generic message: "An unexpected error occurred. Please try again."
- Never leak stack traces or internal paths to client.

---

### G. PERFORMANCE BENCHMARKS

| Metric | Requirement | Implementation |
|--------|-------------|----------------|
| API Response Time (p95) | < 3 seconds per turn | Async LLM calls; streaming not required but response must be complete within 3s |
| Feedback Generation Time | < 30 seconds | LLM synthesis call with full transcript; if >25s, return partial feedback with timeout flag |
| Concurrent Sessions | 10 simultaneous | Uvicorn workers = 4; in-memory state is process-local (acceptable for demo) |
| Session State Size | < 100KB | Enforce max conversation history length; summarize after turn 6 |
| Rate Limit | 30 req/min/IP | In-memory token bucket (sufficient for hackathon) or slowapi library |

---

### H. THIRD-PARTY SERVICE INTEGRATIONS

#### OpenRouter API (LLM Provider)
- **Endpoint**: `https://openrouter.ai/api/v1/chat/completions`
- **Model**: `nvidia/llama-3.1-nemotron-70b-instruct` or equivalent high-reasoning model
- **Configuration**:
  - Temperature: 0.7 (question generation), 0.3 (feedback synthesis)
  - Max tokens: 1024 (questions), 2048 (feedback)
  - System prompts: Provided by Member 3 (AI Agent Developer)
- **Error Handling**:
  - Timeout: 5 seconds. If timeout, serve from fallback question bank.
  - 5xx from OpenRouter: Retry once after 2 seconds. If still failing, serve fallback.
  - 4xx (e.g., invalid model): Log and alert, serve fallback.
- **Fallback Question Bank**:
  - Pre-generate 50 question chains covering all curriculum days.
  - Store in `fallback_questions.json`.
  - Rotate through fallback pool based on uncovered days.

#### ChromaDB (Optional P1 — Vector Store)
- **Purpose**: RAG retrieval over synthetic project artifacts
- **Setup**: In-memory ChromaDB client (`chromadb.Client()`)
- **Collections**: `project_artifacts` (documents = synthetic project submissions, metadata = candidate_id, day_id, tools)
- **Integration**: If ChromaDB is enabled, retrieve top-3 chunks before LLM call and inject into context.
- **Fallback**: If ChromaDB fails or is disabled, skip RAG and use profile metadata only.

---

### I. BACKGROUND JOBS & SCHEDULED TASKS

Implement using FastAPI's `BackgroundTasks` or `asyncio` scheduled loops:

1. **Session Cleanup Job**
   - **Frequency**: Every 10 minutes
   - **Logic**: Iterate active sessions. Mark as "expired" if `updated_at` > 1 hour.
   - **Action**: Remove from in-memory dict. Delete `/tmp/sessions/{session_id}.json`.
   - **Endpoint**: `GET /admin/stats` returns active session count and memory usage.

2. **Health Check Refresh**
   - **Frequency**: Every 60 seconds
   - **Logic**: Ping OpenRouter API with a cheap request (e.g., `{"messages": [{"role": "user", "content": "hi"}]}`).
   - **Action**: Update global `llm_ready` flag. If unhealthy, increase fallback usage.

---

### J. DELIVERABLES

1. **OpenAPI 3.0 Specification** (`openapi.json` or auto-generated from FastAPI docs at `/docs`).
2. **Database Migration Plan**: Not a traditional migration (no SQL DB), but a "Data Loading Plan" documenting how `curriculum.json` and `candidate_profiles.json` are validated and loaded at startup.
3. **API Implementation**: Working FastAPI application with all endpoints, validation, error handling, and rate limiting.
4. **Session State Manager**: Module handling in-memory state, filesystem persistence, and optional Redis fallback.
5. **LLM Service Client**: Typed client for OpenRouter with retries, timeouts, and fallback logic.
6. **Background Job Scheduler**: Cleanup and health check tasks.
7. **Integration Tests**: pytest suite covering happy path, edge cases (E1-E6 from PRD), and fallback scenarios.

---

### K. SUCCESS CRITERIA

- [ ] All 6 endpoints return correct status codes and validated JSON schemas.
- [ ] OpenAPI documentation is accessible at `/docs` and accurately reflects all request/response models.
- [ ] 10 concurrent interviews can run without session cross-contamination or state loss.
- [ ] LLM timeout triggers fallback question within 3 seconds.
- [ ] Session survives server restart if within 1-hour window (filesystem persistence works).
- [ ] Rate limiting correctly blocks 31st request from same IP within 60 seconds.
- [ ] All 422 errors include field-level detail usable by the front-end for inline validation.
- [ ] pytest suite passes with ≥90% code coverage for endpoint handlers.

---

### L. TIMELINE ESTIMATE

- **Hours 0–2**: Scaffold FastAPI app. Define all Pydantic models. Load static JSON data. Build `/health`. Deliver OpenAPI spec to Member 1.
- **Hours 2–5**: Implement session state manager and all interview endpoints (`/start`, `/respond`, `/feedback`, `/abort`).
- **Hours 5–7**: Integrate LLM service client (using prompt schemas from Member 3). Implement fallback question bank. Add rate limiting and validation.
- **Hours 7–8**: Background jobs, filesystem persistence, integration tests, and performance tuning.

**Total**: 8 hours to MVP backend.

---

### M. DEPENDENCIES & ASSUMPTIONS

- **Receives From Member 3 (AI Agent)**: Prompt templates and expected LLM output schemas by Hour 2.
- **Receives From Member 3**: Guardrail logic (e.g., forbidden topics, question type diversity rules) by Hour 4.
- **Shares With Member 1 (Front-End)**: OpenAPI spec and base URL by Hour 2.
- **Shares With Member 3**: Data model definitions (Pydantic schemas) by Hour 1 so AI agent can align I/O formats.
- **Assumes**: OpenRouter API key is available in environment variable `OPENROUTER_API_KEY`.
- **Assumes**: Python 3.11+, FastAPI 0.100+, Pydantic 2.0+.
```

---

## PART 3 — Member 3: AI Agent Developer Prompt

```
ROLE: You are an expert AI Agent Developer and Prompt Engineer specializing in LLM orchestration, conversational AI, retrieval-augmented generation (RAG), and agent guardrails. You are building the "brain" of "The Thread Puller"—the intelligent interviewer that adapts to candidates, generates probing follow-ups, and synthesizes structured feedback.

MISSION: Design and implement the AI agent layer that drives the interview conversation. This includes prompt engineering, context management, output validation, persona orchestration, and feedback synthesis. Your outputs (prompts, schemas, guardrails) will be consumed by the Back-End Developer (Member 2) and integrated into the FastAPI service.

---

### A. SCOPE & CONTEXT

You own the AI/NLP layer:
- System prompt design for the core interviewer personality
- Dynamic follow-up generation logic
- Persona-switching prompt architecture
- Conversation context management (history, summarization, windowing)
- Structured feedback synthesis pipeline
- Output validation and guardrails (hallucination prevention, loop detection, curriculum anchoring)
- Optional RAG pipeline for project-aware questioning
- Optional confidence calibration for difficulty adaptation

The Back-End Developer (Member 2) will integrate your prompts into the LLM service client. You must align your output schemas with their Pydantic models.

---

### B. CORE AI CAPABILITY

**Primary Capability**: **Adaptive Conversational Generation with Structured Output Synthesis**

The agent must perform three distinct cognitive tasks:
1. **Interview Facilitation**: Generate natural, contextually grounded technical questions that probe the candidate's understanding of their cohort curriculum.
2. **Adaptive Probing**: Analyze the candidate's last response and generate a follow-up that challenges assumptions, requests evidence, compares alternatives, or applies concepts to new scenarios.
3. **Feedback Synthesis**: After interview conclusion, analyze the full transcript and produce a structured, evidence-based feedback report.

**Task Breakdown**:

| Task | Input | Output | Model Config |
|------|-------|--------|--------------|
| Question Generation | Candidate profile + conversation history + uncovered topics | Next question (string) + metadata (persona, question_type, target_day) | temp=0.7, max_tokens=1024 |
| Follow-Up Generation | Last answer + conversation history + recent question types | Follow-up question (string) + metadata | temp=0.7, max_tokens=1024 |
| Feedback Synthesis | Full transcript + evidence_log | Structured JSON matching FeedbackReport schema | temp=0.3, max_tokens=2048 |
| Conversation Summarization | Full history (turns 1-N) | Condensed summary (string) | temp=0.2, max_tokens=512 |

---

### C. TRAINING DATA SOURCES & LABELING

**Data Sources** (all synthetic, provided by hackathon organizers):
1. **curriculum.json**: 31 days of topics, learning objectives, and tools. Use this as the **ground truth** for valid interview content.
2. **candidate_profiles.json**: Progress data including completed missions, skipped topics, attempts, and tools used. Use this to **personalize** the interview.
3. **fallback_questions.json** (you will generate this): Pre-written question chains for graceful degradation when LLM fails.

**Labeling Requirements**:
- You must create a **Question Type Taxonomy** and label every generated question:
  - `challenge`: Push back on a claim or assumption
  - `expand`: Deepen into a specific technical detail
  - `compare`: Ask to contrast two technologies or approaches
  - `apply`: Pose a scenario or hypothetical based on cohort concepts
  - `teach`: Ask candidate to explain a concept as if teaching a junior
  - `meta`: Ask about trade-offs, decision rationale, or learning process
- Maintain a `recent_question_types` queue (last 3) and enforce diversity: no repeated type within 2 turns.

---

### D. MODEL SELECTION CRITERIA

**Primary Model**: `nvidia/llama-3.1-nemotron-70b-instruct` via OpenRouter
- **Rationale**: High reasoning capability, large context window (128K), cost-effective for hackathon, strong instruction following for structured output.

**Fallback Model**: `openai/gpt-4o-mini` via OpenRouter
- **Rationale**: If Nemotron is unavailable or slow, GPT-4o-mini provides reliable JSON mode and fast inference.

**Model Configuration**:
- **Question/Follow-Up**: temperature=0.7 (creative but grounded), top_p=0.9
- **Feedback**: temperature=0.3 (factual, consistent), top_p=0.95
- **Summarization**: temperature=0.2 (extractive focus)
- **JSON Mode**: Always use `response_format={"type": "json_object"}` when available. Otherwise, enforce JSON via system prompt + regex validation.

---

### E. EVALUATION METRICS

You must implement evaluation checks for every LLM output:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Question Relevance** | ≥85% | Semantic similarity between generated question and target curriculum day's learning objectives (embed both, cosine similarity > 0.65) |
| **Follow-Up Depth** | ≥80% | Human review: does the follow-up reference a specific claim from the previous answer? (Binary pass/fail on 20 samples) |
| **Feedback Schema Compliance** | 100% | Every feedback output must parse against Pydantic FeedbackReport model. Zero tolerance for schema violation. |
| **Evidence Anchoring** | ≥90% | Every strength/growth claim in feedback must include a transcript citation. Automated check: citation string exists in conversation history. |
| **Question Type Diversity** | ≥4 distinct types per interview | Automated tracking of `question_types_used` set size. |
| **Hallucination Rate** | <5% | Automated fact-check: verify that any technical claim in the AI's question (e.g., "ChromaDB uses HNSW") appears in curriculum.json or is marked as hypothetical. |

---

### F. INFERENCE PIPELINE

Implement a 4-stage pipeline for every LLM call:

#### Stage 1: Pre-Processing
1. **Context Assembly**: 
   - Load candidate profile (completed days, skipped days, tools used).
   - Load curriculum metadata for uncovered days (prioritize days with completion status).
   - Assemble conversation history. If >6 turns, replace turns 1-(N-4) with a running summary.
2. **Prompt Construction**:
   - Inject system prompt (persona + rules + curriculum context).
   - Inject user messages (history + current state).
   - Inject constraint: "You must output valid JSON matching the schema below."
3. **Guardrail Pre-Check**: Verify no disallowed topics are present in context.

#### Stage 2: Inference
1. Call OpenRouter API with assembled payload.
2. Set timeout: 5 seconds for questions, 25 seconds for feedback.
3. If timeout or 5xx: trigger fallback mechanism.

#### Stage 3: Post-Processing
1. **Output Parsing**: Attempt JSON parse. If fail, attempt regex extraction of JSON block. If still fail, mark as invalid.
2. **Schema Validation**: Validate parsed JSON against Pydantic model (provided by Member 2).
3. **Content Validation**:
   - Check `target_day` exists in curriculum.
   - Check `question_type` is in allowed taxonomy.
   - Check question does not repeat recent question types.
   - For feedback: check every evidence citation exists in transcript.
4. **Hallucination Check**: If question makes a factual technical claim, verify against curriculum.json or flag as hypothetical.

#### Stage 4: Fallback (if any validation fails)
1. **Retry**: Re-call LLM once with stricter prompt (e.g., "Simplify. Focus only on [specific topic].").
2. **Fallback Bank**: If retry fails, serve pre-generated question from `fallback_questions.json` aligned to an uncovered day.
3. **Logging**: Log failure reason, input context hash, and fallback used for post-hoc analysis.

---

### G. FALLBACK MECHANISMS FOR LOW-CONFIDENCE OUTPUTS

**Trigger Conditions**:
- LLM API timeout (>5s)
- JSON parse failure after 2 attempts
- Schema validation failure
- Hallucination detection (unverified technical claim)
- Question type repetition (same type as last 2 turns)
- Semantic relevance score < 0.65

**Fallback Actions**:
1. **Question Fallback**: Select from `fallback_questions.json` based on:
   - Candidate's completed but not-yet-covered days (highest priority)
   - Candidate's skipped days (probe gently: "You skipped X—can you explain the core concept?")
   - General cohort overview question (lowest priority)
2. **Feedback Fallback**: If feedback synthesis fails, return a template feedback:
   - `readiness_score`: null
   - `strengths`: ["Interview completed. Detailed analysis unavailable due to technical issue."]
   - `growth_areas`: ["Review your cohort materials for Days X, Y, Z."]
   - `is_partial`: true
   - `disclaimer`: "We encountered an issue generating detailed feedback. Please consult your instructor."

---

### H. CONTINUOUS IMPROVEMENT LOOPS

**Feedback Collection** (lightweight, hackathon-appropriate):
- After each interview, log the full transcript + generated questions + feedback to `/tmp/interview_logs/{session_id}.jsonl`.
- Fields: `session_id`, `candidate_id`, `question`, `expected_type`, `actual_type`, `relevance_score`, `validation_passed`, `fallback_used`.

**Retraining / Prompt Refinement Schedule**:
- **Hour 8 (MVP Checkpoint)**: Review 10 logged transcripts. Identify 3 most common failure modes. Adjust system prompts or fallback bank.
- **Hour 24 (Alpha Checkpoint)**: Review 20 logs. If hallucination rate >5%, add explicit "Do not invent facts" instruction to system prompt. If follow-up depth <80%, strengthen the "reference specific claims" instruction.
- **Hour 40 (Beta Checkpoint)**: Final prompt polish based on accumulated logs. Freeze prompts for demo.

**Bias Mitigation Strategy**:
- **Auditing**: Log persona distribution. Ensure no persona dominates (>50% of turns).
- **Fairness Check**: For candidates with many skipped days, ensure questions are not disproportionately focused on skipped content (penalizing) vs. completed content (strength-probing). Target 70% completed-day questions, 30% skipped-day or comparative questions.
- **Language Neutrality**: System prompt must instruct the model to avoid gendered assumptions, age bias, or cultural references in questions.

---

### I. PROMPT LIBRARY DELIVERABLES

You must produce the following artifacts as Python string constants or Jinja2 templates:

1. **System Prompt — Core Interviewer**
   - Defines the agent's mission, tone (professional but encouraging), rules (no answering for the candidate, no leading questions), and output format.

2. **System Prompt — Persona Variants**
   - `hiring_manager`: Focus on business impact, communication clarity, team fit.
   - `senior_engineer`: Focus on technical depth, edge cases, architecture rigor.
   - `staff_engineer`: Focus on system design, scalability, cross-system integration.
   - Each variant must include a "bridge phrase" generator instruction for smooth transitions.

3. **User Prompt — Question Generation**
   - Template accepting: candidate_profile, uncovered_days, conversation_history, recent_question_types.
   - Output schema: `{ "question": "...", "target_day": "day_14", "question_type": "challenge", "persona": "senior_engineer" }`

4. **User Prompt — Follow-Up Generation**
   - Template accepting: last_answer, conversation_history, recent_question_types, evidence_log.
   - Output schema: `{ "question": "...", "question_type": "expand", "references_claim": "..." }`

5. **User Prompt — Feedback Synthesis**
   - Template accepting: full_transcript, evidence_log.
   - Output schema matching `FeedbackReport` Pydantic model exactly.
   - Must include instruction: "Every claim must cite a specific moment from the transcript. If you cannot cite evidence, do not include the claim."

6. **User Prompt — Conversation Summarization**
   - Template accepting: full_history.
   - Output: `{ "summary": "Candidate demonstrated strong understanding of RAG but struggled with vector DB indexing trade-offs." }`

---

### J. AGENT INPUT/OUTPUT SCHEMA

**Input Schema** (what the backend sends to your agent module):
```json
{
  "task": "generate_question | generate_followup | synthesize_feedback | summarize",
  "candidate_profile": { "candidate_id": "...", "completed_missions": [...], "skipped_topics": [...], "tools_used": [...] },
  "conversation_history": [{ "role": "interviewer|candidate", "content": "...", "turn": 1 }],
  "session_metadata": { "turn_count": 5, "covered_days": ["day_12"], "current_persona": "senior_engineer", "question_types_used": ["challenge", "expand"] },
  "evidence_log": [{ "topic": "RAG", "signal": "strong", "evidence": "..." }]
}
```

**Output Schema** (what your agent module returns to the backend):
```json
{
  "task": "generate_question",
  "output": {
    "question": "Walk me through why you chose ChromaDB over Pinecone for your RAG project.",
    "target_day": "day_12",
    "question_type": "challenge",
    "persona": "senior_engineer",
    "confidence": 0.92,
    "validation_passed": true
  },
  "fallback_used": false,
  "latency_ms": 1200
}
```

---

### K. PROOF-OF-CONCEPT PLAN

**PoC 1: Static Prompt Test** (Hour 0–2)
- Hardcode one candidate profile and one curriculum day.
- Run 5-turn conversation manually via Python script.
- Evaluate: Are follow-ups referencing previous answers? Are questions curriculum-aligned?

**PoC 2: Schema Compliance Test** (Hour 2–4)
- Generate 20 feedback reports from synthetic transcripts.
- Validate 100% schema compliance and ≥90% evidence anchoring.

**PoC 3: Persona Switch Test** (Hour 4–6)
- Run a 9-turn interview with forced persona switches at turns 3 and 6.
- Evaluate: Are bridge phrases natural? Does question style shift appropriately?

**PoC 4: RAG Integration Test** (Hour 6–8, Optional)
- Index 3 synthetic project documents in ChromaDB.
- Verify retrieved chunks appear in ≥20% of generated questions.

---

### L. TESTING STRATEGY

**Automated Tests**:
1. **Unit Tests**: Test each prompt template with 10 diverse inputs. Assert output contains required fields.
2. **Integration Tests**: Test full pipeline (pre-processing → inference → post-processing) with mocked LLM responses.
3. **Regression Tests**: After every prompt change, re-run 5 golden transcript scenarios and diff outputs.

**Edge Case Tests** (must pass before backend integration):
- **Empty Answer**: Candidate submits "idk". Agent redirects with simpler question.
- **Off-Topic Answer**: Candidate talks about Kubernetes when asked about RAG. Agent gently redirects.
- **Confident Bluff**: Candidate gives detailed but incorrect answer. Agent asks for evidence or specific example.
- **Repeated Answer**: Candidate copies previous answer. Agent switches question type to `compare`.
- **Skipped Topic Probe**: Candidate skipped Day 14. Agent asks a high-level conceptual question, not a "gotcha."
- **Context Window Stress**: 12-turn interview. Verify summarization maintains coherence.

**Bias Tests**:
- Run identical interview logic against 5 synthetic candidate profiles with varying completion rates.
- Assert: readiness_score distribution is not statistically correlated with number of skipped days alone (Pearson r < 0.5).

---

### M. DELIVERABLES

1. **Prompt Library**: Python module containing all system prompts, user prompt templates, and persona variants.
2. **I/O Schema Definitions**: Pydantic models for agent input/output (align with Member 2's models).
3. **Inference Pipeline Code**: Complete Python module with pre-processing, inference, post-processing, and fallback logic.
4. **Fallback Question Bank**: `fallback_questions.json` with 50 pre-generated questions mapped to curriculum days.
5. **Evaluation Suite**: Scripts to measure relevance, depth, schema compliance, and hallucination rate.
6. **Testing Harness**: pytest suite with edge case and bias tests.
7. **Integration Guide**: Markdown document explaining how Member 2 should call your agent module from FastAPI endpoints.

---

### N. SUCCESS CRITERIA

- [ ] All prompt templates generate outputs that pass schema validation ≥95% of the time (allowing for LLM stochasticity).
- [ ] Follow-up questions reference specific claims from the previous answer in ≥80% of cases (measured on 20 sample transcripts).
- [ ] Feedback reports contain ≥3 transcript citations on average.
- [ ] Hallucination rate (unverified technical claims) <5%.
- [ ] Persona switches include natural bridge phrases in ≥90% of cases.
- [ ] Fallback question bank covers all 31 curriculum days with at least 1 question per day.
- [ ] Edge case tests (empty answer, off-topic, bluff, repeat, skipped topic, context stress) all produce acceptable agent behavior.
- [ ] Bias test: no significant correlation between skipped-day count and readiness_score.

---

### O. TIMELINE ESTIMATE

- **Hours 0–2**: Design core system prompt and question generation template. Run PoC 1 (static prompt test).
- **Hours 2–4**: Build follow-up generation template and feedback synthesis template. Run PoC 2 (schema compliance).
- **Hours 4–6**: Implement persona variants, bridge phrases, and conversation summarization. Run PoC 3 (persona switch).
- **Hours 6–8**: Build inference pipeline with validation, fallback logic, and evaluation suite. Generate fallback question bank. Deliver integration guide to Member 2.

**Total**: 8 hours to MVP agent layer.

---

### P. DEPENDENCIES & ASSUMPTIONS

- **Receives From Member 2 (Back-End)**: Pydantic data model definitions by Hour 1 to align I/O schemas.
- **Receives From Member 2**: Access to `curriculum.json` and `candidate_profiles.json` by Hour 0.
- **Shares With Member 2**: Prompt templates and expected output schemas by Hour 2.
- **Shares With Member 2**: Guardrail logic and fallback trigger conditions by Hour 4.
- **Assumes**: OpenRouter API key with access to Nemotron 3 Ultra and GPT-4o-mini.
- **Assumes**: Python 3.11+, `openai` client library (compatible with OpenRouter), `pydantic` 2.0+, `chromadb` (optional).
```

---

## COORDINATION MATRIX: Cross-Stream Dependencies & Integration Gates

| Gate | Time | From | To | Deliverable | Purpose |
|------|------|------|-----|-------------|---------|
| **G1** | Hour 0 | Member 2 | Member 3 | Pydantic model definitions (`CandidateProfile`, `CurriculumDay`, `InterviewSession`, `FeedbackReport`) | AI Agent aligns I/O schemas with backend data layer |
| **G2** | Hour 0 | Member 2 | Member 3 | Static data files (`curriculum.json`, `candidate_profiles.json`) | AI Agent has ground truth for prompts and validation |
| **G3** | Hour 1 | Member 3 | Member 2 | Draft system prompt + question output schema | Backend knows expected LLM payload structure |
| **G4** | Hour 2 | Member 2 | Member 1 | **OpenAPI 3.0 Spec** (auto-generated from FastAPI) | Front-End can generate typed API client and build components |
| **G5** | Hour 2 | Member 3 | Member 2 | Finalized prompt templates (question, follow-up, feedback) | Backend integrates prompts into LLM service client |
| **G6** | Hour 4 | Member 3 | Member 2 | Guardrail logic + fallback trigger conditions | Backend implements validation layer and fallback routing |
| **G7** | Hour 6 | Member 1 | Member 2 | UI component contract (any API needs discovered during build) | Backend adjusts endpoints if front-end needs minor schema tweaks |
| **G8** | Hour 8 | All | All | **MVP Integration Test**: Run 3 end-to-end interviews via UI | Validate full stack: FE → BE → AI → BE → FE |
| **G9** | Hour 24 | Member 3 | Member 2 | RAG pipeline module (if implemented) | Backend integrates vector retrieval into `/respond` endpoint |
| **G10** | Hour 40 | All | All | **Final Integration & Load Test**: 10 concurrent interviews | Validate performance benchmarks and cross-stream stability |

---

### Dependency Graph

```
Hour 0        Hour 2        Hour 4        Hour 6        Hour 8
  │             │             │             │             │
  ▼             ▼             ▼             ▼             ▼
┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐
│ M2  │─────→│ M1  │      │     │      │     │      │     │
│models│      │OpenAPI│    │     │      │     │      │     │
└─────┘      └─────┘      └─────┘      └─────┘      └─────┘
  │             ▲             ▲             ▲             ▲
  │             │             │             │             │
  ▼             │             │             │             │
┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐
│ M3  │─────→│ M2  │─────→│ M2  │─────→│ M1  │─────→│ ALL │
│prompts│     │integrate│  │guardrails│  │tweaks│     │MVP  │
└─────┘      └─────┘      └─────┘      └─────┘      └─────┘

Legend:
M1 = Member 1 (Front-End)
M2 = Member 2 (Back-End)
M3 = Member 3 (AI Agent)
──→ = Deliverable / Dependency
```

---

### Communication Protocol

- **Daily Standups** (5 min each, Hours 0, 8, 24, 40): Each member reports blockers and deliverable status.
- **Shared Channel** (Discord/Slack): `#integration-gates` — post deliverables with gate tag (e.g., `[G4] OpenAPI spec v1.0`).
- **Versioning**: All shared artifacts use semantic versioning in filename (e.g., `openapi_v1.0.json`, `prompts_v0.5.py`).
- **Conflict Resolution**: If API schema needs change after Hour 4, the requesting member must provide a migration snippet and both other members must ACK before implementation.

---

## Conclusion

This 3-part prompt chain decomposes the PRD into **atomic workstreams** with **clear handoffs**. Each member can execute their prompt independently while respecting sequential dependencies at defined integration gates. The coordination matrix ensures that the Front-End's typed API client, the Back-End's validated endpoints, and the AI Agent's structured outputs all converge into a cohesive, demo-ready product within 48 hours.

**Critical Success Factor**: Hit Gate G8 (Hour 8 MVP Integration) on time. If the full stack can conduct one 8-turn interview end-to-end by Hour 8, the remaining 40 hours are available for polish, differentiation, and stability.
