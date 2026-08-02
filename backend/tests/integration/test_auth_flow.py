from httpx import AsyncClient

from app.core.security import TokenType, decode_token
from tests.integration.conftest import unique_email

ADMIN_PASSWORD = "correct-horse-battery"


async def _bootstrap_admin(client: AsyncClient) -> dict[str, str]:
    email = unique_email()
    response = await client.post("/auth/setup", json={"email": email, "password": ADMIN_PASSWORD})
    assert response.status_code == 201
    return {"email": email, **response.json()}


async def test_setup_status_reports_needs_setup_when_no_users(client: AsyncClient) -> None:
    response = await client.get("/auth/setup-status")

    assert response.status_code == 200
    assert response.json() == {"needs_setup": True}


async def test_setup_creates_admin_and_disables_further_setup(client: AsyncClient) -> None:
    tokens = await _bootstrap_admin(client)

    status_response = await client.get("/auth/setup-status")
    assert status_response.json() == {"needs_setup": False}

    second_attempt = await client.post(
        "/auth/setup", json={"email": unique_email(), "password": ADMIN_PASSWORD}
    )
    assert second_attempt.status_code == 409

    me_response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == tokens["email"]
    assert me_response.json()["is_admin"] is True


async def test_login_succeeds_with_correct_credentials(client: AsyncClient) -> None:
    tokens = await _bootstrap_admin(client)

    response = await client.post(
        "/auth/login", json={"email": tokens["email"], "password": ADMIN_PASSWORD}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    tokens = await _bootstrap_admin(client)

    response = await client.post(
        "/auth/login", json={"email": tokens["email"], "password": "not-the-password"}
    )

    assert response.status_code == 401


async def test_refresh_issues_usable_access_token(client: AsyncClient) -> None:
    tokens = await _bootstrap_admin(client)
    original_user_id = decode_token(tokens["access_token"], expected_type=TokenType.ACCESS)

    response = await client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    new_access_token = response.json()["access_token"]
    assert decode_token(new_access_token, expected_type=TokenType.ACCESS) == original_user_id


async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/auth/me")

    assert response.status_code == 401


async def test_admin_can_create_additional_user_but_non_admin_cannot(client: AsyncClient) -> None:
    admin_tokens = await _bootstrap_admin(client)
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

    new_email = unique_email()
    create_response = await client.post(
        "/auth/users",
        json={"email": new_email, "password": "another-strong-pass", "is_admin": False},
        headers=admin_headers,
    )
    assert create_response.status_code == 201

    member_login = await client.post(
        "/auth/login", json={"email": new_email, "password": "another-strong-pass"}
    )
    member_headers = {"Authorization": f"Bearer {member_login.json()['access_token']}"}

    forbidden_response = await client.post(
        "/auth/users",
        json={"email": unique_email(), "password": "another-strong-pass"},
        headers=member_headers,
    )
    assert forbidden_response.status_code == 403
