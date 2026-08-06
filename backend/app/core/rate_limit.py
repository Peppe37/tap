"""Fixed-window rate limiting for the public API, independent from the per-provider limiter in
app/workers/tasks.py (that one protects third-party providers from being hammered by tap; this
one protects tap's own API from being hammered by a single caller).
"""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import cast

from redis import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.security import InvalidTokenError, TokenType, decode_token

EXEMPT_PATHS = frozenset({"/api/health", "/api/health/ready"})
WINDOW_SECONDS = 90


def _redis() -> Redis:
    return Redis.from_url(get_settings().redis_url)


def _client_key(request: Request) -> str:
    """Best-effort caller identity: the authenticated user if the bearer token decodes cleanly,
    otherwise the client IP. Token validity itself is still enforced downstream by the normal
    auth dependency -- this only needs a stable-enough key to bucket requests by."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        try:
            user_id = decode_token(auth_header[7:], expected_type=TokenType.ACCESS)
            return f"user:{user_id}"
        except InvalidTokenError:
            pass
    client = request.client
    return f"ip:{client.host}" if client else "ip:unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path
        if not path.startswith("/api") or path in EXEMPT_PATHS:
            return await call_next(request)

        settings = get_settings()
        bucket = datetime.now(UTC).strftime("%Y%m%d%H%M")
        key = f"tap:api_rate_limit:{_client_key(request)}:{bucket}"
        redis = _redis()
        count = cast(int, redis.incr(key))
        if count == 1:
            redis.expire(key, WINDOW_SECONDS)

        if count > settings.rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down and try again shortly."},
            )
        return await call_next(request)
