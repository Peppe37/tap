import pytest

from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_plaintext_and_verifies() -> None:
    hashed = hash_password("correct-horse-battery")

    assert hashed != "correct-horse-battery"
    assert verify_password("correct-horse-battery", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_and_refresh_tokens_round_trip() -> None:
    user_id = "5b1a6c1e-7f3f-4a3e-9c3a-1f7c9b3d9a11"

    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)

    assert decode_token(access, expected_type=TokenType.ACCESS) == user_id
    assert decode_token(refresh, expected_type=TokenType.REFRESH) == user_id


def test_decode_token_rejects_wrong_type() -> None:
    access = create_access_token("some-user-id")

    with pytest.raises(InvalidTokenError):
        decode_token(access, expected_type=TokenType.REFRESH)


def test_decode_token_rejects_garbage() -> None:
    with pytest.raises(InvalidTokenError):
        decode_token("not-a-real-token", expected_type=TokenType.ACCESS)
