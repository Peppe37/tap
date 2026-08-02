"""Checks GitHub Releases for a newer tap version than the one currently running -- an update
notification similar to Uptime Kuma's. The result is cached in Redis so the frontend can poll a
cheap local endpoint instead of hitting GitHub's API (unauthenticated, 60 requests/hour per IP)
on every page load.
"""

import re
from typing import cast

import httpx
from redis import Redis

from app.core.config import get_settings

CACHE_KEY = "tap:update_check:latest_release"
CACHE_TTL_SECONDS = 6 * 60 * 60
REQUEST_TIMEOUT_SECONDS = 5.0
_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")


def _redis() -> Redis:
    return Redis.from_url(get_settings().redis_url)


def _parse_semver(tag: str) -> tuple[int, int, int] | None:
    match = _SEMVER_RE.match(tag)
    if match is None:
        return None
    major, minor, patch = match.groups()
    return (int(major), int(minor), int(patch))


async def _fetch_latest_release_tag() -> str | None:
    settings = get_settings()
    url = f"https://api.github.com/repos/{settings.github_repo}/releases/latest"
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        try:
            response = await client.get(url, headers={"Accept": "application/vnd.github+json"})
        except httpx.HTTPError:
            return None
    if response.status_code != 200:
        return None
    tag = response.json().get("tag_name")
    return tag if isinstance(tag, str) else None


async def get_latest_release_tag() -> str | None:
    """Cache-first lookup; ``None`` means either "checked, no release found" or "check failed"
    -- both are treated the same by the caller (nothing to report)."""
    redis = _redis()
    cached = cast(bytes | None, redis.get(CACHE_KEY))
    if cached is not None:
        value = cached.decode()
        return value or None

    tag = await _fetch_latest_release_tag()
    redis.set(CACHE_KEY, tag or "", ex=CACHE_TTL_SECONDS)
    return tag


async def check_for_update() -> tuple[str, bool]:
    """Returns (latest_tag_or_current_version, update_available)."""
    settings = get_settings()
    latest_tag = await get_latest_release_tag()
    if latest_tag is None:
        return settings.app_version, False

    current = _parse_semver(settings.app_version)
    latest = _parse_semver(latest_tag)
    if current is None or latest is None:
        # Can't compare (e.g. running "dev" outside the release pipeline) -- nothing to report.
        return latest_tag, False

    return latest_tag, latest > current
