import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from todos_app.core.settings import get_settings
from todos_app.infrastructure.persistence.database import Base, import_all_orm_models, require_async_db_driver


config = context.config

if config.config_file_name is not None:
	fileConfig(config.config_file_name)

import_all_orm_models()
target_metadata = Base.metadata


def get_database_url() -> str:
	return get_settings().database_url


def run_migrations_offline() -> None:
	url = get_database_url()
	context.configure(
		url=url,
		target_metadata=target_metadata,
		literal_binds=True,
		dialect_opts={"paramstyle": "named"},
	)

	with context.begin_transaction():
		context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
	context.configure(connection=connection, target_metadata=target_metadata)

	with context.begin_transaction():
		context.run_migrations()


async def run_async_migrations() -> None:
	database_url = get_database_url()
	require_async_db_driver(database_url)
	connectable = create_async_engine(database_url, poolclass=pool.NullPool)

	async with connectable.connect() as connection:
		await connection.run_sync(do_run_migrations)

	await connectable.dispose()


def run_migrations_online() -> None:
	connectable = config.attributes.get("connection")
	if connectable is None:
		asyncio.run(run_async_migrations())
	else:
		do_run_migrations(connectable)


if context.is_offline_mode():
	run_migrations_offline()
else:
	run_migrations_online()
