from collections.abc import Generator

import httpx
import pytest
import respx

from app.core.config import get_settings
from app.services import update_check


class _FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    def get(self, key: str) -> bytes | None:
        return self._store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value.encode()


@pytest.fixture(autouse=True)
def _fake_redis(monkeypatch: pytest.MonkeyPatch) -> _FakeRedis:
    fake = _FakeRedis()
    monkeypatch.setattr(update_check, "_redis", lambda: fake)
    return fake


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Generator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _github_url() -> str:
    return f"https://api.github.com/repos/{get_settings().github_repo}/releases/latest"


async def test_get_latest_release_tag_caches_result(respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get(_github_url()).mock(
        return_value=httpx.Response(200, json={"tag_name": "v0.2.0"})
    )

    first = await update_check.get_latest_release_tag()
    second = await update_check.get_latest_release_tag()

    assert first == "v0.2.0"
    assert second == "v0.2.0"
    assert route.call_count == 1


async def test_get_latest_release_tag_returns_none_on_error(respx_mock: respx.MockRouter) -> None:
    respx_mock.get(_github_url()).mock(return_value=httpx.Response(500))

    assert await update_check.get_latest_release_tag() is None


async def test_check_for_update_detects_newer_version(
    respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TAP_APP_VERSION", "0.1.0")
    respx_mock.get(_github_url()).mock(
        return_value=httpx.Response(200, json={"tag_name": "v0.2.0"})
    )

    latest_version, update_available = await update_check.check_for_update()

    assert latest_version == "v0.2.0"
    assert update_available is True


async def test_check_for_update_reports_up_to_date(
    respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TAP_APP_VERSION", "0.2.0")
    respx_mock.get(_github_url()).mock(
        return_value=httpx.Response(200, json={"tag_name": "v0.2.0"})
    )

    _, update_available = await update_check.check_for_update()

    assert update_available is False


async def test_check_for_update_skips_comparison_for_dev_builds(
    respx_mock: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TAP_APP_VERSION", "dev")
    respx_mock.get(_github_url()).mock(
        return_value=httpx.Response(200, json={"tag_name": "v0.2.0"})
    )

    _, update_available = await update_check.check_for_update()

    assert update_available is False
