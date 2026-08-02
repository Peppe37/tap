"""Celery tasks driving automatic package polling.

Design: a single lightweight periodic dispatcher (``enqueue_due_packages``) finds packages whose
``next_check_at`` has passed and hands each one to the generic ``check_package_status`` task.
Per-provider rate limiting (respecting an external service's request quota, e.g. an aggregator's
free tier) is enforced inside ``check_package_status`` itself via a Redis fixed-window counter
keyed by provider code, rather than via dedicated Celery queues -- this keeps the provider plugin
system the single place that knows about a given provider's limits (``Provider.config``) without
the deployment needing one worker/queue per provider.
"""

import asyncio
import uuid
from collections.abc import Coroutine
from datetime import UTC, datetime
from typing import Any, cast

from celery.utils.log import get_task_logger
from redis import Redis
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app import providers  # noqa: F401  (side effect: registers every adapter)
from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, engine
from app.models.package import Package
from app.providers.base import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderInvalidTrackingNumberError,
    ProviderNotConfiguredError,
    ProviderRateLimitedError,
    ProviderTransientError,
)
from app.providers.registry import provider_registry
from app.services.credentials import load_credentials
from app.services.tracking import apply_tracking_result, record_fetch_failure

logger = get_task_logger(__name__)

DEFAULT_MAX_REQUESTS_PER_MINUTE = 30
DISPATCH_BATCH_SIZE = 500


async def _run_with_fresh_engine[T](coro: Coroutine[Any, Any, T]) -> T:
    """Celery's prefork workers call ``asyncio.run()`` once per task, each spinning up and later
    closing its own event loop -- but SQLAlchemy's async engine/connection pool
    (``app.db.session.engine``) is a process-wide singleton. A connection opened during one
    task's loop cannot be closed from a later task's loop (asyncpg ties a connection's transport
    to the loop that created it), so we dispose before running (drop anything left over from a
    previous invocation, against the loop that actually owns those connections) and after
    (make sure nothing this invocation opened outlives its own loop)."""
    await engine.dispose()
    try:
        return await coro
    finally:
        await engine.dispose()


_PACKAGE_EAGER_LOAD = (
    selectinload(Package.carrier),
    selectinload(Package.provider),
    selectinload(Package.events),
)


def _redis() -> Redis:
    return Redis.from_url(get_settings().redis_url)


def _provider_rate_limit_exceeded(provider_code: str, max_per_minute: int) -> bool:
    """Fixed-window counter: at most `max_per_minute` fetches per provider per clock minute."""
    bucket = datetime.now(UTC).strftime("%Y%m%d%H%M")
    key = f"tap:ratelimit:{provider_code}:{bucket}"
    redis = _redis()
    count = cast(int, redis.incr(key))
    if count == 1:
        redis.expire(key, 90)
    return count > max_per_minute


@celery_app.task(name="app.workers.tasks.enqueue_due_packages")  # type: ignore[untyped-decorator]
def enqueue_due_packages() -> int:
    return asyncio.run(_run_with_fresh_engine(_enqueue_due_packages()))


async def _enqueue_due_packages() -> int:
    now = datetime.now(UTC)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Package.id)
            .where(
                Package.is_archived.is_(False),
                or_(Package.next_check_at.is_(None), Package.next_check_at <= now),
            )
            .limit(DISPATCH_BATCH_SIZE)
        )
        package_ids = list(result.scalars().all())

    for package_id in package_ids:
        check_package_status.delay(str(package_id))

    logger.info("enqueued %d package(s) for a status check", len(package_ids))
    return len(package_ids)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="app.workers.tasks.check_package_status",
    autoretry_for=(ProviderRateLimitedError, ProviderTransientError),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def check_package_status(package_id: str) -> None:
    asyncio.run(_run_with_fresh_engine(_check_package_status(package_id)))


async def _check_package_status(package_id: str) -> None:
    async with AsyncSessionLocal() as session:
        package = await session.get(Package, uuid.UUID(package_id), options=_PACKAGE_EAGER_LOAD)
        if package is None or package.is_archived:
            return

        implementation = provider_registry.get(package.provider.code)
        max_per_minute = package.provider.config.get(
            "max_requests_per_minute", DEFAULT_MAX_REQUESTS_PER_MINUTE
        )
        if _provider_rate_limit_exceeded(package.provider.code, max_per_minute):
            raise ProviderRateLimitedError(
                f"local rate limit reached for provider {package.provider.code!r}"
            )

        credentials: dict[str, str] | None = None
        if implementation.requires_credentials:
            credentials = await load_credentials(
                session, user_id=package.user_id, provider_id=package.provider_id
            )
            if credentials is None:
                # Nothing to do until the user configures a connection; check back much later
                # instead of retrying every beat tick.
                record_fetch_failure(package)
                await session.commit()
                return

        permanent_errors = (
            ProviderInvalidTrackingNumberError,
            ProviderAuthenticationError,
            ProviderNotConfiguredError,
        )
        try:
            result = await implementation.fetch(
                package.tracking_number, package.carrier.code, credentials, package.provider_params
            )
        except permanent_errors as exc:
            record_fetch_failure(package)
            await session.commit()
            logger.warning("permanent error checking package %s: %s", package_id, exc)
            return
        except ProviderError:
            record_fetch_failure(package)
            await session.commit()
            raise  # transient/rate-limit: let Celery's autoretry_for handle backoff+retry

        apply_tracking_result(package, result)
        await session.commit()
