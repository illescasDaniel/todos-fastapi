import importlib
import os
import sys

import pytest

from env_config.loader import clear_env_settings_cache, get_env_settings


pytestmark = pytest.mark.unit

_COMPOSE_DB = "postgresql+asyncpg://todos:pass@postgres:5432/todos"
_COMPOSE_VALKEY = "valkey://:pass@valkey:6379/0"


def test_given_compose_database_url_in_environ_when_loading_settings_then_overrides_profile() -> None:
	# given
	os.environ["ENV_PROFILE"] = "test"
	os.environ["DATABASE_URL"] = _COMPOSE_DB
	os.environ["VALKEY_URL"] = _COMPOSE_VALKEY
	clear_env_settings_cache()

	# when
	settings = get_env_settings()

	# then
	assert settings.postgres.url == _COMPOSE_DB
	assert settings.valkey.url == _COMPOSE_VALKEY
	assert os.environ["DATABASE_URL"] == _COMPOSE_DB


def test_given_empty_database_url_in_environ_when_loading_settings_then_keeps_profile() -> None:
	# given
	os.environ["ENV_PROFILE"] = "test"
	os.environ["DATABASE_URL"] = ""
	clear_env_settings_cache()

	# when
	settings = get_env_settings()

	# then
	assert settings.postgres.url == "postgresql+asyncpg://todos:todos@127.0.0.1:5432/todos_test"

	clear_env_settings_cache()
	os.environ.pop("DATABASE_URL", None)


def test_given_missing_local_profile_when_loading_settings_then_raises_with_fix_hint(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	# given
	real_import = importlib.import_module

	def fake_import(name: str, package: str | None = None):
		if name == "env_config.profiles.local":
			raise ModuleNotFoundError(name)
		return real_import(name, package)

	monkeypatch.setenv("ENV_PROFILE", "local")
	monkeypatch.setattr(importlib, "import_module", fake_import)
	sys.modules.pop("env_config.profiles.local", None)
	clear_env_settings_cache()

	# when / then
	with pytest.raises(RuntimeError, match="profiles/local.py"):
		get_env_settings()

	clear_env_settings_cache()


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
	sys.modules.pop("env_config.profiles.local2", None)

	with pytest.raises(RuntimeError, match="profiles/local2.py"):
		get_env_settings()

	clear_env_settings_cache()
	os.environ.pop("ENV_PROFILE", None)
