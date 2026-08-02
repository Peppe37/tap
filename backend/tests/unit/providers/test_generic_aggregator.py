import json
from pathlib import Path

import httpx
import pytest
import respx

from app.core.config import get_settings
from app.models.enums import PackageStatus
from app.providers.base import ProviderAuthenticationError, ProviderNotConfiguredError
from app.providers.generic_aggregator.provider import SeventeenTrackProvider

FIXTURES = Path(__file__).parent.parent / "fixtures" / "providers" / "aggregator_17track"
BASE_URL = get_settings().aggregator_base_url


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


async def test_fetch_raises_when_not_configured() -> None:
    with pytest.raises(ProviderNotConfiguredError):
        await SeventeenTrackProvider().fetch("770123456789", "brt", credentials=None)


async def test_fetch_parses_delivered_shipment(respx_mock: respx.MockRouter) -> None:
    respx_mock.post(f"{BASE_URL}/register").mock(
        return_value=httpx.Response(200, json={"code": 0, "data": {"accepted": [], "rejected": []}})
    )
    respx_mock.post(f"{BASE_URL}/gettrackinfo").mock(
        return_value=httpx.Response(200, json=_load_fixture("gettrackinfo_delivered.json"))
    )

    result = await SeventeenTrackProvider().fetch(
        "770123456789", "brt", credentials={"api_key": "test-key"}
    )

    assert result.status is PackageStatus.DELIVERED
    assert len(result.events) == 4
    assert result.events[0].status is PackageStatus.DELIVERED
    assert result.events[-1].status is PackageStatus.CREATED


async def test_fetch_raises_on_invalid_api_key(respx_mock: respx.MockRouter) -> None:
    respx_mock.post(f"{BASE_URL}/register").mock(return_value=httpx.Response(401))

    with pytest.raises(ProviderAuthenticationError):
        await SeventeenTrackProvider().fetch(
            "770123456789", "brt", credentials={"api_key": "wrong-key"}
        )


async def test_test_credentials_returns_false_on_invalid_key(respx_mock: respx.MockRouter) -> None:
    respx_mock.post(f"{BASE_URL}/getquota").mock(return_value=httpx.Response(401))

    is_valid = await SeventeenTrackProvider().test_credentials({"api_key": "wrong-key"})

    assert is_valid is False


async def test_test_credentials_returns_true_on_valid_key(respx_mock: respx.MockRouter) -> None:
    respx_mock.post(f"{BASE_URL}/getquota").mock(return_value=httpx.Response(200, json={"code": 0}))

    is_valid = await SeventeenTrackProvider().test_credentials({"api_key": "good-key"})

    assert is_valid is True


async def test_fetch_includes_carrier_id_for_mapped_carriers(respx_mock: respx.MockRouter) -> None:
    register_route = respx_mock.post(f"{BASE_URL}/register").mock(
        return_value=httpx.Response(200, json={"code": 0, "data": {"accepted": [], "rejected": []}})
    )
    respx_mock.post(f"{BASE_URL}/gettrackinfo").mock(
        return_value=httpx.Response(200, json=_load_fixture("gettrackinfo_delivered.json"))
    )

    # A regression test for a real bug: 17TRACK cannot auto-detect Mondial Relay's short,
    # generic-looking tracking numbers and rejects registration outright without an explicit
    # carrier id ("Carrier cannot be detected").
    await SeventeenTrackProvider().fetch(
        "58438531", "mondial_relay", credentials={"api_key": "test-key"}
    )

    sent_body = json.loads(register_route.calls[0].request.content)
    assert sent_body == [{"number": "58438531", "carrier": 100304}]


async def test_fetch_omits_carrier_id_for_unmapped_carriers(respx_mock: respx.MockRouter) -> None:
    register_route = respx_mock.post(f"{BASE_URL}/register").mock(
        return_value=httpx.Response(200, json={"code": 0, "data": {"accepted": [], "rejected": []}})
    )
    respx_mock.post(f"{BASE_URL}/gettrackinfo").mock(
        return_value=httpx.Response(200, json=_load_fixture("gettrackinfo_delivered.json"))
    )

    await SeventeenTrackProvider().fetch(
        "770123456789", "some_unmapped_carrier", credentials={"api_key": "test-key"}
    )

    sent_body = json.loads(register_route.calls[0].request.content)
    assert sent_body == [{"number": "770123456789"}]


async def test_fetch_forwards_destination_postal_code(
    respx_mock: respx.MockRouter,
) -> None:
    register_route = respx_mock.post(f"{BASE_URL}/register").mock(
        return_value=httpx.Response(200, json={"code": 0, "data": {"accepted": [], "rejected": []}})
    )
    respx_mock.post(f"{BASE_URL}/gettrackinfo").mock(
        return_value=httpx.Response(200, json=_load_fixture("gettrackinfo_delivered.json"))
    )

    await SeventeenTrackProvider().fetch(
        "58438531",
        "mondial_relay",
        credentials={"api_key": "test-key"},
        extra_params={"destination_postal_code": "75001"},
    )

    sent_body = json.loads(register_route.calls[0].request.content)
    assert sent_body == [
        {"number": "58438531", "carrier": 100304, "destination_postal_code": "75001"}
    ]
