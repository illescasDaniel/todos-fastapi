import importlib
import ipaddress
from collections.abc import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from todos_app.core.settings import get_settings


_LOCAL_DATABASE_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def require_async_db_driver(database_url: str) -> None:
	driver = make_url(database_url).drivername.split("+", 1)[-1]
	if driver != "asyncpg":
		raise RuntimeError(
			f"Unsupported database driver {driver!r}. "
			"This project requires PostgreSQL with asyncpg "
			"(DATABASE_URL=postgresql+asyncpg://...)."
		)
	try:
		importlib.import_module("asyncpg")
	except ImportError as exc:
		raise RuntimeError("Database driver 'asyncpg' is not installed.") from exc


def database_url_is_postgresql(database_url: str) -> bool:
	driver = make_url(database_url).drivername
	return driver.startswith("postgresql") or driver.startswith("postgres")


def _database_host_is_loopback(host: str | None) -> bool:
	if not host:
		return False
	normalized = host.strip().lower()
	if normalized in _LOCAL_DATABASE_HOSTS:
		return True
	if normalized.endswith(".localhost"):
		return True
	try:
		return ipaddress.ip_address(normalized).is_loopback
	except ValueError:
		return False


def database_url_is_local_only(database_url: str) -> bool:
	if not database_url_is_postgresql(database_url):
		return False
	return _database_host_is_loopback(make_url(database_url).host)


def assert_database_url_is_local_only(database_url: str) -> None:
	if database_url_is_local_only(database_url):
		return
	url = make_url(database_url)
	host = url.host or "(no host)"
	raise RuntimeError(
		"Refusing to wipe: DATABASE_URL must point to a local development database only.\n"
		"  PostgreSQL: host must be 127.0.0.1, localhost, or ::1\n"
		f"  Configured URL host: {host}"
	)


def create_engine_for_url(database_url: str) -> AsyncEngine:
	require_async_db_driver(database_url)
	if not database_url_is_postgresql(database_url):
		raise RuntimeError("DATABASE_URL must use postgresql+asyncpg://...")
	return create_async_engine(database_url)


engine = create_engine_for_url(get_settings().database_url)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
	pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
	async with AsyncSessionLocal() as session:
		try:
			yield session
			await session.commit()
		except Exception:
			await session.rollback()
			raise


def import_all_orm_models() -> None:
	importlib.import_module("todos_app.infrastructure.persistence.users.orm")
	importlib.import_module("todos_app.infrastructure.persistence.todos.orm")
