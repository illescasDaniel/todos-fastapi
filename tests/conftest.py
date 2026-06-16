import os


# Must be set before importing todos_app (profile loader runs at import time).
os.environ["ENV_PROFILE"] = "test"

from todos_app.core.config.loader import clear_env_settings_cache, get_env_settings


clear_env_settings_cache()
_ENV = get_env_settings()
_TEST_DATABASE_URL = _ENV.postgres.test_url

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from fakes.fast_password_hasher import get_test_password_hasher
from fakes.user_auth_cache import FakeUserAuthCache
from todos_app.core.dependencies import get_password_hasher, get_user_auth_cache
from todos_app.infrastructure.persistence.database import AsyncSessionLocal
from todos_app.infrastructure.persistence.migrations import run_migrations_async
from todos_app.main import app


_TEST_PASSWORD_HASHER = get_test_password_hasher()


@pytest.fixture(scope="session", autouse=True)
def override_password_hasher():
	"""Low-cost Argon2 for tests; full signup/login HTTP paths stay in dedicated cases."""
	app.dependency_overrides[get_password_hasher] = lambda: _TEST_PASSWORD_HASHER
	yield
	app.dependency_overrides.pop(get_password_hasher, None)


@pytest.fixture(scope="session", autouse=True)
def override_user_auth_cache():
	"""Tests use FakeUserAuthCache — no live Valkey required (CI speed)."""
	app.dependency_overrides[get_user_auth_cache] = lambda: FakeUserAuthCache()
	yield
	app.dependency_overrides.pop(get_user_auth_cache, None)


async def _reset_test_database_schema() -> None:
	engine = create_async_engine(_TEST_DATABASE_URL, poolclass=NullPool)
	try:
		async with engine.begin() as conn:
			await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
			await conn.execute(text("CREATE SCHEMA public"))
			await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
	finally:
		await engine.dispose()


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
