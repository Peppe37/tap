import json
from pathlib import Path

import httpx
import pytest
import respx

from app.models.enums import PackageStatus
from app.providers.base import ProviderInvalidTrackingNumberError
from app.providers.poste_it.provider import TRACKING_URL, PosteItalianeProvider

FIXTURES = Path(__file__).parent.parent / "fixtures" / "providers" / "poste_italiane"


def _load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text())


async def test_fetch_parses_delivered_shipment(respx_mock: respx.MockRouter) -> None:
    respx_mock.post(TRACKING_URL).mock(
        return_value=httpx.Response(200, json=_load_fixture("delivered.json"))
    )

    result = await PosteItalianeProvider().fetch("AB123456789IT", "poste_it", credentials=None)

    assert result.status is PackageStatus.DELIVERED
    assert len(result.events) == 4
    assert result.events[0].status is PackageStatus.DELIVERED
    assert result.events[0].location == "ROMA"


async def test_fetch_raises_when_error_reported(respx_mock: respx.MockRouter) -> None:
    respx_mock.post(TRACKING_URL).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "idTracciatura": "UNKNOWN123",
                    "sintesiStato": None,
                    "descrizioneErrore": "Spedizione non trovata",
                    "listaMovimenti": [],
                }
            ],
        )
    )

    with pytest.raises(ProviderInvalidTrackingNumberError):
        await PosteItalianeProvider().fetch("UNKNOWN123", "poste_it", credentials=None)
