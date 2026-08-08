import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from datetime import datetime, timezone

from app.config import settings

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = None, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests or settings.RATE_LIMIT_PER_MINUTE
        self.window_seconds = window_seconds
        self.client_requests: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Exclude documentation and health check from rate limiting if desired, or apply globally
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        # Clean old timestamps outside sliding window
        window_start = now - self.window_seconds
        requests = [ts for ts in self.client_requests[client_ip] if ts > window_start]
        self.client_requests[client_ip] = requests

        if len(requests) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - requests[0]))
            retry_after = max(1, retry_after)
            content = {
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit of {self.max_requests} requests/min exceeded. Please try again later.",
                "recoverable": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            return JSONResponse(
                status_code=429,
                content=content,
                headers={"Retry-After": str(retry_after)}
            )

        self.client_requests[client_ip].append(now)
        response = await call_next(request)
        return response
