import os
from collections.abc import AsyncIterator

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from todos_app.core.settings import get_settings
from todos_app.infrastructure.persistence.migrations import (
	alembic_config,
	downgrade_migrations_async,
	run_migrations_async,
)


pytestmark = pytest.mark.integration

_MIGRATION_TEST_URL = os.environ.get(
	"TEST_DATABASE_URL",
	"postgresql+asyncpg://todos:todos@127.0.0.1:5432/todos_test",
)


@pytest.fixture
async def migration_db_url(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[str]:
	monkeypatch.setenv("DATABASE_URL", _MIGRATION_TEST_URL)
	get_settings.cache_clear()
	yield _MIGRATION_TEST_URL
	get_settings.cache_clear()


async def test_alembic_upgrade_head_applies_migrations(migration_db_url: str) -> None:
	await downgrade_migrations_async("base")
	await run_migrations_async("head")

	engine = create_async_engine(migration_db_url)
	try:
		async with engine.connect() as conn:
			tables = await conn.run_sync(lambda connection: inspect(connection).get_table_names())
			assert "users" in tables
			assert "todos" in tables
			assert "alembic_version" in tables

			head_revision = ScriptDirectory.from_config(alembic_config()).get_current_head()
			result = await conn.execute(text("SELECT version_num FROM alembic_version"))
			version = result.scalar_one()
			assert version == head_revision
	finally:
		await engine.dispose()


async def test_alembic_downgrade_base_removes_schema(migration_db_url: str) -> None:
	await run_migrations_async("head")
	await downgrade_migrations_async("base")

	engine = create_async_engine(migration_db_url)
	try:
		async with engine.connect() as conn:
			tables = await conn.run_sync(lambda connection: inspect(connection).get_table_names())
			assert "users" not in tables
			assert "todos" not in tables
	finally:
		await engine.dispose()

	await run_migrations_async("head")
