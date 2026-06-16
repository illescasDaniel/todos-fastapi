"""Build EnvSettings instances for unit tests."""

from typing import Any

from env_config.loader import apply_dotted_overrides
from env_config.schema import (
	ApiSettings,
	Argon2Settings,
	ComposeSettings,
	DeploySettings,
	EnvSettings,
	JwtSettings,
	McpSettings,
	PostgresSettings,
	ValkeySettings,
)


# Legacy flat kwargs from pre-nested EnvSettings — mapped to dotted override paths.
_FLAT_OVERRIDE_PATHS: dict[str, str] = {
	"api_host": "api.host",
	"api_port": "api.port",
	"postgres_port": "postgres.port",
	"valkey_port": "valkey.port",
	"compose_infra_bind": "compose.infra_bind",
	"compose_app_bind": "compose.app_bind",
	"postgres_user": "postgres.user",
	"postgres_db": "postgres.db",
	"postgres_password": "postgres.password",
	"database_url": "postgres.url",
	"test_database_url": "postgres.test_url",
	"valkey_password": "valkey.password",
	"valkey_url": "valkey.url",
	"auth_user_cache_ttl_seconds": "valkey.auth_user_cache_ttl_seconds",
	"jwt_secret_key": "jwt.secret_key",
	"jwt_algorithm": "jwt.algorithm",
	"jwt_expire_minutes": "jwt.expire_minutes",
	"jwt_issuer": "jwt.issuer",
	"jwt_audience": "jwt.audience",
	"run_migrations": "deploy.run_migrations",
	"api_pagination_default_limit": "api.pagination_default_limit",
	"api_pagination_max_limit": "api.pagination_max_limit",
	"api_body_max_bytes": "api.body_max_bytes",
	"rate_limit_auth_per_minute": "api.rate_limit_auth_per_minute",
	"rate_limit_users_per_minute": "api.rate_limit_users_per_minute",
	"argon2_time_cost": "argon2.time_cost",
	"argon2_memory_cost": "argon2.memory_cost",
	"argon2_parallelism": "argon2.parallelism",
	"todos_api_base_url": "mcp.api_base_url",
	"mcp_allow_destructive": "mcp.allow_destructive",
	"mcp_allow_remote_api": "mcp.allow_remote_api",
}


def _default_env_settings() -> EnvSettings:
	return EnvSettings(
		app_env="local",
		api=ApiSettings(
			host="127.0.0.1",
			port=8000,
			pagination_default_limit=20,
			pagination_max_limit=100,
			body_max_bytes=1_048_576,
			rate_limit_auth_per_minute=20,
			rate_limit_users_per_minute=10,
		),
		jwt=JwtSettings(
			secret_key="test-secret-key-for-pytest-suite-32bytes!",
			algorithm="HS256",
			expire_minutes=60,
			issuer="todos-api",
			audience="todos-client",
		),
		argon2=Argon2Settings(time_cost=3, memory_cost=65536, parallelism=4),
		postgres=PostgresSettings(
			port=5432,
			user="todos",
			db="todos",
			password="local-db-pass",
			url="postgresql+asyncpg://todos:local-db-pass@127.0.0.1:5432/todos",
			test_url="postgresql+asyncpg://todos:todos@127.0.0.1:5432/todos_test",
		),
		valkey=ValkeySettings(
			port=6379,
			password="local-valkey-pass",
			url="valkey://:local-valkey-pass@127.0.0.1:6379/0",
			auth_user_cache_ttl_seconds=120,
		),
		compose=ComposeSettings(infra_bind="127.0.0.1", app_bind="127.0.0.1"),
		mcp=McpSettings(
			api_base_url="http://127.0.0.1:8000",
			allow_destructive=False,
			allow_remote_api=False,
		),
		deploy=DeploySettings(run_migrations=True),
	)


def make_env_settings(**overrides: Any) -> EnvSettings:
	base = _default_env_settings()
	if not overrides:
		return base
	dotted: dict[str, object] = {}
	for key, value in overrides.items():
		path = _FLAT_OVERRIDE_PATHS.get(key, key)
		dotted[path] = value
	return apply_dotted_overrides(base, dotted)
