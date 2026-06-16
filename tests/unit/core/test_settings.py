import pytest

from env_helpers import make_env_settings


pytestmark = pytest.mark.unit

_VALID_SECRET = "test-secret-key-for-pytest-suite-32bytes!"

_PROD_DB_URL = "postgresql+asyncpg://todos:securepassword@prod.example.com:5432/todos"


def test_given_local_env_when_checking_settings_helpers_then_exposes_local_flags() -> None:
	# given
	settings = make_env_settings(
		jwt_secret_key=_VALID_SECRET,
		app_env="local",
		database_url="postgresql+asyncpg://todos:x@127.0.0.1:5432/todos",
	)

	# when
	is_local = settings.is_local()
	is_staging = settings.is_staging()
	is_production = settings.is_production()
	exposes_details = settings.exposes_error_details()
	exposes_docs = settings.exposes_api_docs()

	# then
	assert is_local is True
	assert is_staging is False
	assert is_production is False
	assert exposes_details is True
	assert exposes_docs is True


def test_given_production_env_when_checking_settings_helpers_then_hides_sensitive_surfaces() -> None:
	# given
	settings = make_env_settings(jwt_secret_key=_VALID_SECRET, app_env="production", database_url=_PROD_DB_URL)

	# when
	is_production = settings.is_production()
	exposes_details = settings.exposes_error_details()
	exposes_docs = settings.exposes_api_docs()

	# then
	assert is_production is True
	assert exposes_details is False
	assert exposes_docs is False


def test_given_staging_env_when_checking_settings_helpers_then_hides_sensitive_surfaces() -> None:
	# given
	settings = make_env_settings(jwt_secret_key=_VALID_SECRET, app_env="staging", database_url=_PROD_DB_URL)

	# when
	is_staging = settings.is_staging()
	exposes_details = settings.exposes_error_details()
	exposes_docs = settings.exposes_api_docs()

	# then
	assert is_staging is True
	assert exposes_details is False
	assert exposes_docs is False


def test_given_explicit_urls_when_building_settings_then_keeps_profile_values() -> None:
	# given
	postgres_password = "local-db-pass"
	valkey_password = "local-valkey-pass"
	database_url = "postgresql+asyncpg://todos:local-db-pass@127.0.0.1:5433/todos"
	valkey_url = "valkey://:local-valkey-pass@127.0.0.1:6380/0"

	# when
	settings = make_env_settings(
		jwt_secret_key=_VALID_SECRET,
		app_env="local",
		database_url=database_url,
		valkey_url=valkey_url,
		postgres_password=postgres_password,
		valkey_password=valkey_password,
		postgres_port=5433,
		valkey_port=6380,
		postgres_db="todos",
	)

	# then
	assert settings.postgres.url == database_url
	assert settings.valkey.url == valkey_url


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
def test_given_weak_jwt_secret_when_creating_settings_then_raises_value_error(secret_key: str) -> None:
	# given

	# when
	with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
		make_env_settings(jwt_secret_key=secret_key)

	# then


def test_given_non_hs256_algorithm_when_creating_settings_then_raises_value_error() -> None:
	# given

	# when
	with pytest.raises(ValueError):
		make_env_settings(jwt_algorithm="HS512")  # pyright: ignore[reportArgumentType]

	# then


def test_given_production_loopback_database_url_when_creating_settings_then_raises_value_error() -> None:
	# given

	# when
	with pytest.raises(ValueError, match="DATABASE_URL"):
		make_env_settings(
			app_env="production",
			database_url="postgresql+asyncpg://todos:x@127.0.0.1:5432/todos",
		)

	# then
