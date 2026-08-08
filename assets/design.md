# Design Document: The Thread Puller
## AI Interview Agent — AI Cohort Hackathon

**Version**: 1.0  
**Date**: 2026-08-08  
**Status**: Final Design  
**Authors**: Product & Engineering Team  

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [System Architecture](#2-system-architecture)
3. [Data Models](#3-data-models)
4. [API Design](#4-api-design)
5. [AI Agent Architecture](#5-ai-agent-architecture)
6. [Frontend Architecture](#6-frontend-architecture)
7. [State & Session Management](#7-state--session-management)
8. [Error Handling & Resilience](#8-error-handling--resilience)
9. [Performance & Scaling](#9-performance--scaling)
10. [Security & Privacy](#10-security--privacy)
11. [Deployment & Operations](#11-deployment--operations)
12. [Integration & Coordination](#12-integration--coordination)

---

## 1. Design Philosophy

### Core Principle
> **"Build the interviewer, not the interview."**

The system is designed as a **conversational intelligence layer** that sits between a candidate's learning history and a realistic technical interview experience. It is not a quiz engine. It is not a chatbot. It is an **adaptive Socratic agent** that treats every candidate response as a signal to probe deeper, pivot topics, or shift persona.

### Design Tenets

| # | Tenet | Implication |
|---|-------|-------------|
| 1 | **Conversation over Script** | No fixed question list. Every turn is generated dynamically based on the previous answer. |
| 2 | **Context is King** | The agent must know what the candidate completed, skipped, and struggled with. This context persists across all 8+ turns. |
| 3 | **Evidence Anchored** | Every piece of feedback must cite a specific moment from the transcript. No generic platitudes. |
| 4 | **Graceful Degradation** | If the LLM fails, hallucinates, or times out, the system must continue with pre-generated fallback questions without the candidate noticing. |
| 5 | **Transparency over Trickery** | The candidate always knows their progress, the interviewer's current persona, and when feedback is partial. |

### Non-Goals (Explicitly Out of Scope)
- Voice interaction
- User authentication or persistent accounts
- Cross-session memory (each interview is ephemeral)
- Mobile native application
- Real-time emotion detection via video
- Integration with external LMS or HR systems

---

## 2. System Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    React SPA (Member 1)                              │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │    │
│  │  │ LandingView │  │ InterviewView │  │    FeedbackView          │  │    │
│  │  └─────────────┘  └──────────────┘  └──────────────────────────┘  │    │
│  │         │                │                      │                  │    │
│  │         └────────────────┴──────────────────────┘                  │    │
│  │                         │                                         │    │
│  │              ┌──────────┴──────────┐                              │    │
│  │              │   Zustand Store     │                              │    │
│  │              │  (State + Actions)  │                              │    │
│  │              └──────────┬──────────┘                              │    │
│  │                         │                                         │    │
│  │              ┌──────────┴──────────┐                              │    │
│  │              │   Typed API Client  │                              │    │
│  │              │  (OpenAPI-generated)│                              │    │
│  │              └──────────┬──────────┘                              │    │
│  └─────────────────────────┼─────────────────────────────────────────┘    │
│                            │ HTTP/JSON (REST)                             │
└────────────────────────────┼──────────────────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────────────────┐
│                         API GATEWAY                                        │
│  ┌───────────────────────┴─────────────────────────────────────────────┐   │
│  │                    FastAPI Service (Member 2)                         │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │  /interview │  │  /interview  │  │    /interview/{id}/      │  │   │
│  │  │   /start    │  │  /{id}/respond│  │      feedback            │  │   │
│  │  └─────────────┘  └──────────────┘  └──────────────────────────┘  │   │
│  │         │                │                      │                  │   │
│  │         └────────────────┴──────────────────────┘                  │   │
│  │                         │                                         │   │
│  │              ┌──────────┴──────────┐                              │   │
│  │              │   Session Manager   │                              │   │
│  │              │  (In-Memory + FS +  │                              │   │
│  │              │   Optional Redis)   │                              │   │
│  │              └──────────┬──────────┘                              │   │
│  │                         │                                         │   │
│  │              ┌──────────┴──────────┐                              │   │
│  │              │   LLM Service Client│                              │   │
│  │              │  (OpenRouter API)   │                              │   │
│  │              └──────────┬──────────┘                              │   │
│  └─────────────────────────┼─────────────────────────────────────────┘   │
└────────────────────────────┼──────────────────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────────────────┐
│                         AI AGENT LAYER                                     │
│  ┌───────────────────────┴─────────────────────────────────────────────┐   │
│  │              AI Agent Module (Member 3)                              │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │   Prompt    │  │   Inference  │  │    Validation &          │  │   │
│  │  │   Library   │  │   Pipeline   │  │    Fallback Engine       │  │   │
│  │  └─────────────┘  └──────────────┘  └──────────────────────────┘  │   │
│  │         │                │                      │                  │   │
│  │         └────────────────┴──────────────────────┘                  │   │
│  │                         │                                         │   │
│  │              ┌──────────┴──────────┐                              │   │
│  │              │   Fallback Q Bank   │                              │   │
│  │              │  (50 pre-gen Qs)    │                              │   │
│  │              └─────────────────────┘                              │   │
│  └───────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼──────────────────────────────────────────────┐
│                         DATA LAYER                                         │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  │
│  │  curriculum.json   │  │ candidate_profiles │  │  /tmp/sessions/    │  │
│  │  (31-day syllabus) │  │     .json          │  │  (session state)   │  │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘  │
│  ┌────────────────────┐  ┌────────────────────┐                          │
│  │ fallback_questions │  │  ChromaDB (opt.)   │                          │
│  │     .json          │  │  (vector store)    │                          │
│  └────────────────────┘  └────────────────────┘                          │
└────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React 18 + TypeScript + Tailwind CSS + Zustand | Type-safe, component-rich, minimal bundle, simple state management |
| **Backend** | FastAPI (Python 3.11+) + Pydantic v2 + Uvicorn | Async-native, auto-generated OpenAPI docs, robust validation |
| **AI/LLM** | OpenRouter API (Nemotron 3 Ultra / GPT-4o-mini fallback) | High reasoning, large context window, cost-efficient |
| **State Store** | In-memory dict + filesystem JSON + optional Redis | Hackathon-appropriate; no DB ops overhead |
| **Vector Store** | ChromaDB (in-memory, optional) | Lightweight RAG for project artifacts |
| **Deployment** | Uvicorn + Docker (optional) + ngrok (for Colab demos) | Portable, easy to expose for hackathon judging |

---

## 3. Data Models

### 3.1 Static Data (Loaded at Startup)

#### CurriculumDay
```json
{
  "day_id": "day_12",
  "title": "Retrieval-Augmented Generation (RAG)",
  "topics": ["Embedding Models", "Vector Databases", "Chunking Strategies", "Retrieval Pipelines"],
  "learning_objectives": [
    "LO-12-1: Explain the difference between dense and sparse retrieval",
    "LO-12-2: Implement a basic RAG pipeline using LangChain",
    "LO-12-3: Evaluate retrieval quality using MRR and nDCG"
  ],
  "tools": ["ChromaDB", "Pinecone", "LangChain", "OpenAI Embeddings"],
  "prerequisites": ["day_10", "day_11"]
}
```

#### CandidateProfile
```json
{
  "candidate_id": "alex_001",
  "completed_missions": ["mission_12_1", "mission_12_2", "mission_15_1"],
  "skipped_topics": ["day_14", "day_22"],
  "attempts": {
    "mission_12_1": 1,
    "mission_12_2": 3,
    "mission_15_1": 1
  },
  "tools_used": ["ChromaDB", "LangChain", "Streamlit"],
  "learning_signals": {
    "day_12_confidence": 0.85,
    "day_15_confidence": 0.60,
    "avg_time_per_mission_minutes": 45
  }
}
```

### 3.2 Runtime Data (Session State)

#### InterviewSession (Internal Runtime Model)
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
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    evidence_log: List[Dict[str, Any]] = Field(default_factory=list)
    question_types_used: Deque[str] = Field(default_factory=lambda: deque(maxlen=3))
```

#### ConversationHistory Entry
```json
{
  "role": "interviewer",
  "content": "Walk me through why you chose ChromaDB over Pinecone for your RAG project.",
  "timestamp": "2026-08-08T14:30:00Z",
  "metadata": {
    "turn": 3,
    "persona": "senior_engineer",
    "question_type": "challenge",
    "target_day": "day_12",
    "fallback_used": false
  }
}
```

#### EvidenceLog Entry
```json
{
  "turn": 3,
  "topic": "RAG",
  "signal": "strong",
  "evidence": "Candidate correctly identified HNSW indexing trade-offs and memory constraints.",
  "question_type": "challenge",
  "day_id": "day_12"
}
```

### 3.3 API Data Transfer Objects

#### StartInterviewRequest / Response
```json
// POST /interview/start
// Request
{ "candidate_id": "alex_001" }

// Response
{
  "session_id": "sess_abc123-def456",
  "first_question": "I see you completed the RAG module on Day 12. Walk me through how you designed your retrieval pipeline.",
  "turn_count": 1,
  "can_conclude": false,
  "covered_days": ["day_12"],
  "current_persona": "hiring_manager"
}
```

#### RespondRequest / Response
```json
// POST /interview/{session_id}/respond
// Request
{ "answer": "I used ChromaDB because it was easy to set up locally..." }

// Response
{
  "next_question": "That's a solid practical reason. But if you were deploying to production with 10M documents, would you still choose ChromaDB?",
  "turn_count": 2,
  "can_conclude": false,
  "covered_days": ["day_12"],
  "current_persona": "senior_engineer"
}
```

#### FeedbackResponse
```json
// POST /interview/{session_id}/feedback
// Response
{
  "readiness_score": 7,
  "strengths": [
    {
      "title": "Strong practical reasoning for tool selection",
      "evidence": "Turn 2: 'I used ChromaDB because it was easy to set up locally and integrated well with LangChain.'"
    },
    {
      "title": "Awareness of production trade-offs",
      "evidence": "Turn 3: Candidate acknowledged HNSW memory constraints and mentioned Pinecone as a scale alternative."
    }
  ],
  "growth_areas": [
    {
      "title": "Quantitative evaluation of retrieval quality",
      "resource": "Review Day 12 Learning Objective LO-12-3: Evaluate retrieval quality using MRR and nDCG"
    }
  ],
  "communication_tips": [
    "Your answers are technically sound, but try leading with the 'why' before the 'how' to show strategic thinking upfront."
  ],
  "evidence_citations": [
    "Turn 2: 'I used ChromaDB because it was easy to set up locally...'",
    "Turn 3: 'HNSW uses a lot of memory, so for 10M docs I'd probably look at Pinecone...'"
  ],
  "is_partial": false,
  "disclaimer": null
}
```

#### AbortResponse
```json
// POST /interview/{session_id}/abort
// Response (partial feedback)
{
  "readiness_score": null,
  "strengths": [],
  "growth_areas": [
    { "title": "Interview incomplete", "resource": "Complete a full 8-question interview for comprehensive feedback." }
  ],
  "communication_tips": [],
  "evidence_citations": [],
  "is_partial": true,
  "disclaimer": "This feedback is based on an incomplete interview (3 of 8+ questions). Results may not reflect full readiness."
}
```

---

## 4. API Design

### 4.1 Endpoint Specification

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Health check + LLM connectivity status |
| POST | `/interview/start` | None | Initialize interview session |
| POST | `/interview/{session_id}/respond` | None | Submit candidate answer, receive next question |
| POST | `/interview/{session_id}/feedback` | None | Generate structured feedback report |
| POST | `/interview/{session_id}/abort` | None | Early termination with partial feedback |
| POST | `/admin/reload-data` | None | Reload static JSON data (hackathon convenience) |
| GET | `/admin/stats` | None | Active session count + memory usage |

### 4.2 Error Response Schema (Universal)

All errors return HTTP 4xx/5xx with this body:
```json
{
  "error_code": "SESSION_NOT_FOUND",
  "message": "The interview session has expired or does not exist.",
  "recoverable": true,
  "timestamp": "2026-08-08T14:30:00Z",
  "details": {}  // optional field-level errors for 422
}
```

### 4.3 Status Code Mapping

| Scenario | Status | Error Code |
|----------|--------|------------|
| Success | 200 | — |
| Candidate ID not found | 404 | `CANDIDATE_NOT_FOUND` |
| Session ID not found | 404 | `SESSION_NOT_FOUND` |
| Validation failure (empty answer, too long) | 422 | `VALIDATION_ERROR` |
| Interview too short for feedback (< 8 turns) | 400 | `INTERVIEW_TOO_SHORT` |
| Rate limit exceeded (30 req/min) | 429 | `RATE_LIMIT_EXCEEDED` |
| LLM service unavailable (fallback triggered) | 200 | — (silent fallback) |
| Unhandled server error | 500 | `INTERNAL_ERROR` |

### 4.4 Rate Limiting

- **Algorithm**: Token bucket, in-memory
- **Limit**: 30 requests per minute per IP address
- **Headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
- **Scope**: All `/interview/*` endpoints + `/admin/*`

---

## 5. AI Agent Architecture

### 5.1 Agent Personality Architecture

The agent operates as a **single unified interviewer** that can "wear different hats." The base personality is a senior engineer who wants the candidate to succeed but has a duty to stress-test their knowledge.

#### Base System Prompt Principles
1. **Advocacy Framing**: Every challenge is framed as help. *"I'm going to push back on this because I want you to build the strongest case for your design."*
2. **Curriculum Grounding**: All questions must map to a `day_id` and `learning_objective` from `curriculum.json`.
3. **No Leading**: Never suggest the answer within the question.
4. **Evidence Demand**: Every follow-up must reference a specific claim, assumption, or technical term from the previous answer.

#### Persona Variants

| Persona | Voice | Focus | Transition Bridge Example |
|---------|-------|-------|---------------------------|
| **Hiring Manager** | Business-oriented, outcome-focused | Impact, trade-offs, communication clarity | *"That's a solid engineering perspective. Let me put on my hiring manager hat—how would you explain this ROI to a non-technical stakeholder?"* |
| **Senior Engineer** | Technical, detail-oriented | Edge cases, implementation rigor, architecture | *"Good product thinking. Now let's stress-test the engineering—what happens when query volume 10x's?"* |
| **Staff Engineer** | Systems-thinking, strategic | Scalability, cross-system integration, long-term maintainability | *"That works at the service level. But as a staff engineer, I'd ask: how does this choice affect the broader data platform?"* |

### 5.2 Question Type Taxonomy

Every generated question is tagged with exactly one type. The agent maintains a rolling queue of the last 3 types and enforces diversity.

| Type | Purpose | Example |
|------|---------|---------|
| `challenge` | Push back on a claim or assumption | *"You said ChromaDB is 'easy'—but easy for whom? The ops team or the developer?"* |
| `expand` | Deepen into a specific technical detail | *"You mentioned HNSW. Can you explain how HNSW handles deletions compared to insertions?"* |
| `compare` | Contrast two technologies or approaches | *"You chose ChromaDB. Under what conditions would Pinecone be the better call?"* |
| `apply` | Pose a scenario or hypothetical | *"Your RAG pipeline is returning irrelevant chunks. Walk me through your debugging strategy."* |
| `teach` | Ask candidate to explain as if teaching | *"Imagine I'm a junior engineer who's never heard of embeddings. Explain why we need them in 2 sentences."* |
| `meta` | Ask about trade-offs, rationale, or learning process | *"Looking back at your Day 12 project, what's the one decision you'd revisit?"* |

### 5.3 Context Window Management

The LLM has a finite context window. To support 8+ turn interviews without truncation:

```
Turns 1-6:  Full conversation history included verbatim
Turn 7+:     Summarize turns 1-(N-4) into a condensed paragraph
             Include turns (N-3) to N verbatim
             Total context: ~4 full turns + 1 summary paragraph
```

**Summarization Prompt**:
> "Summarize the following interview turns into 3-4 sentences. Capture: (1) topics covered, (2) candidate's demonstrated strengths, (3) areas where they struggled or were vague."

### 5.4 Inference Pipeline (4-Stage)

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  1. PRE-PROCESS │───→│  2. INFERENCE   │───→│ 3. POST-PROCESS │───→│ 4. FALLBACK     │
│                 │    │                 │    │                  │    │ (if needed)     │
│ • Load profile  │    │ • Call OpenRouter│   │ • JSON parse     │    │ • Retry once    │
│ • Assemble ctx  │    │ • Timeout: 5s    │   │ • Schema validate│    │ • Fallback bank │
│ • Build prompt  │    │ • Retry once     │   │ • Content check  │    │ • Log failure   │
│ • Guardrail pre │    │   on 5xx         │   │ • Hallucination  │    │                 │
│                 │    │                 │    │   detection      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 5.5 Feedback Synthesis Pipeline

```
Input: Full transcript + evidence_log
│
├─→ Step 1: Extract strength signals from evidence_log (signal == "strong")
├─→ Step 2: Extract growth signals from evidence_log (signal == "weak" or "vague")
├─→ Step 3: Identify communication patterns (hedge words, clarity, structure)
├─→ Step 4: Generate readiness_score (1-10) based on signal distribution
├─→ Step 5: Draft feedback sections with mandatory evidence citations
├─→ Step 6: Validate every claim has a transcript citation
└─→ Output: Structured FeedbackReport JSON
```

**Mandatory Prompt Constraint for Feedback**:
> "Every claim in strengths, growth_areas, and communication_tips MUST cite a specific moment from the transcript. If you cannot find evidence, do not include the claim."

### 5.6 Hallucination Guardrails

| Check | Method | Action on Failure |
|-------|--------|-------------------|
| Curriculum alignment | Embed question + learning objectives; cosine similarity > 0.65 | Reject, retry with stricter topic constraint |
| Fact verification | If question states a technical fact (e.g., "ChromaDB uses HNSW"), verify against curriculum.json | Flag as hypothetical or rephrase as question |
| Question type diversity | `question_type` not in last 3 types used | Reject, regenerate with different type |
| Persona consistency | Question tone must match current persona's voice guidelines | Reject, apply persona style guide |

---

## 6. Frontend Architecture

### 6.1 Component Hierarchy

```
App
├── Layout
│   ├── Header (logo + health status dot from GET /health)
│   └── GlobalErrorBoundary
│       └── ErrorFallback (friendly message + reload CTA)
│
├── Router (conditional rendering based on activeScreen)
│   ├── LandingView (activeScreen === 'landing')
│   │   ├── CandidateIdForm
│   │   │   ├── TextInput (validated, max 50 chars)
│   │   │   └── SubmitButton (loading state during API call)
│   │   └── InfoPanel (context about the interview)
│   │
│   ├── InterviewView (activeScreen === 'chat')
│   │   ├── InterviewHeader
│   │   │   ├── ProgressBar (turn_count / 8+)
│   │   │   ├── TopicChips (covered_days mapped to curriculum titles)
│   │   │   └── PersonaBadge (avatar + name + tooltip)
│   │   ├── ChatContainer (scrollable, auto-scroll to bottom)
│   │   │   ├── ChatMessage (interviewer: left-aligned, styled bubble)
│   │   │   ├── ChatMessage (candidate: right-aligned, styled bubble)
│   │   │   ├── TypingIndicator (animated dots, shown during API call)
│   │   │   └── PersonaTransition (fade animation wrapper)
│   │   ├── AnswerComposer
│   │   │   ├── TextArea (auto-resize, char counter, max 5000)
│   │   │   ├── AutoSaveIndicator ("Draft saved" micro-copy)
│   │   │   ├── ActionBar
│   │   │   │   ├── SubmitAnswerButton (primary, disabled if empty)
│   │   │   │   ├── EndInterviewButton (secondary, disabled until can_conclude)
│   │   │   │   └── AbortInterviewButton (tertiary, triggers ConfirmDialog)
│   │   │   └── ConfirmDialog (abort confirmation)
│   │   └── InterviewSidebar (md+ breakpoint only)
│   │       └── TopicCoverageList (detailed day-by-day status)
│   │
│   ├── FeedbackView (activeScreen === 'feedback')
│   │   ├── ScoreCard (animated number, color-coded)
│   │   ├── FeedbackSection
│   │   │   ├── StrengthCard[] (green theme, blockquote evidence)
│   │   │   ├── GrowthCard[] (amber theme, resource link)
│   │   │   └── TipItem[] (bulleted communication tips)
│   │   ├── EvidenceLog (collapsible, transcript citations)
│   │   └── ActionFooter
│   │       └── StartNewInterviewButton (clears state, returns to Landing)
│   │
│   └── ErrorView (activeScreen === 'error')
│       ├── ErrorIcon
│       ├── ErrorMessage (human-friendly, never raw JSON)
│       └── RetryButton (if recoverable)
│
└── Shared
    ├── Button (variants: primary, secondary, danger, ghost, loading)
    ├── Skeleton (loading placeholder for chat bubbles)
    ├── LoadingOverlay (full-screen blocker for feedback generation)
    ├── Tooltip (accessible, keyboard-triggerable)
    └── Toast (for transient notifications: "Draft saved", "Session restored")
```

### 6.2 State Management (Zustand)

```typescript
// store.ts
interface AppState {
  // Navigation
  activeScreen: 'landing' | 'chat' | 'feedback' | 'error';

  // Global error (null when healthy)
  globalError: {
    message: string;
    code: string;
    recoverable: boolean;
  } | null;

  // Session
  session: {
    session_id: string | null;
    candidate_id: string | null;
    status: 'idle' | 'active' | 'completing' | 'completed' | 'aborted';
    turn_count: number;
    can_conclude: boolean;
    covered_days: string[];
    current_persona: 'hiring_manager' | 'senior_engineer' | 'staff_engineer';
  };

  // Chat
  messages: Array<{
    id: string;           // uuid
    role: 'interviewer' | 'candidate';
    content: string;
    timestamp: string;    // ISO 8601
    persona?: string;     // only for interviewer
    question_type?: string; // only for interviewer (debug/transparent mode)
  }>;

  // UI
  isLoading: boolean;     // global loading (e.g., starting interview)
  isTyping: boolean;      // interviewer thinking state
  draftAnswer: string;    // textarea content

  // Feedback
  feedback: {
    readiness_score: number | null;
    strengths: Array<{ title: string; evidence: string }>;
    growth_areas: Array<{ title: string; resource: string }>;
    communication_tips: string[];
    evidence_citations: string[];
    is_partial: boolean;
    disclaimer: string | null;
  } | null;
}

interface AppActions {
  // Lifecycle
  startInterview: (candidate_id: string) => Promise<void>;
  submitAnswer: (answer: string) => Promise<void>;
  endInterview: () => Promise<void>;
  abortInterview: () => Promise<void>;

  // UI
  setDraftAnswer: (text: string) => void;
  clearError: () => void;
  resetSession: () => void;

  // Recovery
  restoreSession: () => Promise<boolean>;
}
```

### 6.3 Persistence Strategy

```
localStorage Keys:
├── threadpuller_session_id      → session_id (string)
├── threadpuller_messages        → messages[] (JSON)
├── threadpuller_draft           → draftAnswer (string)
└── threadpuller_timestamp       → last update ISO string

Rules:
• Write after every successful API response
• Clear only after feedback is fully rendered OR user clicks "Start New Interview"
• On app load: check for session_id → validate with backend → restore if valid
• If session expired (404 from backend): clear localStorage, show "Session expired" toast
```

### 6.4 Accessibility Requirements (WCAG 2.1 AA)

| Requirement | Implementation |
|-------------|----------------|
| **Keyboard Navigation** | Full tab order. Enter = newline in textarea. Shift+Enter = submit. |
| **Screen Reader Announcements** | `aria-live="polite"` region for new questions. `aria-live="assertive"` for persona switches and errors. |
| **Focus Management** | After question loads, focus moves to textarea (configurable). Modal dialogs trap focus. |
| **Color Contrast** | All text ≥ 4.5:1 ratio. Feedback colors use patterns (stripes/icons) in addition to color. |
| **Motion** | Respect `prefers-reduced-motion`. Disable persona transition animations if set. |
| **Touch Targets** | All buttons ≥ 44×44px. Textarea pinch-zoom friendly. |

---

## 7. State & Session Management

### 7.1 Session Lifecycle

```
[CREATED] ──startInterview()──→ [ACTIVE]
                                    │
                                    ├──respond()──→ [ACTIVE] (loop until turn_count ≥ 8)
                                    │
                                    ├──feedback()──→ [COMPLETED]
                                    │
                                    └──abort()──→ [ABORTED]

[EXPIRED] ←──1 hour idle─── [COMPLETED/ABORTED]
```

### 7.2 State Transition Rules

| From State | Allowed Actions | Guards |
|------------|-----------------|--------|
| `CREATED` | `respond` | Must have first question loaded |
| `ACTIVE` | `respond`, `feedback`, `abort` | `feedback` requires `turn_count >= 8` AND `covered_days.size >= 4` |
| `COMPLETED` | None (terminal) | Session purged after 1 hour |
| `ABORTED` | None (terminal) | Partial feedback generated; session purged after 1 hour |

### 7.3 Backend Session Store

```python
# In-memory active sessions
active_sessions: Dict[str, InterviewSession] = {}

# Filesystem persistence (async write every 2 turns)
SESSIONS_DIR = Path("/tmp/sessions")
TTL_HOURS = 1

# Optional Redis fallback
redis_client: Optional[redis.Redis] = None  # initialized if REDIS_URL env var present
```

### 7.4 Context Window Budget

| Turn Range | History Strategy | Approximate Tokens |
|------------|----------------|-------------------|
| 1-4 | Full history verbatim | ~2,000-4,000 |
| 5-6 | Full history + evidence_log | ~4,000-6,000 |
| 7+ | Summary(1 to N-4) + Full(N-3 to N) | ~4,000-6,000 (capped) |
| Feedback | Full history (no summarization needed, single call) | ~6,000-10,000 |

---

## 8. Error Handling & Resilience

### 8.1 Failure Modes & Mitigations

| Failure | Detection | Client Impact | Server Action | Fallback |
|---------|-----------|---------------|---------------|----------|
| LLM timeout (>5s) | Timer | Typing indicator stalls | Log, increment retry counter | Serve fallback question from bank |
| LLM 5xx | HTTP status | Typing indicator stalls | Retry once after 2s delay | Serve fallback question |
| LLM hallucination | Content validation | None (prevented) | Reject output, retry with stricter prompt | Serve fallback question |
| JSON parse failure | `json.loads()` exception | None (prevented) | Retry once with "output valid JSON" reminder | Serve fallback question |
| Schema validation fail | Pydantic ValidationError | None (prevented) | Retry once with schema example | Serve fallback question |
| Session not found | KeyError in dict | "Session expired" message | Return 404 | Clear localStorage, redirect to landing |
| Rate limit | Token bucket empty | "Too many requests" with cooldown | Return 429 + Retry-After | Client exponential backoff |
| Network partition | Fetch exception | "Connection lost" toast | N/A | Auto-retry ×3 with backoff |
| Server crash | Process termination | "Server unavailable" | On restart: reload sessions from `/tmp/sessions` | Sessions <1hr old restored |

### 8.2 Fallback Question Bank

**Structure**: `fallback_questions.json`
```json
{
  "day_12": [
    {
      "question": "Explain the role of embeddings in a RAG pipeline.",
      "question_type": "teach",
      "persona": "hiring_manager"
    },
    {
      "question": "Compare dense retrieval vs. sparse retrieval for legal document search.",
      "question_type": "compare",
      "persona": "senior_engineer"
    }
  ],
  "day_14": [...]
}
```

**Selection Logic**:
1. Priority 1: Candidate's completed days that are not yet covered
2. Priority 2: Candidate's skipped days (gentle conceptual probe)
3. Priority 3: Any curriculum day (general cohort knowledge)

---

## 9. Performance & Scaling

### 9.1 Benchmarks

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (p95) | < 3s per turn | Load test: 20 concurrent sessions |
| Feedback Generation | < 30s end-to-end | Timer: request to JSON response |
| Concurrent Sessions | 10 simultaneous | Stress test with threading |
| Session State Size | < 100KB | Enforce max history length |
| Frontend Bundle | < 200KB gzipped | webpack/vite analyzer |
| Lighthouse Accessibility | ≥ 95 | Chrome DevTools audit |

### 9.2 Optimization Strategies

| Layer | Strategy |
|-------|----------|
| **LLM** | Use `temperature=0.7` for speed (lower than creative writing). Cache identical context hashes. |
| **Backend** | Uvicorn with 4 workers. In-memory state avoids DB round-trips. |
| **Frontend** | Code-splitting by route. Lazy load FeedbackView. Debounce draft saves (300ms). |
| **Network** | Keep-alive connections to OpenRouter. Compress JSON payloads. |

---

## 10. Security & Privacy

### 10.1 Threat Model

| Threat | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Session hijacking | Low | Medium | UUIDv4 session IDs (unpredictable). No auth tokens to steal. |
| Input injection | Medium | Low | Pydantic validation. Max string lengths. No SQL (no DB). |
| LLM prompt injection | Medium | Medium | System prompt hardening. No user input in system prompt. |
| Rate limit abuse | Medium | Low | 30 req/min/IP. In-memory token bucket. |
| Data leakage | Low | High | No PII. All data synthetic. Sessions purged after 1 hour. |

### 10.2 Data Handling

- **No PII**: Candidate profiles are synthetic. No real names, emails, or identifiers.
- **Ephemeral Storage**: Session data lives in memory + `/tmp/` for max 1 hour. No persistent database.
- **No External Logging**: Interview transcripts are not sent to third-party analytics.
- **CORS**: Allow all origins for hackathon demo. Document as insecure for production.

---

## 11. Deployment & Operations

### 11.1 Local Development (Primary)

```bash
# Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (dev server)
npm run dev  # → http://localhost:5173

# Environment Variables
OPENROUTER_API_KEY=sk-or-v1-...
REDIS_URL=redis://localhost:6379/0  # optional
```

### 11.2 Google Colab Deployment (Hackathon Context)

```python
# Colab Notebook Cell
!pip install fastapi uvicorn pydantic python-multipart

# Run backend
import uvicorn
from main import app

# Expose via ngrok
from pyngrok import ngrok
public_url = ngrok.connect(8000)
print(f"API URL: {public_url}")

# Frontend can point to this ngrok URL
```

### 11.3 Health Monitoring

```json
// GET /health
{
  "status": "ok",
  "llm_ready": true,
  "active_sessions": 3,
  "memory_usage_mb": 128,
  "version": "1.0.0"
}
```

### 11.4 Log Format

```json
{
  "timestamp": "2026-08-08T14:30:00Z",
  "level": "INFO",
  "session_id": "sess_abc123",
  "candidate_id": "alex_001",
  "event": "question_generated",
  "turn": 3,
  "question_type": "challenge",
  "persona": "senior_engineer",
  "fallback_used": false,
  "latency_ms": 1200,
  "tokens_used": 450
}
```

---

## 12. Integration & Coordination

### 12.1 Integration Gates

| Gate | Time | Deliverable | From → To |
|------|------|-------------|-----------|
| G1 | H0 | Pydantic models | M2 → M3 |
| G2 | H0 | Static data files | M2 → M3 |
| G3 | H1 | Draft prompt schemas | M3 → M2 |
| G4 | H2 | **OpenAPI 3.0 Spec** | M2 → M1 |
| G5 | H2 | Finalized prompts | M3 → M2 |
| G6 | H4 | Guardrail logic | M3 → M2 |
| G7 | H6 | UI component contract | M1 → M2 |
| G8 | H8 | **MVP Integration Test** | All → All |
| G9 | H24 | RAG module (if built) | M3 → M2 |
| G10 | H40 | **Final Load Test** | All → All |

### 12.2 Dependency Matrix

| Component | Depends On | Provides To |
|-----------|-----------|-------------|
| **Frontend (M1)** | OpenAPI spec (G4) | UI-specific API needs (G7) |
| **Backend (M2)** | Prompts (G5), Guardrails (G6) | OpenAPI spec (G4), Data models (G1) |
| **AI Agent (M3)** | Data models (G1), Static data (G2) | Prompts (G5), Guardrails (G6), RAG (G9) |

### 12.3 Communication Protocol

- **Shared Channel**: `#integration-gates` (Discord/Slack)
- **Artifact Naming**: `{artifact}_v{major}.{minor}.{patch}.ext`
- **Version Control**: All shared artifacts committed to repo under `/shared/`
- **Conflict Resolution**: Schema changes after H4 require migration snippet + dual ACK

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **RAG** | Retrieval-Augmented Generation |
| **MCP** | Model Context Protocol |
| **HNSW** | Hierarchical Navigable Small World (vector indexing algorithm) |
| **nDCG** | Normalized Discounted Cumulative Gain (retrieval metric) |
| **MRR** | Mean Reciprocal Rank (retrieval metric) |
| **Persona** | A defined interviewing style/voice (Hiring Manager, Senior Engineer, Staff Engineer) |
| **Evidence Log** | Structured notes appended after each turn tracking candidate signals |
| **Fallback Bank** | Pre-generated question pool used when LLM generation fails |
| **Turn** | One complete question-answer pair |

## Appendix B: File Structure

```
thread-puller/
├── backend/
│   ├── main.py                 # FastAPI app, endpoints
│   ├── models.py               # Pydantic models
│   ├── session_manager.py      # In-memory + FS + Redis state
│   ├── llm_client.py           # OpenRouter integration
│   ├── fallback_engine.py      # Fallback question selection
│   ├── validators.py           # Request validation + guardrails
│   ├── background_jobs.py      # Cleanup + health refresh
│   ├── data/
│   │   ├── curriculum.json
│   │   ├── candidate_profiles.json
│   │   └── fallback_questions.json
│   └── tests/
│       └── test_endpoints.py
│
├── frontend/
│   ├── src/
│   │   ├── store.ts            # Zustand state management
│   │   ├── api.ts              # Typed API client
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── LandingView.tsx
│   │   │   ├── InterviewView.tsx
│   │   │   ├── FeedbackView.tsx
│   │   │   └── shared/
│   │   │       ├── Button.tsx
│   │   │       ├── Skeleton.tsx
│   │   │       └── Tooltip.tsx
│   │   └── hooks/
│   │       └── useInterview.ts
│   └── package.json
│
├── ai_agent/
│   ├── prompts/
│   │   ├── system_base.txt
│   │   ├── persona_hiring_manager.txt
│   │   ├── persona_senior_engineer.txt
│   │   ├── persona_staff_engineer.txt
│   │   ├── question_generation.j2
│   │   ├── followup_generation.j2
│   │   ├── feedback_synthesis.j2
│   │   └── summarization.j2
│   ├── pipeline.py             # 4-stage inference pipeline
│   ├── guardrails.py           # Validation + hallucination checks
│   ├── evaluation.py           # Metrics computation
│   └── tests/
│       └── test_pipeline.py
│
├── shared/
│   └── openapi.json            # Auto-generated OpenAPI spec
│
├── docker-compose.yml
└── README.md
```

---

## Appendix C: OpenAPI 3.0 Spec (Condensed)

```yaml
openapi: 3.0.3
info:
  title: The Thread Puller API
  version: 1.0.0
paths:
  /health:
    get:
      responses:
        200:
          description: Health status
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string, enum: [ok] }
                  llm_ready: { type: boolean }

  /interview/start:
    post:
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                candidate_id: { type: string, minLength: 1, maxLength: 50 }
              required: [candidate_id]
      responses:
        200:
          description: Interview started
          content:
            application/json:
              schema:
                type: object
                properties:
                  session_id: { type: string, format: uuid }
                  first_question: { type: string }
                  turn_count: { type: integer }
                  can_conclude: { type: boolean }
                  covered_days: { type: array, items: { type: string } }
                  current_persona: { type: string }

  /interview/{session_id}/respond:
    post:
      parameters:
        - name: session_id
          in: path
          required: true
          schema: { type: string, format: uuid }
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                answer: { type: string, minLength: 1, maxLength: 5000 }
              required: [answer]
      responses:
        200:
          description: Next question
          content:
            application/json:
              schema:
                type: object
                properties:
                  next_question: { type: string }
                  turn_count: { type: integer }
                  can_conclude: { type: boolean }
                  covered_days: { type: array, items: { type: string } }
                  current_persona: { type: string }

  /interview/{session_id}/feedback:
    post:
      parameters:
        - name: session_id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        200:
          description: Feedback report
          content:
            application/json:
              schema:
                type: object
                properties:
                  readiness_score: { type: integer, minimum: 1, maximum: 10 }
                  strengths:
                    type: array
                    items:
                      type: object
                      properties:
                        title: { type: string }
                        evidence: { type: string }
                  growth_areas:
                    type: array
                    items:
                      type: object
                      properties:
                        title: { type: string }
                        resource: { type: string }
                  communication_tips: { type: array, items: { type: string } }
                  evidence_citations: { type: array, items: { type: string } }
                  is_partial: { type: boolean }
                  disclaimer: { type: string, nullable: true }

  /interview/{session_id}/abort:
    post:
      parameters:
        - name: session_id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        200:
          description: Partial feedback
          content:
            application/json:
              schema:
                # Same as feedback but with is_partial: true and nullable readiness_score
```

---

*End of Design Document*
