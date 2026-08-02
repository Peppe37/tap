import pytest

from app.workers import tasks


class _FakeRedis:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key]

    def expire(self, key: str, seconds: int) -> None:
        pass


def test_rate_limit_not_exceeded_below_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeRedis()
    monkeypatch.setattr(tasks, "_redis", lambda: fake)

    for _ in range(5):
        assert tasks._provider_rate_limit_exceeded("inpost_official", max_per_minute=5) is False


def test_rate_limit_exceeded_once_threshold_crossed(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeRedis()
    monkeypatch.setattr(tasks, "_redis", lambda: fake)

    for _ in range(5):
        tasks._provider_rate_limit_exceeded("aggregator_17track", max_per_minute=5)

    assert tasks._provider_rate_limit_exceeded("aggregator_17track", max_per_minute=5) is True


def test_rate_limit_is_tracked_independently_per_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeRedis()
    monkeypatch.setattr(tasks, "_redis", lambda: fake)

    for _ in range(3):
        tasks._provider_rate_limit_exceeded("provider_a", max_per_minute=3)

    assert tasks._provider_rate_limit_exceeded("provider_a", max_per_minute=3) is True
    assert tasks._provider_rate_limit_exceeded("provider_b", max_per_minute=3) is False
