import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.config import settings
from app.services.data_loader import FALLBACK_QUESTIONS, CURRICULUM_STORE
from app.models.schemas import CandidateProfile, FeedbackReport, InterviewSession

logger = logging.getLogger(__name__)

# Global flag for health check status
llm_ready: bool = False


async def check_llm_health() -> bool:
    """Ping OpenRouter API to verify connectivity and update llm_ready flag."""
    global llm_ready
    if not settings.OPENROUTER_API_KEY:
        llm_ready = False
        return False

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
            res = await client.post(settings.OPENROUTER_API_URL, headers=headers, json=payload)
            if res.status_code == 200:
                llm_ready = True
                return True
            else:
                logger.warning(f"LLM Health check returned status {res.status_code}")
                llm_ready = False
                return False
    except Exception as e:
        logger.warning(f"LLM Health check failed: {e}")
        llm_ready = False
        return False


def get_fallback_question(session: InterviewSession) -> str:
    """Select appropriate question from fallback question bank based on turn count and covered days."""
    days = list(CURRICULUM_STORE.keys()) or ["day_1", "day_2", "day_3"]
    # Pick target day based on turn count
    day_idx = session.turn_count % len(days)
    target_day = days[day_idx]

    session.covered_days.add(target_day)

    questions = FALLBACK_QUESTIONS.get(target_day, [
        "Can you describe your experience with Python, FastAPI, and asynchronous backend development?",
        "How do you approach error handling, logging, and state management in production services?",
        "What strategies do you use for integration testing and microservices resilience?"
    ])

    q_idx = (session.turn_count // len(days)) % len(questions)
    return questions[q_idx]


async def generate_next_question(
    session: InterviewSession,
    candidate_profile: Optional[CandidateProfile],
    candidate_answer: Optional[str] = None
) -> str:
    """
    Generate next interview question via OpenRouter LLM.
    If timeout (5s), 5xx (retry 1x after 2s), or error, serve from fallback pool.
    """
    if candidate_answer:
        session.conversation_history.append({"role": "candidate", "content": candidate_answer})

    if not settings.OPENROUTER_API_KEY:
        logger.info("OPENROUTER_API_KEY not provided. Serving question from fallback bank.")
        q = get_fallback_question(session)
        session.conversation_history.append({"role": "interviewer", "content": q})
        return q

    prompt_messages = [
        {
            "role": "system",
            "content": (
                f"You are a technical interviewer acting as persona: {session.current_persona}. "
                f"Candidate ID: {session.candidate_id}. Ask a single targeted technical interview question "
                f"based on Python, FastAPI, microservices architecture, and state management."
            )
        }
    ]
    # Add conversation history
    for entry in session.conversation_history:
        prompt_messages.append({"role": entry["role"], "content": entry["content"]})

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": prompt_messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    attempts = 2
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
                res = await client.post(settings.OPENROUTER_API_URL, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    session.conversation_history.append({"role": "interviewer", "content": content})
                    # Mark day as covered
                    days = list(CURRICULUM_STORE.keys()) or ["day_1"]
                    session.covered_days.add(days[session.turn_count % len(days)])
                    return content
                elif res.status_code >= 500 and attempt == 0:
                    logger.warning(f"OpenRouter 5xx ({res.status_code}). Retrying in 2 seconds...")
                    await asyncio.sleep(2)
                    continue
                else:
                    logger.error(f"OpenRouter returned status {res.status_code}: {res.text}")
                    break
        except httpx.TimeoutException:
            logger.warning("OpenRouter API timed out after 5 seconds.")
            break
        except Exception as e:
            logger.error(f"OpenRouter call failed with exception: {e}")
            break

    # Fallback if LLM failed
    logger.info("Serving fallback question due to LLM error or timeout.")
    q = get_fallback_question(session)
    session.conversation_history.append({"role": "interviewer", "content": q})
    return q


async def generate_feedback_report(session: InterviewSession, is_partial: bool = False) -> FeedbackReport:
    """
    Generate feedback synthesis report via LLM or fallback deterministic generator.
    """
    # Deterministic fallback evaluation logic
    covered_list = list(session.covered_days)
    readiness_score = min(10, max(3, len(session.conversation_history) + len(covered_list)))

    fallback_report = FeedbackReport(
        readiness_score=readiness_score,
        strengths=[
            {"title": "API & Schema Design", "evidence": "Demonstrated understanding of RESTful routing and Pydantic validation schemas."},
            {"title": "State Resolution", "evidence": "Understands multi-tier session state management across RAM, Redis, and Disk."}
        ],
        growth_areas=[
            {"title": "LLM Resilience Strategy", "resource": "Review fallback question banks, rate limiting retry-after, and circuit breaker patterns."}
        ],
        communication_tips=[
            "Be clear and concise when explaining state persistence tradeoffs under heavy concurrency."
        ],
        evidence_citations=[
            f"Candidate answered {session.turn_count} interview prompt turn(s).",
            f"Covered curriculum day topics: {', '.join(covered_list) if covered_list else 'Day 1 System Architecture'}"
        ],
        is_partial=is_partial,
        disclaimer="Partial evaluation generated early upon abort request." if is_partial else None
    )

    if not settings.OPENROUTER_API_KEY:
        return fallback_report

    prompt = (
        "Analyze the following technical interview transcript and return a JSON feedback report with format: "
        "readiness_score (int 1-10), strengths (list of objects with title, evidence), growth_areas (list of objects with title, resource), "
        "communication_tips (list of str), evidence_citations (list of str).\n\n"
        f"Transcript:\n{json.dumps(session.conversation_history, indent=2)}"
    )

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2048,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.post(settings.OPENROUTER_API_URL, headers=headers, json=payload)
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"]
                report_data = json.loads(content)
                report_data["is_partial"] = is_partial
                if is_partial:
                    report_data["disclaimer"] = "Partial feedback generated upon early termination."
                return FeedbackReport(**report_data)
    except Exception as e:
        logger.warning(f"Feedback LLM call failed or timed out. Serving synthesized fallback: {e}")

    return fallback_report
