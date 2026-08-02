"""Poste Italiane tracking adapter.

Poste Italiane has no documented public tracking API. This adapter calls the same internal REST
endpoint used by the "Dove Quando" widget on poste.it (confirmed against community
reverse-engineering of that widget; see docs/ADDING_A_PROVIDER.md). Being unofficial, it may
change or start blocking non-browser clients without notice -- this is the trade-off of a
scraper-kind provider, and why it exists alongside real API-backed adapters rather than as the
only option.
"""

from datetime import UTC, datetime
from typing import Any, ClassVar

import httpx

from app.models.enums import ProviderKind
from app.providers.base import (
    ProviderInvalidTrackingNumberError,
    ProviderRateLimitedError,
    ProviderTransientError,
    TrackingEventDTO,
    TrackingProvider,
    TrackingResult,
)
from app.providers.poste_it.parser import classify
from app.providers.registry import register_provider

TRACKING_URL = "https://www.poste.it/online/dovequando/DQ-REST/ricercamultipla"
REQUEST_TIMEOUT_SECONDS = 10.0
_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.poste.it/cerca/index.html",
    "Origin": "https://www.poste.it",
}


@register_provider
class PosteItalianeProvider(TrackingProvider):
    code: ClassVar[str] = "poste_it_scraper"
    display_name: ClassVar[str] = "Poste Italiane"
    kind: ClassVar[ProviderKind] = ProviderKind.SCRAPER
    supported_carrier_codes: ClassVar[frozenset[str]] = frozenset({"poste_it"})
    requires_credentials: ClassVar[bool] = False

    async def fetch(
        self,
        tracking_number: str,
        carrier_code: str,
        credentials: dict[str, str] | None,
        extra_params: dict[str, str] | None = None,
    ) -> TrackingResult:
        body = {"tipoRichiedente": "WEB", "listaCodici": [tracking_number]}

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            try:
                response = await client.post(TRACKING_URL, json=body, headers=_HEADERS)
            except httpx.TimeoutException as exc:
                raise ProviderTransientError("Poste Italiane tracking request timed out") from exc
            except httpx.TransportError as exc:
                raise ProviderTransientError(f"Poste Italiane request failed: {exc}") from exc

        if response.status_code == 429:
            raise ProviderRateLimitedError(
                "Poste Italiane tracking endpoint rate-limited this request"
            )
        if response.status_code >= 500:
            raise ProviderTransientError(f"Poste Italiane endpoint returned {response.status_code}")
        response.raise_for_status()

        shipments = response.json()
        if not isinstance(shipments, list) or not shipments:
            raise ProviderInvalidTrackingNumberError(
                f"Poste Italiane returned no data for {tracking_number!r}"
            )

        shipment = next(
            (s for s in shipments if s.get("idTracciatura") == tracking_number), shipments[0]
        )
        if shipment.get("descrizioneErrore"):
            raise ProviderInvalidTrackingNumberError(
                f"Poste Italiane: {shipment['descrizioneErrore']}"
            )

        return self._parse(shipment)

    def _parse(self, shipment: dict[str, Any]) -> TrackingResult:
        overall_status = classify(shipment.get("sintesiStato"))

        events: list[TrackingEventDTO] = []
        for movement in shipment.get("listaMovimenti", []):
            occurred_at = _parse_epoch_millis(movement.get("dataOra"))
            description = movement.get("statoLavorazione") or "Aggiornamento stato"
            if occurred_at is None:
                continue
            events.append(
                TrackingEventDTO(
                    occurred_at=occurred_at,
                    status=classify(description),
                    description=description,
                    location=movement.get("luogo") or None,
                    raw=movement,
                )
            )
        events.sort(key=lambda e: e.occurred_at, reverse=True)

        return TrackingResult(status=overall_status, events=events, raw=shipment)


def _parse_epoch_millis(value: int | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1000, tz=UTC)
