from datetime import UTC, datetime
from typing import AsyncGenerator
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_active_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Allocation, Asset, Client, Movement, User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        for model in (Allocation, Movement, Asset, Client, User):
            await session.execute(delete(model))
        await session.commit()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def _get_test_user() -> User:
        return User(
            id=1,
            name="Test User",
            email="test@example.com",
            hashed_password="",
            is_active=True,
            created_at=datetime.now(UTC),
        )

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_current_active_user] = _get_test_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client

    app.dependency_overrides.clear()
