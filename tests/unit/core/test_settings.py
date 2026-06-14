import pytest

from todos_app.core.settings import Settings


pytestmark = pytest.mark.unit

_VALID_SECRET = "test-secret-key-for-pytest-suite-32bytes!"

_PROD_DB_URL = "postgresql+asyncpg://todos:securepassword@prod.example.com:5432/todos"


def test_settings_helpers() -> None:
	settings = Settings(
		jwt_secret_key=_VALID_SECRET,
		app_env="local",
		database_url="postgresql+asyncpg://todos:x@127.0.0.1:5432/todos",
	)
	assert settings.is_local() is True
	assert settings.is_staging() is False
	assert settings.is_production() is False
	assert settings.exposes_error_details() is True
	assert settings.exposes_api_docs() is True

	settings = Settings(jwt_secret_key=_VALID_SECRET, app_env="production", database_url=_PROD_DB_URL)
	assert settings.is_production() is True
	assert settings.exposes_error_details() is False
	assert settings.exposes_api_docs() is False

	settings = Settings(jwt_secret_key=_VALID_SECRET, app_env="staging", database_url=_PROD_DB_URL)
	assert settings.is_staging() is True
	assert settings.exposes_error_details() is False
	assert settings.exposes_api_docs() is False


def test_settings_derives_local_urls_from_passwords() -> None:
	settings = Settings(
		jwt_secret_key=_VALID_SECRET,
		app_env="local",
		database_url="",
		valkey_url="",
		postgres_password="local-db-pass",
		valkey_password="local-valkey-pass",
		postgres_port=5433,
		valkey_port=6380,
		postgres_db="todos",
	)
	assert settings.database_url == "postgresql+asyncpg://todos:local-db-pass@127.0.0.1:5433/todos"
	assert settings.valkey_url == "valkey://:local-valkey-pass@127.0.0.1:6380/0"


@pytest.mark.parametrize(
	"secret_key",
	[
		"short",
		"change-me-generate-a-secure-random-value",
		"your-secret-key-is-not-long-enough-here",
		"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
		"local-dev-migrate-placeholder-secret",
		"container-migrate-placeholder-secret",
	],
)
def test_settings_rejects_weak_jwt_secret(secret_key: str) -> None:
	with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
		Settings(
			jwt_secret_key=secret_key,
			database_url="postgresql+asyncpg://todos:x@127.0.0.1:5432/todos",
		)


def test_settings_rejects_non_hs256_algorithm() -> None:
	with pytest.raises(ValueError, match="JWT_ALGORITHM"):
		Settings(
			jwt_secret_key=_VALID_SECRET,
			jwt_algorithm="HS512",
			database_url="postgresql+asyncpg://todos:x@127.0.0.1:5432/todos",
		)


def test_settings_valkey_defaults_without_password() -> None:
	settings = Settings(
		jwt_secret_key=_VALID_SECRET,
		database_url="postgresql+asyncpg://todos:x@127.0.0.1:5432/todos",
		valkey_url="",
		valkey_password="",
		valkey_port=6379,
	)
	assert settings.valkey_url == "valkey://127.0.0.1:6379/0"
	assert settings.auth_user_cache_ttl_seconds == 120
