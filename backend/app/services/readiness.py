"""Readiness check: distinct from the plain liveness check at GET /api/health (always "ok" if the
process is running), this actually exercises the database and Redis connections so an
orchestrator can tell "the process is up" apart from "the process can actually serve requests".
"""

from dataclasses import dataclass

import sqlalchemy.exc
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal


@dataclass
class ReadinessResult:
    database: bool
    redis: bool

    @property
    def ready(self) -> bool:
        return self.database and self.redis


async def _check_database() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except sqlalchemy.exc.SQLAlchemyError:
        return False


async def _check_redis() -> bool:
    try:
        client = Redis.from_url(get_settings().redis_url)
        try:
            client.ping()
        finally:
            client.close()
        return True
    except RedisError:
        return False


async def check_readiness() -> ReadinessResult:
    return ReadinessResult(database=await _check_database(), redis=await _check_redis())
