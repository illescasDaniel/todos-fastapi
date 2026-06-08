import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine

from todos_app.core.settings import get_settings
from todos_app.infrastructure.persistence.database import (
	create_engine_for_url,
	database_url_is_local_only,
)
from todos_app.infrastructure.persistence.migrations import run_migrations_async


_COMPOSE_DATABASE_HOSTS = frozenset({"postgres"})
SEED_DIR = Path(__file__).resolve().parent
SEED_SQL_FILES = (
	SEED_DIR / "default_users.sql",
	SEED_DIR / "default_todos.sql",
)


async def _truncate_tables(engine: AsyncEngine) -> None:
	async with engine.begin() as conn:
		await conn.execute(text("TRUNCATE TABLE todos, users RESTART IDENTITY CASCADE"))


async def _reset_database(seed_engine: AsyncEngine) -> None:
	await run_migrations_async()
	await _truncate_tables(seed_engine)


async def _apply_seed_sql(seed_engine: AsyncEngine) -> None:
	async with seed_engine.begin() as conn:
		for sql_file in SEED_SQL_FILES:
			if not sql_file.exists():
				raise FileNotFoundError(f"Seed SQL file not found: {sql_file}")
			await conn.execute(text(sql_file.read_text(encoding="utf-8")))


def assert_seed_allowed() -> None:
	"""Refuse seeding outside local development (remote DB, staging, or production)."""
	settings = get_settings()
	app_env = settings.app_env.strip().lower()
	if app_env in ("production", "staging"):
		raise RuntimeError(
			f"Refusing to seed: APP_ENV={settings.app_env!r} is not allowed. "
			"Seeding is only permitted in local development (APP_ENV=local)."
		)

	database_url = settings.database_url
	if database_url_is_local_only(database_url):
		return

	if app_env == "local":
		host = make_url(database_url).host
		if host in _COMPOSE_DATABASE_HOSTS:
			return

	url = make_url(database_url)
	host = url.host or "(no host)"
	raise RuntimeError(
		"Refusing to seed: DATABASE_URL must point to a local development database only.\n"
		"  PostgreSQL: host must be 127.0.0.1, localhost, ::1,\n"
		"    or Compose service name postgres with APP_ENV=local\n"
		f"  Configured URL host: {host}"
	)


async def reset_and_seed_defaults_async() -> None:
	assert_seed_allowed()
	database_url = get_settings().database_url
	seed_engine = create_engine_for_url(database_url)
	try:
		await _reset_database(seed_engine)
		await _apply_seed_sql(seed_engine)
	finally:
		await seed_engine.dispose()


def reset_and_seed_defaults() -> None:
	"""Recreate the configured database and apply default seed records."""
	asyncio.run(reset_and_seed_defaults_async())
