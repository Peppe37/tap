"""Identity endpoints: first-run admin bootstrap, login, token refresh, and (admin-only) user
management for a multi-user self-hosted instance."""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentAdmin, CurrentUser, DbSession
from app.core.security import (
    InvalidTokenError,
    TokenType,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    CreateUserRequest,
    LoginRequest,
    RefreshRequest,
    SetupRequest,
    SetupStatus,
    TokenPair,
)
from app.schemas.user import UserRead
from app.services.tokens import issue_token_pair

router = APIRouter(prefix="/auth", tags=["auth"])


async def _user_count(db: DbSession) -> int:
    return (await db.execute(select(func.count()).select_from(User))).scalar_one()


@router.get("/setup-status", response_model=SetupStatus)
async def setup_status(db: DbSession) -> SetupStatus:
    return SetupStatus(needs_setup=await _user_count(db) == 0)


@router.post("/setup", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def setup(payload: SetupRequest, db: DbSession) -> TokenPair:
    if await _user_count(db) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Setup has already been completed; ask an administrator for an account",
        )
    user = User(email=payload.email, hashed_password=hash_password(payload.password), is_admin=True)
    db.add(user)
    await db.commit()
    return issue_token_pair(user)


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, db: DbSession) -> TokenPair:
    user = (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    return issue_token_pair(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    try:
        user_id = decode_token(payload.refresh_token, expected_type=TokenType.REFRESH)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        ) from exc

    user = await db.get(User, uuid.UUID(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists"
        )
    return issue_token_pair(user)


@router.get("/me", response_model=UserRead)
async def me(user: CurrentUser) -> User:
    return user


@router.get("/users", response_model=list[UserRead])
async def list_users(_admin: CurrentAdmin, db: DbSession) -> list[User]:
    return list((await db.execute(select(User).order_by(User.created_at))).scalars().all())


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: CreateUserRequest, _admin: CurrentAdmin, db: DbSession) -> User:
    existing = (
        await db.execute(select(User).where(User.email == payload.email))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_admin=payload.is_admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
