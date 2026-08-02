"""Integration test fixtures: a dedicated Postgres database, migrated once per session and
wrapped in a rolled-back savepoint per test so tests never see each other's data."""

import os
import uuid
from collections.abc import AsyncGenerator

os.environ.setdefault("TAP_DATABASE_URL", "postgresql+asyncpg://tap:tap@localhost:5544/tap_test")
os.environ.setdefault("TAP_JWT_SECRET_KEY", "test-only-secret-do-not-use-in-production")
os.environ.setdefault(
    "TAP_CREDENTIAL_ENCRYPTION_KEY", "Hp5q9TzHLw7yzbZsL3vdfCFWlLAMt-sj3F8JAzg-SMc="
)

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.api.deps import get_db
from app.core.config import get_settings
from app.db.base import Base
from app.main import app
from app.seed.loader import seed


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine]:
    eng = create_async_engine(get_settings().database_url)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def seeded_db(db_session: AsyncSession) -> AsyncSession:
    await seed(db_session)
    return db_session


@pytest_asyncio.fixture
async def client(seeded_db: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        yield seeded_db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"
