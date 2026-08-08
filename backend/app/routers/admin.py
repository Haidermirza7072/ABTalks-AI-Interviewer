import os
import psutil
from fastapi import APIRouter
from app.services.data_loader import init_data_stores
from app.services.session_manager import SESSION_STORE

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/reload-data", summary="Reload static JSON data")
async def reload_data():
    """Reload static curriculum and candidate profile JSON data from disk."""
    days, candidates = init_data_stores()
    return {
        "status": "reloaded",
        "days": days,
        "candidates": candidates
    }

@router.get("/stats", summary="Get system & session statistics")
async def get_stats():
    """Return active session count and current server memory usage."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return {
        "active_sessions": len(SESSION_STORE),
        "rss_memory_bytes": mem_info.rss,
        "rss_memory_mb": round(mem_info.rss / (1024 * 1024), 2)
    }
