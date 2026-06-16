import os
import shutil
from pathlib import Path

import pytest

from todos_app.core.config.loader import clear_env_settings_cache, get_env_settings


pytestmark = pytest.mark.unit

_COMPOSE_DB = "postgresql+asyncpg://todos:todos@postgres:5432/todos_test"
_COMPOSE_VALKEY = "valkey://:test-valkey-password-for-ci@valkey:6379/0"


def test_given_compose_url_in_profile_when_loading_with_todos_compose_then_uses_in_network_urls() -> None:
	os.environ["ENV_PROFILE"] = "test"
	os.environ["TODOS_COMPOSE"] = "1"
	clear_env_settings_cache()

	settings = get_env_settings()

	assert settings.postgres.url == _COMPOSE_DB
	assert settings.valkey.url == _COMPOSE_VALKEY
	assert settings.postgres.compose_url == _COMPOSE_DB
	assert settings.valkey.compose_url == _COMPOSE_VALKEY

	clear_env_settings_cache()
	os.environ.pop("TODOS_COMPOSE", None)


def test_given_todos_compose_without_compose_url_when_loading_settings_then_raises(
	tmp_path: Path,
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	repo_root = Path(__file__).resolve().parents[4]
	config_dir = tmp_path / "config"
	profiles_dir = config_dir / "profiles"
	profiles_dir.mkdir(parents=True)
	shutil.copy(repo_root / "config" / "base.toml", config_dir / "base.toml")
	(profiles_dir / "nocompose.toml").write_text(
		'[jwt]\nsecret_key = "test-secret-key-for-pytest-suite-32bytes!"\n'
		'[postgres]\npassword = "p"\nurl = "postgresql+asyncpg://u:p@127.0.0.1:5432/db"\n'
		'test_url = "postgresql+asyncpg://u:p@127.0.0.1:5432/db"\n'
		'[valkey]\npassword = "p"\nurl = "valkey://:p@127.0.0.1:6379/0"\n',
		encoding="utf-8",
	)
	monkeypatch.setenv("TODOS_CONFIG_DIR", str(config_dir))
	monkeypatch.setenv("ENV_PROFILE", "nocompose")
	monkeypatch.setenv("TODOS_COMPOSE", "1")
	clear_env_settings_cache()

	with pytest.raises(RuntimeError, match="POSTGRES_COMPOSE_URL"):
		get_env_settings()

	clear_env_settings_cache()
	monkeypatch.delenv("TODOS_CONFIG_DIR", raising=False)
	monkeypatch.delenv("TODOS_COMPOSE", raising=False)
	os.environ.pop("ENV_PROFILE", None)


def test_given_todos_compose_unset_when_loading_settings_then_uses_profile_urls() -> None:
	os.environ["ENV_PROFILE"] = "test"
	os.environ.pop("TODOS_COMPOSE", None)
	clear_env_settings_cache()

	settings = get_env_settings()

	assert "127.0.0.1" in settings.postgres.url
	assert "127.0.0.1" in settings.valkey.url
	assert "postgres" in settings.postgres.compose_url
	assert "valkey" in settings.valkey.compose_url

	clear_env_settings_cache()


def test_given_missing_local_profile_when_loading_settings_then_raises_with_fix_hint() -> None:
	os.environ["ENV_PROFILE"] = "localmissing"
	clear_env_settings_cache()

	with pytest.raises(RuntimeError, match="profiles/localmissing.toml"):
		get_env_settings()

	clear_env_settings_cache()
	os.environ.pop("ENV_PROFILE", None)


@pytest.mark.parametrize(
	"profile",
	["", "../other", "Local", "local-2", "production.example"],
)
def test_given_invalid_profile_name_when_loading_settings_then_raises(profile: str) -> None:
	os.environ["ENV_PROFILE"] = profile
	clear_env_settings_cache()

	with pytest.raises(RuntimeError, match="ENV_PROFILE"):
		get_env_settings()

	clear_env_settings_cache()
	os.environ.pop("ENV_PROFILE", None)


def test_given_unset_profile_when_loading_settings_then_raises() -> None:
	os.environ.pop("ENV_PROFILE", None)
	clear_env_settings_cache()

	with pytest.raises(RuntimeError, match="ENV_PROFILE is not set"):
		get_env_settings()


def test_given_reserved_example_profile_when_loading_settings_then_raises() -> None:
	os.environ["ENV_PROFILE"] = "example"
	clear_env_settings_cache()

	with pytest.raises(RuntimeError, match="reserved"):
		get_env_settings()

	clear_env_settings_cache()
	os.environ.pop("ENV_PROFILE", None)


def test_given_missing_custom_profile_when_loading_settings_then_raises_with_create_hint() -> None:
	os.environ["ENV_PROFILE"] = "local2"
	clear_env_settings_cache()

	with pytest.raises(RuntimeError, match="profiles/local2.toml"):
		get_env_settings()

	clear_env_settings_cache()
	os.environ.pop("ENV_PROFILE", None)


def test_given_todos_repo_root_when_loading_settings_then_uses_repo_config(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	repo_root = Path(__file__).resolve().parents[4]
	monkeypatch.setenv("TODOS_REPO_ROOT", str(repo_root))
	monkeypatch.setenv("ENV_PROFILE", "test")
	clear_env_settings_cache()

	settings = get_env_settings()

	assert settings.postgres.db == "todos_test"
	assert (repo_root / "config" / "base.toml").is_file()

	clear_env_settings_cache()
	monkeypatch.delenv("TODOS_REPO_ROOT", raising=False)
