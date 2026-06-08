import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool


_TEST_DATABASE_URL = os.environ.get(
	"TEST_DATABASE_URL",
	"postgresql+asyncpg://todos:todos@127.0.0.1:5432/todos_test",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-suite-32bytes!")
os.environ["DATABASE_URL"] = _TEST_DATABASE_URL

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from fakes.user_auth_cache import FakeUserAuthCache
from todos_app.core.dependencies import get_user_auth_cache
from todos_app.core.settings import get_settings
from todos_app.infrastructure.persistence.database import AsyncSessionLocal
from todos_app.infrastructure.persistence.migrations import run_migrations_async
from todos_app.main import app


get_settings.cache_clear()


async def _reset_test_database_schema() -> None:
	engine = create_async_engine(_TEST_DATABASE_URL, poolclass=NullPool)
	try:
		async with engine.begin() as conn:
			await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
			await conn.execute(text("CREATE SCHEMA public"))
			await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
	finally:
		await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def override_user_auth_cache():
	"""Tests use FakeUserAuthCache — no live Valkey required (CI speed)."""
	app.dependency_overrides[get_user_auth_cache] = lambda: FakeUserAuthCache()
	yield
	app.dependency_overrides.pop(get_user_auth_cache, None)


@pytest.fixture(scope="session")
async def initialized_db() -> AsyncIterator[None]:
	await _reset_test_database_schema()
	await run_migrations_async("head")
	yield


@pytest.fixture
async def db_session(initialized_db: None) -> AsyncIterator[AsyncSession]:  # pyright: ignore[reportUnusedParameter]
	async with AsyncSessionLocal() as session:
		yield session
		await session.rollback()


@pytest.fixture
async def client(initialized_db: None) -> AsyncIterator[AsyncClient]:  # pyright: ignore[reportUnusedParameter]
	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as ac:
		yield ac
