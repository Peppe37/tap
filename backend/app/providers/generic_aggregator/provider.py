"""17TRACK aggregator adapter.

A fallback for any carrier without a dedicated official/scraper adapter. Requires the user's own
17TRACK API key (see the ``setup_guide`` seeded for this provider, rendered by the frontend's
guided "Connections" screen) -- this is a metered third-party service, not something the project
can proxy for every self-hoster for free.

Reference: 17TRACK API v2.x (https://asset.17track.net/api/document/v2.2_en/index.html).
"""

from datetime import datetime
from typing import Any, ClassVar

import httpx

from app.core.config import get_settings
from app.models.enums import PackageStatus, ProviderKind
from app.providers.base import (
    ProviderAuthenticationError,
    ProviderInvalidTrackingNumberError,
    ProviderNotConfiguredError,
    ProviderRateLimitedError,
    ProviderTransientError,
    TrackingEventDTO,
    TrackingProvider,
    TrackingResult,
)
from app.providers.generic_aggregator.carrier_codes import seventeen_track_carrier_id
from app.providers.generic_aggregator.mapping import STATUS_MAP
from app.providers.registry import register_provider

REQUEST_TIMEOUT_SECONDS = 15.0


@register_provider
class SeventeenTrackProvider(TrackingProvider):
    code: ClassVar[str] = "aggregator_17track"
    display_name: ClassVar[str] = "17TRACK"
    kind: ClassVar[ProviderKind] = ProviderKind.AGGREGATOR
    supports_all_carriers: ClassVar[bool] = True
    requires_credentials: ClassVar[bool] = True

    def _base_url(self) -> str:
        return get_settings().aggregator_base_url.rstrip("/")

    def _headers(self, credentials: dict[str, str]) -> dict[str, str]:
        api_key = credentials.get("api_key")
        if not api_key:
            raise ProviderNotConfiguredError("17TRACK requires an 'api_key' credential")
        return {"17token": api_key, "Content-Type": "application/json"}

    async def fetch(
        self,
        tracking_number: str,
        carrier_code: str,
        credentials: dict[str, str] | None,
        extra_params: dict[str, str] | None = None,
    ) -> TrackingResult:
        if not credentials:
            raise ProviderNotConfiguredError(
                "17TRACK requires the user to configure an API key before use"
            )
        headers = self._headers(credentials)
        item: dict[str, Any] = {"number": tracking_number}
        carrier_id = seventeen_track_carrier_id(carrier_code)
        if carrier_id is not None:
            item["carrier"] = carrier_id
        postal_code = (extra_params or {}).get("destination_postal_code")
        if postal_code:
            # Some carriers (e.g. Mondial Relay) reject registration outright without this --
            # it's a distinct top-level field, not the generic `param` one the API docs mention.
            item["destination_postal_code"] = postal_code

        async with httpx.AsyncClient(
            base_url=self._base_url(), timeout=REQUEST_TIMEOUT_SECONDS, headers=headers
        ) as client:
            # Registration is idempotent enrolment for continuous tracking; a rejection here
            # most commonly means the number is already registered, which is not fatal. The
            # authoritative signal of an unknown number is a rejection from gettrackinfo below.
            await self._post(client, "/register", [item])
            info_response = await self._post(client, "/gettrackinfo", [item])

        data = info_response.get("data", {})
        rejected = {item.get("number"): item for item in data.get("rejected", [])}
        if tracking_number in rejected and not data.get("accepted"):
            reason = rejected[tracking_number].get("error", {}).get("message", "unknown reason")
            raise ProviderInvalidTrackingNumberError(f"17TRACK rejected this number: {reason}")

        accepted = data.get("accepted", [])
        if not accepted:
            raise ProviderInvalidTrackingNumberError(
                f"17TRACK has no tracking data for {tracking_number!r}"
            )

        return self._parse(accepted[0].get("track_info", {}))

    async def test_credentials(self, credentials: dict[str, str]) -> bool:
        headers = self._headers(credentials)
        async with httpx.AsyncClient(
            base_url=self._base_url(), timeout=REQUEST_TIMEOUT_SECONDS, headers=headers
        ) as client:
            try:
                response = await client.post("/getquota", json={})
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                raise ProviderTransientError(f"17TRACK quota check failed: {exc}") from exc

        if response.status_code in (401, 403):
            return False
        if response.status_code == 429:
            raise ProviderRateLimitedError("17TRACK rate-limited the credential check")
        if response.status_code >= 500:
            raise ProviderTransientError(f"17TRACK returned {response.status_code}")
        response.raise_for_status()

        body = response.json()
        return int(body.get("code", -1)) == 0

    async def _post(
        self, client: httpx.AsyncClient, path: str, payload: list[dict[str, Any]]
    ) -> dict[str, Any]:
        try:
            response = await client.post(path, json=payload)
        except httpx.TimeoutException as exc:
            raise ProviderTransientError(f"17TRACK request to {path} timed out") from exc
        except httpx.TransportError as exc:
            raise ProviderTransientError(f"17TRACK request to {path} failed: {exc}") from exc

        if response.status_code in (401, 403):
            raise ProviderAuthenticationError("17TRACK rejected the configured API key")
        if response.status_code == 429:
            raise ProviderRateLimitedError("17TRACK rate-limited this request")
        if response.status_code >= 500:
            raise ProviderTransientError(f"17TRACK {path} returned {response.status_code}")
        response.raise_for_status()

        body: dict[str, Any] = response.json()
        code = body.get("code")
        if code not in (0, None):
            message = str(body.get("data", body)).lower()
            if "token" in message or "auth" in message:
                raise ProviderAuthenticationError(f"17TRACK authentication error: {body}")
            raise ProviderTransientError(f"17TRACK {path} returned error code {code}: {body}")
        return body

    def _parse(self, track_info: dict[str, Any]) -> TrackingResult:
        latest_status = track_info.get("latest_status", {})
        overall_status = STATUS_MAP.get(latest_status.get("status", ""), PackageStatus.UNKNOWN)

        events: list[TrackingEventDTO] = []
        seen: set[tuple[str | None, str]] = set()
        for provider_entry in track_info.get("tracking", {}).get("providers", []):
            for raw_event in provider_entry.get("events", []):
                occurred_at = _parse_event_time(raw_event)
                description = raw_event.get("description", "")
                key = (raw_event.get("time_iso"), description)
                if occurred_at is None or key in seen:
                    continue
                seen.add(key)
                events.append(
                    TrackingEventDTO(
                        occurred_at=occurred_at,
                        status=STATUS_MAP.get(raw_event.get("stage", ""), PackageStatus.UNKNOWN),
                        description=description or "Status update",
                        location=raw_event.get("location"),
                        raw=raw_event,
                    )
                )
        events.sort(key=lambda e: e.occurred_at, reverse=True)

        return TrackingResult(status=overall_status, events=events, raw=track_info)


def _parse_event_time(raw_event: dict[str, Any]) -> datetime | None:
    for key in ("time_iso", "time_utc"):
        value = raw_event.get(key)
        if not value:
            continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
    return None
