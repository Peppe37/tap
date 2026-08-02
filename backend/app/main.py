"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import providers  # noqa: F401  (side effect: registers every adapter, see __init__.py)
from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="tap - Track All Packs", version="0.1.0")

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
