from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.models.enums import PackageStatus
from app.providers.base import TrackingEventDTO, TrackingResult
from app.providers.inpost.provider import InPostProvider
from tests.integration.conftest import unique_email

PASSWORD = "correct-horse-battery"


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    email = unique_email()
    response = await client.post("/auth/setup", json={"email": email, "password": PASSWORD})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_create_and_list_package(client: AsyncClient) -> None:
    headers = await _auth_headers(client)

    response = await client.post(
        "/packages",
        json={
            "tracking_number": "60011234567890123456789012",
            "carrier_code": "inpost",
            "provider_code": "inpost_official",
            "shop_code": "aliexpress",
            "label": "Mechanical keyboard",
        },
        headers=headers,
    )
    assert response.status_code == 201
    package = response.json()
    assert package["status"] == "created"
    assert package["carrier"]["code"] == "inpost"
    assert package["shop"]["code"] == "aliexpress"
    assert package["events"] == []

    list_response = await client.get("/packages", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_create_package_rejects_provider_carrier_mismatch(client: AsyncClient) -> None:
    headers = await _auth_headers(client)

    response = await client.post(
        "/packages",
        json={
            "tracking_number": "AB123456789IT",
            "carrier_code": "brt",
            "provider_code": "inpost_official",
        },
        headers=headers,
    )

    assert response.status_code == 400


async def test_users_cannot_see_each_others_packages(client: AsyncClient) -> None:
    owner_headers = await _auth_headers(client)
    create_response = await client.post(
        "/packages",
        json={
            "tracking_number": "60011234567890123456789012",
            "carrier_code": "inpost",
            "provider_code": "inpost_official",
        },
        headers=owner_headers,
    )
    package_id = create_response.json()["id"]

    other_email = unique_email()
    other_login = await client.post(
        "/auth/users",
        json={"email": other_email, "password": PASSWORD},
        headers=owner_headers,
    )
    assert other_login.status_code == 201
    other_token = await client.post(
        "/auth/login", json={"email": other_email, "password": PASSWORD}
    )
    other_headers = {"Authorization": f"Bearer {other_token.json()['access_token']}"}

    response = await client.get(f"/packages/{package_id}", headers=other_headers)

    assert response.status_code == 404


async def test_update_and_delete_package(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    create_response = await client.post(
        "/packages",
        json={
            "tracking_number": "60011234567890123456789012",
            "carrier_code": "inpost",
            "provider_code": "inpost_official",
        },
        headers=headers,
    )
    package_id = create_response.json()["id"]

    patch_response = await client.patch(
        f"/packages/{package_id}",
        json={"label": "Renamed", "is_archived": True},
        headers=headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["label"] == "Renamed"
    assert patch_response.json()["is_archived"] is True

    delete_response = await client.delete(f"/packages/{package_id}", headers=headers)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/packages/{package_id}", headers=headers)
    assert get_response.status_code == 404


async def test_update_can_change_shop_and_clear_it(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    create_response = await client.post(
        "/packages",
        json={
            "tracking_number": "60011234567890123456789012",
            "carrier_code": "inpost",
            "provider_code": "inpost_official",
            "shop_code": "aliexpress",
        },
        headers=headers,
    )
    package_id = create_response.json()["id"]

    changed = await client.patch(
        f"/packages/{package_id}", json={"shop_code": "vinted"}, headers=headers
    )
    assert changed.json()["shop"]["code"] == "vinted"

    cleared = await client.patch(
        f"/packages/{package_id}", json={"shop_code": None}, headers=headers
    )
    assert cleared.json()["shop"] is None


async def test_update_rejects_incompatible_provider_carrier_combination(
    client: AsyncClient,
) -> None:
    headers = await _auth_headers(client)
    create_response = await client.post(
        "/packages",
        json={
            "tracking_number": "60011234567890123456789012",
            "carrier_code": "inpost",
            "provider_code": "inpost_official",
        },
        headers=headers,
    )
    package_id = create_response.json()["id"]

    response = await client.patch(
        f"/packages/{package_id}", json={"carrier_code": "brt"}, headers=headers
    )

    assert response.status_code == 400


async def test_update_retargeting_tracking_number_resets_status_and_events(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_fetch(self, tracking_number, carrier_code, credentials, extra_params=None):  # type: ignore[no-untyped-def]
        return TrackingResult(
            status=PackageStatus.DELIVERED,
            events=[
                TrackingEventDTO(
                    occurred_at=datetime(2026, 7, 20, 9, 0, tzinfo=UTC),
                    status=PackageStatus.DELIVERED,
                    description="Delivered",
                )
            ],
        )

    monkeypatch.setattr(InPostProvider, "fetch", fake_fetch)

    headers = await _auth_headers(client)
    create_response = await client.post(
        "/packages",
        json={
            "tracking_number": "60011234567890123456789012",
            "carrier_code": "inpost",
            "provider_code": "inpost_official",
        },
        headers=headers,
    )
    package_id = create_response.json()["id"]
    refreshed = await client.post(f"/packages/{package_id}/refresh", headers=headers)
    assert refreshed.json()["status"] == "delivered"
    assert len(refreshed.json()["events"]) == 1

    updated = await client.patch(
        f"/packages/{package_id}",
        json={"tracking_number": "60019999999999999999999999"},
        headers=headers,
    )

    assert updated.status_code == 200
    assert updated.json()["tracking_number"] == "60019999999999999999999999"
    assert updated.json()["status"] == "created"
    assert updated.json()["events"] == []
    assert updated.json()["last_checked_at"] is None


async def test_update_resubmitting_unchanged_targeting_fields_preserves_history(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression test: the edit form resubmits tracking_number/carrier_code/provider_code on
    every save, even when the user only changed the label. That must not wipe history -- only an
    actual change to one of those fields should reset tracking (see the previous test)."""

    async def fake_fetch(self, tracking_number, carrier_code, credentials, extra_params=None):  # type: ignore[no-untyped-def]
        return TrackingResult(
            status=PackageStatus.DELIVERED,
            events=[
                TrackingEventDTO(
                    occurred_at=datetime(2026, 7, 20, 9, 0, tzinfo=UTC),
                    status=PackageStatus.DELIVERED,
                    description="Delivered",
                )
            ],
        )

    monkeypatch.setattr(InPostProvider, "fetch", fake_fetch)

    headers = await _auth_headers(client)
    create_response = await client.post(
        "/packages",
        json={
            "tracking_number": "60011234567890123456789012",
            "carrier_code": "inpost",
            "provider_code": "inpost_official",
        },
        headers=headers,
    )
    package_id = create_response.json()["id"]
    await client.post(f"/packages/{package_id}/refresh", headers=headers)

    updated = await client.patch(
        f"/packages/{package_id}",
        json={
            "tracking_number": "60011234567890123456789012",
            "carrier_code": "inpost",
            "provider_code": "inpost_official",
            "shop_code": None,
            "label": "Solo rinomina",
            "extra_params": None,
        },
        headers=headers,
    )

    assert updated.status_code == 200
    assert updated.json()["label"] == "Solo rinomina"
    assert updated.json()["status"] == "delivered"
    assert len(updated.json()["events"]) == 1


async def test_update_persists_extra_params(client: AsyncClient) -> None:
    headers = await _auth_headers(client)
    create_response = await client.post(
        "/packages",
        json={
            "tracking_number": "58438531",
            "carrier_code": "mondial_relay",
            "provider_code": "aggregator_17track",
        },
        headers=headers,
    )
    package_id = create_response.json()["id"]
    assert create_response.json()["extra_params"] is None

    updated = await client.patch(
        f"/packages/{package_id}",
        json={"extra_params": {"destination_postal_code": "20100"}},
        headers=headers,
    )

    assert updated.json()["extra_params"] == {"destination_postal_code": "20100"}


async def test_refresh_persists_status_and_events_without_duplicating_on_repeat(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    canned_result = TrackingResult(
        status=PackageStatus.OUT_FOR_DELIVERY,
        events=[
            TrackingEventDTO(
                occurred_at=datetime(2026, 7, 20, 9, 0, tzinfo=UTC),
                status=PackageStatus.IN_TRANSIT,
                description="Adopted at sorting center",
                location="Warszawa",
            ),
            TrackingEventDTO(
                occurred_at=datetime(2026, 7, 21, 8, 0, tzinfo=UTC),
                status=PackageStatus.OUT_FOR_DELIVERY,
                description="Out for delivery",
                location="Krakow",
            ),
        ],
    )

    async def fake_fetch(
        self: InPostProvider,
        tracking_number: str,
        carrier_code: str,
        credentials: dict | None,
        extra_params: dict | None = None,
    ) -> TrackingResult:
        return canned_result

    monkeypatch.setattr(InPostProvider, "fetch", fake_fetch)

    headers = await _auth_headers(client)
    create_response = await client.post(
        "/packages",
        json={
            "tracking_number": "60011234567890123456789012",
            "carrier_code": "inpost",
            "provider_code": "inpost_official",
        },
        headers=headers,
    )
    package_id = create_response.json()["id"]

    first_refresh = await client.post(f"/packages/{package_id}/refresh", headers=headers)
    assert first_refresh.status_code == 200
    assert first_refresh.json()["status"] == "out_for_delivery"
    assert len(first_refresh.json()["events"]) == 2

    second_refresh = await client.post(f"/packages/{package_id}/refresh", headers=headers)
    assert second_refresh.status_code == 200
    assert len(second_refresh.json()["events"]) == 2
