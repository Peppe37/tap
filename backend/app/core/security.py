"""Password hashing and JWT access/refresh token handling."""

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    return _create_token(
        user_id, TokenType.ACCESS, timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: str) -> str:
    settings = get_settings()
    return _create_token(
        user_id, TokenType.REFRESH, timedelta(days=settings.refresh_token_expire_days)
    )


class InvalidTokenError(Exception):
    pass


def decode_token(token: str, *, expected_type: TokenType) -> str:
    """Return the subject (user id) encoded in the token, or raise InvalidTokenError."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    if payload.get("type") != expected_type.value:
        raise InvalidTokenError(f"expected token type {expected_type.value!r}")

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise InvalidTokenError("token missing subject")
    return subject
