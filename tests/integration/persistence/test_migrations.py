from collections.abc import AsyncIterator

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

from env_config.loader import clear_env_settings_cache, get_env_settings
from todos_app.infrastructure.persistence.migrations import (
	alembic_config,
	downgrade_migrations_async,
	run_migrations_async,
)


pytestmark = pytest.mark.integration

_MIGRATION_TEST_URL = get_env_settings().postgres.test_url


@pytest.fixture
async def migration_db_url(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[str]:
	monkeypatch.setenv("DATABASE_URL", _MIGRATION_TEST_URL)
	clear_env_settings_cache()
	yield _MIGRATION_TEST_URL
	clear_env_settings_cache()


async def test_given_empty_schema_when_upgrading_to_head_then_applies_migrations(
	migration_db_url: str,
) -> None:
	# given
	await downgrade_migrations_async("base")

	# when
	await run_migrations_async("head")

	# then
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


async def test_given_migrated_schema_when_downgrading_to_base_then_removes_application_tables(
	migration_db_url: str,
) -> None:
	# given
	await run_migrations_async("head")

	# when
	await downgrade_migrations_async("base")

	# then
	engine = create_async_engine(migration_db_url)
	try:
		async with engine.connect() as conn:
			tables = await conn.run_sync(lambda connection: inspect(connection).get_table_names())
			assert "users" not in tables
			assert "todos" not in tables
	finally:
		await engine.dispose()

	await run_migrations_async("head")
