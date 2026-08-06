import pytest
from httpx import AsyncClient

from app.services import readiness


async def test_health_is_always_ok(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness_reports_200_when_everything_is_reachable(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def ok() -> bool:
        return True

    monkeypatch.setattr(readiness, "_check_database", ok)
    monkeypatch.setattr(readiness, "_check_redis", ok)

    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"ready": True, "checks": {"database": True, "redis": True}}


async def test_readiness_reports_503_when_a_dependency_is_down(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def ok() -> bool:
        return True

    async def down() -> bool:
        return False

    monkeypatch.setattr(readiness, "_check_database", ok)
    monkeypatch.setattr(readiness, "_check_redis", down)

    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"ready": False, "checks": {"database": True, "redis": False}}
