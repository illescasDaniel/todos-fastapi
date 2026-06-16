from unittest.mock import patch

import pytest

from todos_app.infrastructure.persistence.database import (
	assert_database_url_is_local_only,
	database_url_is_local_only,
	database_url_is_postgresql,
	require_async_db_driver,
)


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
	("database_url", "expected"),
	[
		("postgresql+asyncpg://u:p@localhost/todos", True),
		("postgres+asyncpg://u:p@localhost/todos", True),
		("mysql+asyncmy://localhost/todos", False),
	],
)
def test_given_database_url_when_checking_is_postgresql_then_returns_expected(
	database_url: str,
	expected: bool,
) -> None:
	# given

	# when
	result = database_url_is_postgresql(database_url)

	# then
	assert result is expected


def test_given_asyncpg_postgresql_url_when_requiring_driver_then_succeeds() -> None:
	# given
	database_url = "postgresql+asyncpg://u:p@localhost/todos"

	# when
	require_async_db_driver(database_url)

	# then


def test_given_non_asyncpg_url_when_requiring_driver_then_raises_runtime_error() -> None:
	# given
	database_url = "sqlite+aiosqlite:///tmp/todos.db"

	# when
	with pytest.raises(RuntimeError, match="asyncpg"):
		require_async_db_driver(database_url)

	# then


def test_given_missing_asyncpg_module_when_requiring_driver_then_raises_runtime_error() -> None:
	# given
	database_url = "postgresql+asyncpg://u:p@localhost/todos"

	# when
	with patch(
		"todos_app.infrastructure.persistence.database.importlib.import_module",
		side_effect=ImportError("No module named asyncpg"),
	):
		with pytest.raises(RuntimeError, match="asyncpg") as exc_info:
			require_async_db_driver(database_url)

	# then
	assert "asyncpg" in str(exc_info.value)


@pytest.mark.parametrize(
	"database_url",
	[
		"postgresql+asyncpg://todos:todos@127.0.0.1:5432/todos",
		"postgresql+asyncpg://todos:todos@localhost:5432/todos",
	],
)
def test_given_local_development_url_when_checking_is_local_only_then_returns_true(
	database_url: str,
) -> None:
	# given

	# when
	result = database_url_is_local_only(database_url)

	# then
	assert result is True


@pytest.mark.parametrize(
	"database_url",
	[
		"postgresql+asyncpg://todos:todos@db.example.com:5432/todos",
		"postgresql+asyncpg://todos:todos@postgres:5432/todos",
	],
)
def test_given_non_local_url_when_checking_is_local_only_then_returns_false(
	database_url: str,
) -> None:
	# given

	# when
	result = database_url_is_local_only(database_url)

	# then
	assert result is False


def test_given_remote_url_when_asserting_local_only_then_raises_with_host_in_message() -> None:
	# given
	database_url = "postgresql+asyncpg://u:p@db.prod.example.com/todos"

	# when
	with pytest.raises(RuntimeError, match="Refusing to wipe") as exc_info:
		assert_database_url_is_local_only(database_url)

	# then
	assert "db.prod.example.com" in str(exc_info.value)
