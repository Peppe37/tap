"""FastAPI application entrypoint."""

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app import providers  # noqa: F401  (side effect: registers every adapter, see __init__.py)
from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.core.config import get_settings
from app.core.rate_limit import RateLimitMiddleware
from app.services.readiness import check_readiness

settings = get_settings()

app = FastAPI(title="tap - Track All Parcels", version="0.1.0")

# Order matters: CORSMiddleware must be the outermost (added last) so it still adds headers to
# responses the rate limiter short-circuits with 429 -- otherwise a rate-limited browser request
# would surface as an opaque CORS error instead of a readable 429.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix="/api")


@app.get("/api/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/health/ready", tags=["health"])
async def readiness(response: Response) -> dict[str, bool | dict[str, bool]]:
    result = await check_readiness()
    response.status_code = 200 if result.ready else 503
    return {"ready": result.ready, "checks": {"database": result.database, "redis": result.redis}}
