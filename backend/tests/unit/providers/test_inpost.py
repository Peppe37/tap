import json
from pathlib import Path

import httpx
import pytest
import respx

from app.models.enums import PackageStatus
from app.providers.base import ProviderInvalidTrackingNumberError, ProviderRateLimitedError
from app.providers.inpost.provider import TRACKING_HOSTS, TRACKING_PATH_TEMPLATE, InPostProvider

FIXTURES = Path(__file__).parent.parent / "fixtures" / "providers" / "inpost_official"
ITALIAN_HOST, POLISH_HOST = TRACKING_HOSTS


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def _path(tracking_number: str) -> str:
    return TRACKING_PATH_TEMPLATE.format(tracking_number=tracking_number)


async def test_fetch_parses_delivered_shipment_from_italian_host(
    respx_mock: respx.MockRouter,
) -> None:
    tracking_number = "60011234567890123456789012"
    respx_mock.get(f"{ITALIAN_HOST}{_path(tracking_number)}").mock(
        return_value=httpx.Response(200, json=_load_fixture("delivered.json"))
    )

    result = await InPostProvider().fetch(tracking_number, "inpost", credentials=None)

    assert result.status is PackageStatus.DELIVERED
    assert len(result.events) == 4
    assert result.events[-1].status is PackageStatus.DELIVERED
    assert result.events[-1].location == "Krakow, ul. Karmelicka - Paczkomat KRA01M"
    assert result.events[0].status is PackageStatus.IN_TRANSIT


async def test_fetch_falls_back_to_polish_host_when_not_on_italian_one(
    respx_mock: respx.MockRouter,
) -> None:
    tracking_number = "60011234567890123456789012"
    respx_mock.get(f"{ITALIAN_HOST}{_path(tracking_number)}").mock(return_value=httpx.Response(404))
    polish_route = respx_mock.get(f"{POLISH_HOST}{_path(tracking_number)}").mock(
        return_value=httpx.Response(200, json=_load_fixture("delivered.json"))
    )

    result = await InPostProvider().fetch(tracking_number, "inpost", credentials=None)

    assert result.status is PackageStatus.DELIVERED
    assert polish_route.called


async def test_fetch_raises_on_unknown_tracking_number(respx_mock: respx.MockRouter) -> None:
    tracking_number = "does-not-exist"
    for host in TRACKING_HOSTS:
        respx_mock.get(f"{host}{_path(tracking_number)}").mock(return_value=httpx.Response(404))

    with pytest.raises(ProviderInvalidTrackingNumberError):
        await InPostProvider().fetch(tracking_number, "inpost", credentials=None)


async def test_fetch_raises_on_rate_limit_without_trying_the_second_host(
    respx_mock: respx.MockRouter,
) -> None:
    tracking_number = "60011234567890123456789012"
    respx_mock.get(f"{ITALIAN_HOST}{_path(tracking_number)}").mock(return_value=httpx.Response(429))
    polish_route = respx_mock.get(f"{POLISH_HOST}{_path(tracking_number)}").mock(
        return_value=httpx.Response(200, json=_load_fixture("delivered.json"))
    )

    with pytest.raises(ProviderRateLimitedError):
        await InPostProvider().fetch(tracking_number, "inpost", credentials=None)

    assert not polish_route.called
