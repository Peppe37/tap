from collections.abc import Generator

import httpx
import pytest
import respx
from httpx import AsyncClient

from app.core.config import get_settings
from app.services import update_check
from tests.integration.conftest import unique_email

PASSWORD = "correct-horse-battery"


@pytest.fixture
def _reset_settings_cache() -> Generator[None]:
    yield
    get_settings.cache_clear()


class _FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    def get(self, key: str) -> bytes | None:
        return self._store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value.encode()


@pytest.fixture(autouse=True)
def _fake_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(update_check, "_redis", lambda: _FakeRedis())


def _github_url() -> str:
    return f"https://api.github.com/repos/{get_settings().github_repo}/releases/latest"


async def test_update_status_requires_admin(client: AsyncClient) -> None:
    email = unique_email()
    admin_response = await client.post("/auth/setup", json={"email": email, "password": PASSWORD})
    admin_headers = {"Authorization": f"Bearer {admin_response.json()['access_token']}"}

    member_email = unique_email()
    await client.post(
        "/auth/users",
        json={"email": member_email, "password": PASSWORD, "is_admin": False},
        headers=admin_headers,
    )
    member_login = await client.post(
        "/auth/login", json={"email": member_email, "password": PASSWORD}
    )
    member_headers = {"Authorization": f"Bearer {member_login.json()['access_token']}"}

    forbidden = await client.get("/system/update-status", headers=member_headers)
    assert forbidden.status_code == 403


async def test_update_status_reports_available_update(
    client: AsyncClient,
    respx_mock: respx.MockRouter,
    monkeypatch: pytest.MonkeyPatch,
    _reset_settings_cache: None,
) -> None:
    monkeypatch.setenv("TAP_APP_VERSION", "0.1.0")
    get_settings.cache_clear()
    respx_mock.get(_github_url()).mock(
        return_value=httpx.Response(200, json={"tag_name": "v99.0.0"})
    )
    email = unique_email()
    admin_response = await client.post("/auth/setup", json={"email": email, "password": PASSWORD})
    admin_headers = {"Authorization": f"Bearer {admin_response.json()['access_token']}"}

    response = await client.get("/system/update-status", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["latest_version"] == "v99.0.0"
    assert body["update_available"] is True
    assert body["release_url"] == "https://github.com/Peppe37/tap/releases/tag/v99.0.0"
