from unittest.mock import patch

import pytest

from todos_app.infrastructure.persistence.database import (
	assert_database_url_is_local_only,
	database_url_is_local_only,
	database_url_is_postgresql,
	require_async_db_driver,
)


pytestmark = pytest.mark.unit


def test_database_url_is_postgresql() -> None:
	assert database_url_is_postgresql("postgresql+asyncpg://u:p@localhost/todos") is True
	assert database_url_is_postgresql("postgres+asyncpg://u:p@localhost/todos") is True
	assert database_url_is_postgresql("mysql+asyncmy://localhost/todos") is False


def test_require_async_db_driver_succeeds_for_asyncpg() -> None:
	require_async_db_driver("postgresql+asyncpg://u:p@localhost/todos")


def test_require_async_db_driver_rejects_non_asyncpg() -> None:
	with pytest.raises(RuntimeError, match="asyncpg"):
		require_async_db_driver("sqlite+aiosqlite:///tmp/todos.db")


def test_require_async_db_driver_raises_when_asyncpg_missing() -> None:
	with patch(
		"todos_app.infrastructure.persistence.database.importlib.import_module",
		side_effect=ImportError("No module named asyncpg"),
	):
		with pytest.raises(RuntimeError, match="asyncpg") as exc_info:
			require_async_db_driver("postgresql+asyncpg://u:p@localhost/todos")
	assert "asyncpg" in str(exc_info.value)


@pytest.mark.parametrize(
	"database_url",
	[
		"postgresql+asyncpg://todos:todos@127.0.0.1:5432/todos",
		"postgresql+asyncpg://todos:todos@localhost:5432/todos",
	],
)
def test_database_url_is_local_only_allows_local_development_urls(database_url: str) -> None:
	assert database_url_is_local_only(database_url) is True


@pytest.mark.parametrize(
	"database_url",
	[
		"postgresql+asyncpg://todos:todos@db.example.com:5432/todos",
		"postgresql+asyncpg://todos:todos@postgres:5432/todos",
	],
)
def test_database_url_is_local_only_rejects_non_local_urls(database_url: str) -> None:
	assert database_url_is_local_only(database_url) is False


def test_assert_database_url_is_local_only_raises_with_helpful_message() -> None:
	with pytest.raises(RuntimeError, match="Refusing to wipe") as exc_info:
		assert_database_url_is_local_only("postgresql+asyncpg://u:p@db.prod.example.com/todos")
	assert "db.prod.example.com" in str(exc_info.value)
