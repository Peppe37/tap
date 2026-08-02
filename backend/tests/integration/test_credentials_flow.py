import pytest
from httpx import AsyncClient

from app.providers.generic_aggregator.provider import SeventeenTrackProvider
from tests.integration.conftest import unique_email

PASSWORD = "correct-horse-battery"


async def _auth_headers(client: AsyncClient) -> dict[str, str]:
    email = unique_email()
    response = await client.post("/auth/setup", json={"email": email, "password": PASSWORD})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_credential_status_starts_unconfigured(client: AsyncClient) -> None:
    headers = await _auth_headers(client)

    response = await client.get("/providers/aggregator_17track/credential-status", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"provider_code": "aggregator_17track", "is_configured": False}


async def test_test_credential_rejects_provider_without_credentials(
    client: AsyncClient,
) -> None:
    headers = await _auth_headers(client)

    response = await client.post(
        "/providers/inpost_official/test-credential",
        json={"fields": {"api_key": "irrelevant"}},
        headers=headers,
    )

    assert response.status_code == 400


async def test_test_credential_reports_validity(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = await _auth_headers(client)

    async def fake_test_credentials(self, credentials):  # type: ignore[no-untyped-def]
        return credentials.get("api_key") == "good-key"

    monkeypatch.setattr(SeventeenTrackProvider, "test_credentials", fake_test_credentials)

    good = await client.post(
        "/providers/aggregator_17track/test-credential",
        json={"fields": {"api_key": "good-key"}},
        headers=headers,
    )
    bad = await client.post(
        "/providers/aggregator_17track/test-credential",
        json={"fields": {"api_key": "bad-key"}},
        headers=headers,
    )

    assert good.json() == {"is_valid": True}
    assert bad.json() == {"is_valid": False}


async def test_save_then_delete_credential_updates_status(client: AsyncClient) -> None:
    headers = await _auth_headers(client)

    save_response = await client.put(
        "/providers/aggregator_17track/credential",
        json={"fields": {"api_key": "my-secret-key"}},
        headers=headers,
    )
    assert save_response.status_code == 204

    status_after_save = await client.get(
        "/providers/aggregator_17track/credential-status", headers=headers
    )
    assert status_after_save.json()["is_configured"] is True

    delete_response = await client.delete(
        "/providers/aggregator_17track/credential", headers=headers
    )
    assert delete_response.status_code == 204

    status_after_delete = await client.get(
        "/providers/aggregator_17track/credential-status", headers=headers
    )
    assert status_after_delete.json()["is_configured"] is False


async def test_credentials_are_isolated_per_user(client: AsyncClient) -> None:
    owner_headers = await _auth_headers(client)
    await client.put(
        "/providers/aggregator_17track/credential",
        json={"fields": {"api_key": "owner-key"}},
        headers=owner_headers,
    )

    other_email = unique_email()
    await client.post(
        "/auth/users",
        json={"email": other_email, "password": PASSWORD},
        headers=owner_headers,
    )
    other_login = await client.post(
        "/auth/login", json={"email": other_email, "password": PASSWORD}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    other_status = await client.get(
        "/providers/aggregator_17track/credential-status", headers=other_headers
    )

    assert other_status.json()["is_configured"] is False
