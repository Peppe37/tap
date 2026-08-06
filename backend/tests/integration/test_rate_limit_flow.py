from collections.abc import Generator

import pytest
from httpx import AsyncClient

from app.core.config import get_settings
from tests.integration.conftest import unique_email

PASSWORD = "correct-horse-battery"


@pytest.fixture
def _low_rate_limit(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    monkeypatch.setenv("TAP_RATE_LIMIT_PER_MINUTE", "3")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_health_endpoints_are_exempt_from_rate_limiting(
    client: AsyncClient, _low_rate_limit: None
) -> None:
    for _ in range(10):
        response = await client.get("/health")
        assert response.status_code == 200


async def test_exceeding_the_limit_returns_429(client: AsyncClient, _low_rate_limit: None) -> None:
    email = unique_email()
    responses = [
        await client.post("/auth/setup", json={"email": email, "password": PASSWORD})
        for _ in range(4)
    ]

    assert [r.status_code for r in responses[:3]] != [429, 429, 429]
    assert responses[-1].status_code == 429
    assert (
        responses[-1].json()["detail"]
        == "Too many requests. Please slow down and try again shortly."
    )


async def test_rate_limited_response_still_carries_cors_headers(
    client: AsyncClient, _low_rate_limit: None
) -> None:
    email = unique_email()
    headers = {"Origin": "http://localhost:5173"}
    for _ in range(3):
        await client.post(
            "/auth/setup", json={"email": email, "password": PASSWORD}, headers=headers
        )

    limited = await client.post(
        "/auth/setup", json={"email": email, "password": PASSWORD}, headers=headers
    )

    assert limited.status_code == 429
    assert limited.headers.get("access-control-allow-origin") == "http://localhost:5173"
