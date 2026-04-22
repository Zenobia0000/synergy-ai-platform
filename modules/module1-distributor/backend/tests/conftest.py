"""Pytest fixtures for backend tests.

Strategy:
- Use SQLite via aiosqlite for an isolated, in-memory DB per test.
- Patch sqlalchemy.dialects.postgresql.UUID -> sa.Uuid BEFORE importing
  app modules, so the PostgreSQL-specific type compiles cross-dialect.
- Set TESTING=1 so config.validate_runtime() does not require real
  webhook secrets at startup.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# 1) Mark test mode and DB URL BEFORE importing the app.
#    Use a file-backed sqlite so the test fixture and the production
#    `app.core.database.async_session` (used by scheduler_service) share
#    the same database — `:memory:` is per-connection and would isolate
#    them into two empty DBs.
_TEST_DB_FILE = Path(tempfile.gettempdir()) / "n8n_rpa_post_test.sqlite3"
if _TEST_DB_FILE.exists():
    _TEST_DB_FILE.unlink()

os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_FILE.as_posix()}"
os.environ.setdefault("N8N_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-prod")

# 2) Cross-dialect UUID patch
import sqlalchemy as _sa  # noqa: E402
import sqlalchemy.dialects.postgresql as _pg  # noqa: E402

_pg.UUID = _sa.Uuid  # type: ignore[assignment,misc]

# 3) Standard imports
import asyncio  # noqa: E402
from typing import AsyncIterator  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

# 4) Import app AFTER patches — uses the env DATABASE_URL set above
from app.core.database import Base, async_session as app_async_session, engine, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def _reset_schema() -> AsyncIterator[None]:
    """Drop & recreate all tables before each test for isolation.

    Uses the app's own engine so any code path that imports
    `app.core.database.async_session` (e.g. scheduler_service) sees the
    same database as the test fixtures.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture()
async def db_session() -> AsyncIterator[AsyncSession]:
    """Session bound to the shared app engine — same DB as production code."""
    async with app_async_session() as session:
        yield session


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """HTTPX async client wired to the FastAPI app with the shared test DB."""

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        async with app_async_session() as s:
            yield s

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
