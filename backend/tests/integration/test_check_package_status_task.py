"""Exercises the Celery task's async core directly (not through Celery/Redis), reusing the same
transactional test session as the rest of the integration suite so it never touches real data."""

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PackageStatus
from app.providers.base import (
    ProviderInvalidTrackingNumberError,
    ProviderTransientError,
    TrackingEventDTO,
    TrackingResult,
)
from app.providers.inpost.provider import InPostProvider
from app.workers import tasks
from tests.integration.conftest import unique_email

PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def _use_shared_session(monkeypatch: pytest.MonkeyPatch, seeded_db: AsyncSession) -> None:
    @asynccontextmanager
    async def _session_cm():  # type: ignore[no-untyped-def]
        yield seeded_db

    monkeypatch.setattr(tasks, "AsyncSessionLocal", _session_cm)


async def _create_package(client: AsyncClient) -> str:
    email = unique_email()
    setup = await client.post("/auth/setup", json={"email": email, "password": PASSWORD})
    headers = {"Authorization": f"Bearer {setup.json()['access_token']}"}

    response = await client.post(
        "/packages",
        json={
            "tracking_number": "60011234567890123456789012",
            "carrier_code": "inpost",
            "provider_code": "inpost_official",
        },
        headers=headers,
    )
    package_id: str = response.json()["id"]
    return package_id


async def test_success_updates_status_and_schedules_next_check(
    client: AsyncClient, seeded_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    package_id = await _create_package(client)

    async def fake_fetch(self, tracking_number, carrier_code, credentials, extra_params=None):  # type: ignore[no-untyped-def]
        return TrackingResult(
            status=PackageStatus.OUT_FOR_DELIVERY,
            events=[
                TrackingEventDTO(
                    occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
                    status=PackageStatus.OUT_FOR_DELIVERY,
                    description="Out for delivery",
                )
            ],
        )

    monkeypatch.setattr(InPostProvider, "fetch", fake_fetch)
    monkeypatch.setattr(tasks, "_provider_rate_limit_exceeded", lambda *_args, **_kwargs: False)

    await tasks._check_package_status(package_id)

    package = await seeded_db.get(tasks.Package, uuid.UUID(package_id))
    assert package is not None
    assert package.status is PackageStatus.OUT_FOR_DELIVERY
    assert package.failure_count == 0
    assert package.next_check_at is not None


async def test_permanent_error_backs_off_without_raising(
    client: AsyncClient, seeded_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    package_id = await _create_package(client)

    async def fake_fetch(self, tracking_number, carrier_code, credentials, extra_params=None):  # type: ignore[no-untyped-def]
        raise ProviderInvalidTrackingNumberError("not found")

    monkeypatch.setattr(InPostProvider, "fetch", fake_fetch)
    monkeypatch.setattr(tasks, "_provider_rate_limit_exceeded", lambda *_args, **_kwargs: False)

    await tasks._check_package_status(package_id)  # must not raise

    package = await seeded_db.get(tasks.Package, uuid.UUID(package_id))
    assert package is not None
    assert package.status is PackageStatus.CREATED  # unchanged
    assert package.failure_count == 1
    assert package.next_check_at is not None


async def test_transient_error_backs_off_and_reraises_for_celery_retry(
    client: AsyncClient, seeded_db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    package_id = await _create_package(client)

    async def fake_fetch(self, tracking_number, carrier_code, credentials, extra_params=None):  # type: ignore[no-untyped-def]
        raise ProviderTransientError("upstream is down")

    monkeypatch.setattr(InPostProvider, "fetch", fake_fetch)
    monkeypatch.setattr(tasks, "_provider_rate_limit_exceeded", lambda *_args, **_kwargs: False)

    with pytest.raises(ProviderTransientError):
        await tasks._check_package_status(package_id)

    package = await seeded_db.get(tasks.Package, uuid.UUID(package_id))
    assert package is not None
    assert package.failure_count == 1


async def test_local_rate_limit_prevents_fetch_and_raises(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    package_id = await _create_package(client)
    fetch_calls = 0

    async def fake_fetch(self, tracking_number, carrier_code, credentials, extra_params=None):  # type: ignore[no-untyped-def]
        nonlocal fetch_calls
        fetch_calls += 1
        return TrackingResult(status=PackageStatus.IN_TRANSIT, events=[])

    monkeypatch.setattr(InPostProvider, "fetch", fake_fetch)
    monkeypatch.setattr(tasks, "_provider_rate_limit_exceeded", lambda *_args, **_kwargs: True)

    with pytest.raises(Exception, match="local rate limit"):
        await tasks._check_package_status(package_id)

    assert fetch_calls == 0
