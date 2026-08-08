import asyncio
import logging
import sys
import traceback
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.routers import admin, health, interview
from app.services.data_loader import init_data_stores
from app.services.llm_client import check_llm_health
from app.services.session_manager import cleanup_expired_sessions, reload_sessions_from_disk_on_startup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Background task loops
async def periodic_session_cleanup():
    while True:
        try:
            await asyncio.sleep(600)  # Every 10 minutes
            cleaned = cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired sessions.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in background session cleanup: {e}")

async def periodic_health_check():
    while True:
        try:
            await check_llm_health()
            await asyncio.sleep(60)  # Every 60 seconds
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in background LLM health check: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Initializing 'The Thread Puller' Backend Service...")
    init_data_stores()
    reload_sessions_from_disk_on_startup()
    await check_llm_health()

    cleanup_task = asyncio.create_task(periodic_session_cleanup())
    health_task = asyncio.create_task(periodic_health_check())

    yield

    # Shutdown tasks
    logger.info("Shutting down background tasks...")
    cleanup_task.cancel()
    health_task.cancel()


app = FastAPI(
    title="The Thread Puller API",
    description="Backend microservice for AI-powered technical interview orchestration.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware (Hackathon scope: allow all)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware (30 req/min/IP)
app.add_middleware(RateLimiterMiddleware, max_requests=settings.RATE_LIMIT_PER_MINUTE)

# Register Routers
app.include_router(health.router)
app.include_router(interview.router)
app.include_router(admin.router)

# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format 422 validation errors with field-level details."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Invalid request payload or query parameters.",
            "details": exc.errors(),
            "recoverable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled server exceptions, log traceback, return standard 500 error schema."""
    logger.error(f"Unhandled Server Error on {request.method} {request.url.path}: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again.",
            "recoverable": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
