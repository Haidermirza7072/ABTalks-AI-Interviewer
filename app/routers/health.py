from fastapi import APIRouter
from app.services.llm_client import check_llm_health, llm_ready

router = APIRouter(tags=["Health"])

@router.get("/health", summary="Health check + LLM connectivity status")
async def health_check():
    """Return application health and LLM connectivity status."""
    is_ready = await check_llm_health()
    return {
        "status": "ok",
        "llm_ready": is_ready
    }
