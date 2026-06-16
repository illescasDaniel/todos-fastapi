import pytest

from env_helpers import make_env_settings
from todos_app.infrastructure.persistence.seeding.runner import assert_seed_allowed


pytestmark = pytest.mark.unit


_PROD_DB_URL = "postgresql+asyncpg://todos:secret@db.prod.example.com:5432/todos"


def _patch_settings(
	monkeypatch: pytest.MonkeyPatch,
	*,
	app_env: str = "local",
	database_url: str = "postgresql+asyncpg://todos:secret@127.0.0.1:5432/todos",
) -> None:
	normalized_env = app_env.lower()
	if normalized_env not in {"local", "staging", "production"}:
		normalized_env = "staging"
	effective_db_url = database_url if normalized_env == "local" else _PROD_DB_URL
	settings = make_env_settings(app_env=normalized_env, database_url=effective_db_url)  # pyright: ignore[reportArgumentType]
	monkeypatch.setattr(
		"todos_app.infrastructure.persistence.seeding.runner.get_settings",
		lambda: settings,
	)
	monkeypatch.setattr("todos_app.core.settings.get_settings", lambda: settings)


@pytest.mark.parametrize("app_env", ["production", "staging", "Production", "STAGING"])
def test_given_non_local_app_env_when_asserting_seed_allowed_then_raises(
	monkeypatch: pytest.MonkeyPatch,
	app_env: str,
) -> None:
	# given
	_patch_settings(monkeypatch, app_env=app_env)

	# when
	with pytest.raises(RuntimeError, match="Refusing to seed: APP_ENV="):
		assert_seed_allowed()

	# then


def test_given_local_env_and_local_postgres_when_asserting_seed_allowed_then_succeeds(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	# given
	_patch_settings(monkeypatch)

	# when
	assert_seed_allowed()

	# then


@pytest.mark.parametrize(
	"database_url",
	[
		"postgresql+asyncpg://todos:secret@127.0.0.1:5432/todos",
		"postgresql+asyncpg://todos:secret@postgres:5432/todos",
	],
)
def test_given_local_database_host_when_asserting_seed_allowed_then_succeeds(
	monkeypatch: pytest.MonkeyPatch,
	database_url: str,
) -> None:
	# given
	_patch_settings(monkeypatch, database_url=database_url)

	# when
	assert_seed_allowed()

	# then


@pytest.mark.parametrize(
	"database_url",
	[
		"postgresql+asyncpg://todos:secret@db.prod.example.com:5432/todos",
	],
)
def test_given_remote_database_url_when_asserting_seed_allowed_then_raises(
	monkeypatch: pytest.MonkeyPatch,
	database_url: str,
) -> None:
	# given
	_patch_settings(monkeypatch, database_url=database_url)

	# when
	with pytest.raises(RuntimeError, match="Refusing to seed"):
		assert_seed_allowed()

	# then
