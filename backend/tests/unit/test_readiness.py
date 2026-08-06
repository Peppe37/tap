import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.services import readiness


class _FakeRedis:
    def __init__(self, *, fails: bool) -> None:
        self._fails = fails

    def ping(self) -> bool:
        if self._fails:
            raise RedisConnectionError("connection refused")
        return True

    def close(self) -> None:
        pass


async def test_check_redis_true_when_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(readiness.Redis, "from_url", lambda *a, **kw: _FakeRedis(fails=False))

    assert await readiness._check_redis() is True


async def test_check_redis_false_when_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(readiness.Redis, "from_url", lambda *a, **kw: _FakeRedis(fails=True))

    assert await readiness._check_redis() is False


async def test_check_readiness_combines_both_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_database() -> bool:
        return True

    async def fake_redis() -> bool:
        return False

    monkeypatch.setattr(readiness, "_check_database", fake_database)
    monkeypatch.setattr(readiness, "_check_redis", fake_redis)

    result = await readiness.check_readiness()

    assert result.database is True
    assert result.redis is False
    assert result.ready is False
