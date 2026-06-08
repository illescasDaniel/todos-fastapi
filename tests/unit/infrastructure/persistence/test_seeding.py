import pytest

from todos_app.core.settings import get_settings
from todos_app.infrastructure.persistence.seeding.runner import assert_seed_allowed


pytestmark = pytest.mark.unit


def _patch_settings(
	monkeypatch: pytest.MonkeyPatch,
	*,
	app_env: str = "local",
	database_url: str = "postgresql+asyncpg://todos:secret@127.0.0.1:5432/todos",
) -> None:
	monkeypatch.setenv("APP_ENV", app_env)
	monkeypatch.setenv("DATABASE_URL", database_url)
	monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-for-pytest-suite-32bytes!")
	get_settings.cache_clear()


@pytest.mark.parametrize("app_env", ["production", "staging", "Production", "STAGING"])
def test_assert_seed_allowed_rejects_non_local_app_env(
	monkeypatch: pytest.MonkeyPatch,
	app_env: str,
) -> None:
	_patch_settings(monkeypatch, app_env=app_env)
	with pytest.raises(RuntimeError, match="Refusing to seed: APP_ENV="):
		assert_seed_allowed()


def test_assert_seed_allowed_allows_local_postgres(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	_patch_settings(monkeypatch)
	assert_seed_allowed()


@pytest.mark.parametrize(
	"database_url",
	[
		"postgresql+asyncpg://todos:secret@127.0.0.1:5432/todos",
		"postgresql+asyncpg://todos:secret@postgres:5432/todos",
	],
)
def test_assert_seed_allowed_allows_local_database_hosts(
	monkeypatch: pytest.MonkeyPatch,
	database_url: str,
) -> None:
	_patch_settings(monkeypatch, database_url=database_url)
	assert_seed_allowed()


@pytest.mark.parametrize(
	"database_url",
	[
		"postgresql+asyncpg://todos:secret@db.prod.example.com:5432/todos",
	],
)
def test_assert_seed_allowed_rejects_remote_database_urls(
	monkeypatch: pytest.MonkeyPatch,
	database_url: str,
) -> None:
	_patch_settings(monkeypatch, database_url=database_url)
	with pytest.raises(RuntimeError, match="Refusing to seed"):
		assert_seed_allowed()
