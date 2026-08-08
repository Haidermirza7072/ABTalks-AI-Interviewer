 # Product Requirements Document (PRD)
## AI Interview Agent — "The Thread Puller"
**Version**: 1.0  
**Status**: Draft  
**Date**: 2026-08-08  
**Author**: Senior Product Manager, AI Cohort Hackathon  
**Stakeholders**: Engineering Team, Design Team, Hackathon Judges, Cohort Instructors

---

## 1. Executive Summary

**The Thread Puller** is an AI-powered conversational interview agent designed to conduct realistic, adaptive technical interviews for graduates of the 31-day AI Cohort program. Unlike static quiz systems, it engages candidates in multi-turn dialogues that probe depth, adapt to individual learning journeys, and deliver structured, actionable feedback.

**Strategic Value**: The agent bridges the gap between *learning* and *articulating* knowledge. By simulating a real technical interview calibrated to each candidate's completed curriculum, it reduces interview anxiety, surfaces knowledge gaps before high-stakes situations, and provides instructors with a scalable readiness assessment tool. For the hackathon, success means demonstrating a living, breathing interview experience that feels indistinguishable from a conversation with a senior engineer—while exposing a clean, compliant HTTP API.

---

## 2. Problem Statement & User Personas

### Problem Statement

Graduates of intensive technical programs often possess strong hands-on skills but struggle to **communicate their knowledge under interview pressure**. Existing preparation tools are either:
- **Too rigid**: Static Q&A banks that don't adapt to what the candidate actually learned
- **Too generic**: Mock interviews that ignore the candidate's specific project history and skipped topics
- **Too shallow**: Single-turn question formats that fail to probe reasoning depth

There is no scalable, personalized system that conducts a *conversational* technical interview based on a candidate's actual 31-day learning trajectory.

### User Personas

#### Persona 1: "Anxious Alex" — The Cohort Graduate
- **Role**: Junior AI Engineer, recently completed the 31-day AI Cohort
- **Demographics**: 24-32 years old, career-switcher or upskiller, 0-2 years of professional AI experience
- **Goals**:
  - Practice explaining technical decisions without freezing up
  - Receive feedback on *how* they communicate, not just *what* they know
  - Feel confident before real job interviews
- **Frustrations**:
  - "I built a RAG system but I don't know how to explain why I chose ChromaDB"
  - "Mock interviews with friends are too nice; real interviews destroy me"
  - "I skipped Day 14 and I'm terrified someone will ask about it"
- **Motivation**: Wants a safe, judgment-free space to fail and improve

#### Persona 2: "Busy Priya" — The Cohort Instructor / Program Lead
- **Role**: Senior Engineer running the AI Cohort, responsible for 50+ learners
- **Demographics**: 30-40 years old, staff+ engineer, time-constrained
- **Goals**:
  - Identify which learners are truly interview-ready vs. which need coaching
  - Scale personalized feedback without 1:1 time investment
  - Ensure cohort outcomes are demonstrable to hiring partners
- **Frustrations**:
  - "I don't have 30 minutes per learner to conduct mock interviews"
  - "Completion metrics don't tell me if someone *understands* what they built"
  - "I need structured data on learner readiness, not gut feelings"
- **Motivation**: Wants an objective, repeatable assessment tool that respects her time

---

## 3. Goals & Success Metrics

### SMART Objectives

| # | Objective | Target | Measurement Method |
|---|-----------|--------|-------------------|
| 1 | **Conversational Depth**: Deliver interviews with ≥8 questions covering ≥4 distinct curriculum days | 100% of sessions | Automated transcript analysis post-session |
| 2 | **Adaptive Follow-Up Quality**: Generate contextually relevant follow-up questions based on previous responses | ≥80% of follow-ups rated relevant by human reviewers | Blind review of 20 sample transcripts |
| 3 | **Feedback Actionability**: Produce structured end-of-interview feedback within 30 seconds of session end | 100% of sessions, ≤30s latency | API response time logging |
| 4 | **API Contract Compliance**: Expose all required endpoints with correct request/response schemas | 100% endpoint coverage | Automated integration test suite |
| 5 | **Perceived Realism**: Candidates rate the interview as "realistic" and "helpful" | ≥4.0/5.0 average rating | Post-interview Likert scale survey (synthetic user testing) |

### Key Performance Indicators (KPIs)

| KPI | Definition | Target | Tracking Frequency |
|-----|-----------|--------|-------------------|
| **Interview Completion Rate** | % of initiated interviews that reach the feedback stage | ≥95% | Per session |
| **Context Retention Score** | % of follow-up questions that correctly reference earlier turns in the same session | ≥90% | Per session |
| **Feedback Specificity Index** | Average number of transcript citations per feedback report | ≥3 citations | Per session |
| **Question Variety Score** | Number of distinct cognitive question types used (challenge, expand, compare, apply, teach) | ≥4 types | Per session |
| **API Uptime / Latency** | % of successful requests; p95 response time | 99% uptime; p95 < 3s | Continuous |

---

## 4. Feature Scope

### P0 — Must-Have (Critical for MVP / Launch)

| Feature | Description | Acceptance Criteria |
|---------|-------------|---------------------|
| **Conversational Interview Engine** | Multi-turn interview endpoint that accepts candidate responses and returns the next question | HTTP endpoint accepts `POST /interview/{session_id}/respond`; maintains state across turns |
| **Dynamic Follow-Up Generation** | LLM-powered follow-ups that probe claims, assumptions, or shallow answers from the previous response | ≥80% of follow-ups reference specific content from the immediately preceding answer |
| **Curriculum-Aware Questioning** | Questions drawn from and anchored to the 31-day curriculum JSON | Each session touches ≥4 distinct curriculum day IDs; each question maps to a learning objective |
| **Candidate Profile Ingestion** | Load candidate progress (completed missions, skipped topics, attempts) into interview context | System prompt includes candidate profile metadata at session initialization |
| **Context Persistence** | Full conversation history maintained per session ID | API accepts arbitrary turn count; history fed to LLM on every request; no loss of context mid-session |
| **Structured Feedback Report** | JSON-formatted post-interview feedback with Strengths, Growth Areas, Communication Tips, Readiness Score | `POST /interview/{session_id}/feedback` returns compliant JSON within 30s of request |
| **Minimum Question Threshold** | Guarantee at least 8 questions before allowing interview conclusion | Interview cannot be finalized before 8 turns; system enforces minimum |

### P1 — Should-Have (High Priority, Post-MVP)

| Feature | Description | Acceptance Criteria |
|---------|-------------|---------------------|
| **Persona Rotation** | System switches questioning style (Hiring Manager → Senior Engineer → Staff Engineer) mid-interview | ≥2 persona switches per interview; transitions include natural bridge phrases |
| **Project Metadata Grounding** | Reference candidate's completed missions/tools by name during questioning | ≥30% of questions mention a specific tool or mission from the candidate's profile |
| **Edge Case Handling** | Graceful degradation for nonsensical, evasive, or extremely brief answers | Detects off-topic/empty responses and redirects with a rephrased or simpler question |
| **Interview Abort / Resume** | Allow explicit session termination and summary generation before 8 questions if needed | `POST /interview/{session_id}/abort` returns partial feedback with disclaimer |

### P2 — Could-Have (Nice to Have)

| Feature | Description | Acceptance Criteria |
|---------|-------------|---------------------|
| **Confidence Calibration** | Real-time analysis of response signals (hedge words, length, semantic depth) to modulate difficulty | Difficulty score shifts up/down based on 3-turn rolling confidence window |
| **RAG over Project Artifacts** | Vector retrieval from synthetic project submissions to ask code-level questions | Top-3 relevant project chunks retrieved and cited in ≥20% of questions |
| **Emotional Tone Adaptation** | Adjust system tone (encouraging vs. challenging) based on candidate response patterns | Tone shift occurs ≤1x per interview; logged for feedback transparency |

### P3 — Won't-Have (Out of Scope)

| Feature | Rationale |
|---------|-----------|
| Voice interaction | Out of scope per technical specification; text-only for this release |
| User authentication / persistent accounts | Synthetic data only; no identity management required |
| Long-term conversation history | Sessions are ephemeral; no cross-session memory |
| Mobile native application | Web-based API only; responsive UI not required |
| Real-time candidate emotion detection (video/facial) | Privacy complexity and hardware requirements exceed hackathon scope |
| Integration with external LMS or HR systems | No external API dependencies beyond LLM and optional vector DB |

---

## 5. User Flows

### Primary Use Case: "Anxious Alex" Completes a Full Interview

```text
Step 1: INITIATION
├─ Client calls POST /interview/start
├─ Request body: { candidate_id: "alex_001" }
├─ System loads Alex's profile from candidate_profiles.json
├─ System initializes session_state (session_id, history[], turn_count=0, 
│   covered_days=Set(), question_types_used=Queue())
└─ Response: { session_id: "sess_abc123", first_question: "..." }

Step 2: INTERVIEW LOOP (Repeats until turn_count ≥ 8 and coverage ≥ 4 days)
├─ Client displays question to Alex
├─ Alex formulates and submits response
├─ Client calls POST /interview/{session_id}/respond
│   └─ Request body: { answer: "I chose ChromaDB because..." }
├─ System appends answer to history
├─ System analyzes answer for: curriculum day coverage, depth signals, 
│   claims made, question type used
├─ System updates covered_days and question_types_used
├─ System generates next_question via LLM with full context:
│   - System prompt: persona + candidate profile + instructions
│   - User messages: full conversation history
│   - Constraint: "Do not repeat recent question structures. 
│     Reference specific claims from the last answer."
├─ System increments turn_count
├─ System persists updated state
└─ Response: { next_question: "...", turn_count: N, can_conclude: false }

Step 3: CONCLUSION TRIGGER
├─ When turn_count ≥ 8 AND covered_days.size ≥ 4
├─ System sets can_conclude = true in response
├─ Client may show "End Interview" button or continue
└─ If Alex continues, loop resumes with can_conclude = true

Step 4: FEEDBACK GENERATION
├─ Client calls POST /interview/{session_id}/feedback
├─ System compiles evidence_log (strengths/growth signals gathered during loop)
├─ System sends full transcript + evidence_log to LLM synthesis prompt
├─ LLM generates structured feedback with mandatory evidence citations
├─ System validates JSON schema compliance
└─ Response: { 
      readiness_score: 7, 
      strengths: [...], 
      growth_areas: [...], 
      communication_tips: [...],
      evidence_citations: [...]
    }

Step 5: TERMINATION
├─ System marks session as closed
├─ State retained in memory for 1 hour then purged (no long-term storage)
└─ Client displays feedback report to Alex
```

### Edge Cases & Alternative Flows

| Edge Case | Trigger | System Behavior |
|-----------|---------|-----------------|
| **E1: Empty/Nonsensical Answer** | Answer length < 5 chars or off-topic | System responds with a rephrased, simpler question on the same topic. Does not increment turn_count. Logs a "redirect" event. |
| **E2: Candidate Repeats Same Answer** | Semantic similarity to previous answer > 0.90 | System switches to a contrasting question type (e.g., from "explain" to "compare"). Logs "stuck detection." |
| **E3: API Timeout / LLM Failure** | LLM response > 5s or 5xx error | System returns a cached "fallback question" from a pre-generated pool aligned to uncovered curriculum days. Logs error for retry. |
| **E4: Early Abort** | Client calls abort before turn_count ≥ 8 | System generates partial feedback with a disclaimer: "Interview incomplete—feedback based on N questions only." |
| **E5: Duplicate Session ID** | Client calls start with existing active session | System returns existing session state and last question (resume behavior). |
| **E6: Curriculum Day Exhaustion** | All required days covered early (turn < 8) | System continues with advanced/comparative questions on already-covered days to reach 8-turn minimum. |

---

## 6. Technical & Design Requirements

### Technical Architecture

| Component | Specification | Rationale |
|-----------|-------------|-----------|
| **Backend Framework** | FastAPI (Python) | Async-native, automatic OpenAPI docs, JSON schema validation via Pydantic |
| **LLM Provider** | OpenRouter API (Nemotron 3 Ultra or equivalent) | Cost-efficient, high context window (128K+), strong reasoning for follow-ups |
| **State Management** | In-memory dictionary (Python dict) with optional Redis fallback | Hackathon-appropriate; sessions are ephemeral; < 50 concurrent users expected |
| **Data Layer** | Static JSON files (curriculum.json, candidate_profiles.json) loaded at startup | Synthetic data; no database required for MVP |
| **Vector Store (P1+)** | ChromaDB (in-memory or lightweight persistent) | For project metadata RAG; minimal setup, Python-native |
| **Deployment** | Uvicorn server; containerized via Docker | Portable; easy to demo locally or on lightweight cloud instance |

### Performance Benchmarks

| Metric | Requirement | Test Method |
|--------|-------------|-------------|
| **API Response Time (p95)** | < 3 seconds per turn | Load test with 20 concurrent sessions |
| **Feedback Generation Time** | < 30 seconds end-to-end | Timer from request to JSON response |
| **Concurrent Sessions** | Support 10 simultaneous interviews | Stress test with threading |
| **Session State Size** | < 100KB per active session | History + metadata limit enforcement |
| **Uptime** | 99% during demo window | Health check endpoint `/health` |

### Security & Compliance

| Requirement | Implementation |
|-------------|----------------|
| **Input Sanitization** | Pydantic validators on all request bodies; max string lengths enforced (answer ≤ 5000 chars) |
| **No PII Persistence** | Candidate profiles are synthetic; no real user data. Session data purged after 1 hour. |
| **Rate Limiting** | 30 requests/minute per IP (middleware) to prevent LLM API abuse |
| **API Schema Validation** | All responses validated against Pydantic models before return; 422 errors for malformed input |

### API Dependencies

| Dependency | Purpose | Fallback if Unavailable |
|------------|---------|------------------------|
| OpenRouter API | LLM inference for questions, follow-ups, feedback | Local cached question bank + template feedback |
| ChromaDB (optional) | Vector retrieval for project-aware RAG (P1) | Degrade to profile metadata only |

### UX/UI Design Principles

| Principle | Application |
|-----------|-------------|
| **Progress Visibility** | Show turn counter (e.g., "Question 3 of 8+") and a subtle topic coverage indicator so Alex knows the interview is progressing |
| **Typing Tolerance** | Large, forgiving text input; auto-save draft every 3 seconds; no punitive timers |
| **Persona Signaling** | When persona switches, display a subtle avatar/name change (e.g., "👔 Hiring Manager asks...") so the shift feels intentional, not chaotic |
| **Feedback Readability** | Feedback report uses color-coded severity (green strengths / amber growth / red critical gaps) with direct quote callouts |
| **Error Recovery** | If backend errors, show a human-friendly message: *"The interviewer is thinking... let's try a different angle."* Never expose raw stack traces |

---

## 7. Dependencies & Risks

### Cross-Team / External Dependencies

| Dependency | Owner | Impact if Blocked | Mitigation |
|------------|-------|-------------------|------------|
| **LLM API Access (OpenRouter)** | External provider | Cannot generate dynamic questions | Pre-generate 50 fallback question chains; cache responses |
| **Curriculum JSON finalization** | Cohort organizers | Wrong topics or missing days | Build adapter layer; validate JSON schema at startup; fail fast with clear error |
| **Candidate Profile format lock** | Cohort organizers | Cannot personalize interviews | Build robust parser with defaults for missing fields |
| **Hackathon judging API requirements** | Judges/Organizers | Disqualification if contract violated | Build OpenAPI spec first; validate every response against spec before demo |

### Technical Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **R1: LLM hallucinates off-curriculum questions** | Medium | High | Hard-constrain LLM with curriculum JSON in system prompt; validate output against allowed topic IDs |
| **R2: Context window overflow** | Medium | High | Implement conversation summarization after turn 6; keep only last 4 full turns + summary of earlier turns |
| **R3: JSON schema non-compliance in feedback** | Medium | Critical | Use Pydantic models + `response_format={"type": "json_object"}`; validate before returning; retry once on failure |
| **R4: State loss mid-interview** | Low | High | In-memory state backed by simple file dump every 2 turns; load on restart if session < 1 hour old |
| **R5: Follow-up loops (repetitive "Why?")** | Medium | Medium | Maintain `recent_question_types` queue (last 3); explicitly prompt LLM to vary structure; enforce diversity rule |

### Mitigation Playbook

- **For R1/R3**: Implement a "guardian layer"—a lightweight validation function that runs *before* returning any LLM output to the client. If validation fails, trigger a single retry with a stricter prompt. If retry fails, serve from fallback cache.
- **For R2**: Set max_tokens per answer summary (200 tokens). Use a rolling window: full context for turns 1-6, summarized context for turns 7+.
- **For R4**: Write session state to `/tmp/sessions/{session_id}.json` asynchronously every 2 turns. On startup, scan and reload recent files.

---

## 8. Milestones & Timeline

### Phase 0: Foundation (Hours 0–2)
- [ ] Finalize OpenAPI contract and share with team
- [ ] Set up FastAPI scaffold with Pydantic models
- [ ] Load curriculum.json and candidate_profiles.json into memory
- [ ] Build `/health` and `/interview/start` endpoints (static first question)

**Deliverable**: API returns a hardcoded first question for any candidate ID.

### Phase 1: MVP Core (Hours 2–8)
- [ ] Implement in-memory session state management
- [ ] Build `/interview/{session_id}/respond` with LLM integration
- [ ] Enforce 8-question minimum and 4-day coverage tracking
- [ ] Implement dynamic follow-up generation with conversation history
- [ ] Build `/interview/{session_id}/feedback` with structured JSON output
- [ ] Add input validation, rate limiting, and error handling
- [ ] Write integration tests for happy path + E1/E4 edge cases

**Deliverable**: End-to-end working interview. A candidate can start, answer 8+ questions, and receive structured feedback.

### Phase 2: Alpha Polish (Hours 8–24)
- [ ] Add persona rotation (P1) with natural bridge phrases
- [ ] Implement project metadata grounding using candidate profile
- [ ] Build edge case handlers (E1–E3)
- [ ] Add conversation summarization for context window management
- [ ] Implement feedback evidence anchoring (citations from transcript)
- [ ] UI polish: progress indicators, persona avatars, feedback report styling
- [ ] Run 10 simulated end-to-end interviews; measure KPIs

**Deliverable**: Adaptive, persona-switching interview with grounded questions and polished feedback.

### Phase 3: Beta Differentiation (Hours 24–40)
- [ ] Add ChromaDB RAG for project artifact retrieval (P1/P2)
- [ ] Implement confidence calibration prototype (P2) — lightweight hedge-word detection
- [ ] Add emotional tone adaptation (P2) — encourage vs. challenge toggle
- [ ] Performance optimization: p95 latency < 3s
- [ ] Expand edge case coverage (E5, E6)
- [ ] Load testing: 10 concurrent sessions

**Deliverable**: Differentiated demo with RAG grounding and adaptive difficulty.

### Phase 4: Launch & Demo Prep (Hours 40–48)
- [ ] Final bug fixes and stability hardening
- [ ] Create demo script with 2 distinct candidate profiles
- [ ] Prepare "wow moment": show same question answered by different personas
- [ ] Document API for judges
- [ ] Record 3 sample interview transcripts for submission

**Deliverable**: Stable, demo-ready system with documented API and sample outputs.

---

## Alignment with Broader Product Vision & Business Objectives

### Product Vision
> *"Every learner deserves an interview experience that feels like it was designed just for them—because it was."*

The Thread Puller is not a quiz engine. It is a **readiness accelerator** that treats interviewing as a skill to be practiced, not a gate to be feared. By grounding every question in the candidate's actual learning journey and maintaining true conversational context, we transform interview prep from a chore into a personalized coaching moment.

### Business Objectives Alignment

| Business Objective | How This PRD Delivers |
|-------------------|----------------------|
| **Improve cohort completion-to-placement confidence** | Structured feedback gives candidates concrete language to articulate their skills in real interviews |
| **Scale instructor assessment capacity** | Automated, consistent evaluation reduces manual mock interview burden by 90%+ |
| **Demonstrate AI-native product thinking** | Dynamic follow-ups, persona rotation, and RAG grounding showcase agentic AI architecture |
| **Generate reusable IP** | The interview engine pattern (profile-aware, context-persistent, feedback-generating) can be adapted to future cohorts or domains |

### Success in 48 Hours Looks Like...
A judge watching our demo sees two candidates with wildly different profiles receive completely different interview experiences—both probing, both fair, both ending with feedback so specific it cites their own words. The API is clean. The conversation is alive. **The interviewer was built. The interview felt human.**

---

**End of PRD**