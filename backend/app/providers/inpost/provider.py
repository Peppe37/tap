"""InPost ShipX tracking adapter.

Calls the tracking-only endpoint InPost exposes without requiring the OAuth2 credentials that
the full ShipX business API needs (confirmed against community reverse-engineering reports; see
docs/ADDING_A_PROVIDER.md for sources and caveats). Because this endpoint is not part of the
documented, authenticated ShipX API, InPost may change or restrict it without notice.

InPost runs a separate ShipX instance per country it operates in. This was originally written
against the Polish instance (api-shipx-pl.easypack24.net) only; a real Italian domestic shipment
(locker-to-locker, both machines physically in Italy) 404'd there despite inpost.it's own
tracking page showing full history for the same number -- inspecting that page's embedded Drupal
settings revealed it actually queries api-shipx-it.easypack24.net. There is no way to tell which
country's instance a given tracking number belongs to from its format alone, so we try the
Italian instance first (this project's primary user base) and fall back to the Polish one on a
404 only. Other error codes (rate limit, server error) are provider-wide, not host-specific, and
propagate immediately without trying the second host.
"""

from datetime import datetime
from typing import Any, ClassVar

import httpx

from app.models.enums import PackageStatus, ProviderKind
from app.providers.base import (
    ProviderInvalidTrackingNumberError,
    ProviderRateLimitedError,
    ProviderTransientError,
    TrackingEventDTO,
    TrackingProvider,
    TrackingResult,
)
from app.providers.inpost.mapping import STATUS_MAP
from app.providers.registry import register_provider

TRACKING_HOSTS: tuple[str, ...] = (
    "https://api-shipx-it.easypack24.net",
    "https://api-shipx-pl.easypack24.net",
)
TRACKING_PATH_TEMPLATE = "/v1/tracking/{tracking_number}"
REQUEST_TIMEOUT_SECONDS = 10.0


@register_provider
class InPostProvider(TrackingProvider):
    code: ClassVar[str] = "inpost_official"
    display_name: ClassVar[str] = "InPost"
    kind: ClassVar[ProviderKind] = ProviderKind.OFFICIAL_API
    supported_carrier_codes: ClassVar[frozenset[str]] = frozenset({"inpost"})
    requires_credentials: ClassVar[bool] = False

    async def fetch(
        self,
        tracking_number: str,
        carrier_code: str,
        credentials: dict[str, str] | None,
        extra_params: dict[str, str] | None = None,
    ) -> TrackingResult:
        path = TRACKING_PATH_TEMPLATE.format(tracking_number=tracking_number)

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            for host in TRACKING_HOSTS:
                try:
                    response = await client.get(f"{host}{path}")
                except httpx.TimeoutException as exc:
                    raise ProviderTransientError("InPost tracking request timed out") from exc
                except httpx.TransportError as exc:
                    raise ProviderTransientError(f"InPost tracking request failed: {exc}") from exc

                if response.status_code == 404:
                    continue  # not on this country's ShipX instance -- try the next one
                if response.status_code == 429:
                    raise ProviderRateLimitedError(
                        "InPost tracking endpoint rate-limited this request"
                    )
                if response.status_code >= 500:
                    raise ProviderTransientError(
                        f"InPost tracking endpoint returned {response.status_code}"
                    )
                response.raise_for_status()
                return self._parse(response.json())

        raise ProviderInvalidTrackingNumberError(
            f"InPost has no shipment for tracking number {tracking_number!r}"
        )

    def _parse(self, payload: dict[str, Any]) -> TrackingResult:
        overall_status = STATUS_MAP.get(payload.get("status", ""), PackageStatus.UNKNOWN)

        events: list[TrackingEventDTO] = []
        for entry in payload.get("tracking_details", []):
            raw_status = entry.get("status", "")
            occurred_at = _parse_datetime(entry.get("datetime"))
            if occurred_at is None:
                continue
            location = entry.get("location")
            location_str = location.get("name") if isinstance(location, dict) else location
            events.append(
                TrackingEventDTO(
                    occurred_at=occurred_at,
                    status=STATUS_MAP.get(raw_status, PackageStatus.UNKNOWN),
                    description=raw_status.replace("_", " ").capitalize() or "Status update",
                    location=location_str,
                    raw=entry,
                )
            )

        return TrackingResult(status=overall_status, events=events, raw=payload)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
