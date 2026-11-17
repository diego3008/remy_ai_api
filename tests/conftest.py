import os

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

from src.api import api_router
from src.db import get_session
from src.models import Base

# Set to a migrated, disposable Postgres DB (postgresql+asyncpg://...) to run
# against the real schema; otherwise tests use in-memory SQLite.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


async def _make_engine():
    if TEST_DATABASE_URL:
        return create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite only enforces FKs (and ON DELETE rules) with this pragma.
    @event.listens_for(engine.sync_engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


@pytest.fixture
async def client():
    engine = await _make_engine()
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    async def _session():
        async with sessionmaker() as session:
            yield session

    app = FastAPI()
    app.include_router(api_router)
    app.dependency_overrides[get_session] = _session

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    if TEST_DATABASE_URL:
        tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
        async with engine.begin() as conn:
            await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    await engine.dispose()
