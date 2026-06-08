from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from todos_app.core.settings import get_settings
from todos_app.infrastructure.persistence.database import require_async_db_driver


def alembic_config() -> Config:
	project_root = Path(__file__).resolve().parents[4]
	cfg = Config(str(project_root / "alembic.ini"))
	cfg.set_main_option("script_location", str(project_root / "alembic"))
	return cfg


def _run_upgrade(connection: Connection, cfg: Config, revision: str) -> None:
	cfg.attributes["connection"] = connection
	command.upgrade(cfg, revision)


def _run_downgrade(connection: Connection, cfg: Config, revision: str) -> None:
	cfg.attributes["connection"] = connection
	command.downgrade(cfg, revision)


async def run_migrations_async(revision: str = "head") -> None:
	cfg = alembic_config()
	database_url = get_settings().database_url
	require_async_db_driver(database_url)
	connectable = create_async_engine(database_url, poolclass=pool.NullPool)
	try:
		async with connectable.begin() as conn:
			await conn.run_sync(_run_upgrade, cfg, revision)
	finally:
		await connectable.dispose()


async def downgrade_migrations_async(revision: str = "base") -> None:
	cfg = alembic_config()
	database_url = get_settings().database_url
	require_async_db_driver(database_url)
	connectable = create_async_engine(database_url, poolclass=pool.NullPool)
	try:
		async with connectable.begin() as conn:
			await conn.run_sync(_run_downgrade, cfg, revision)
	finally:
		await connectable.dispose()
