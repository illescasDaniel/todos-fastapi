"""CI and pytest profile — safe non-production values."""

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


api_host = "127.0.0.1"
api_port = 8000
postgres_port = 5432
valkey_port = 6379
compose_infra_bind = "127.0.0.1"
compose_app_bind = "127.0.0.1"

postgres_user = "todos"
postgres_db = "todos_test"
postgres_password = "todos"
valkey_password = "test-valkey-password-for-ci"

settings = EnvSettings(
	app_env="local",
	api=ApiSettings(
		host=api_host,
		port=api_port,
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
		port=postgres_port,
		user=postgres_user,
		db=postgres_db,
		password=postgres_password,
		url=f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{api_host}:{postgres_port}/{postgres_db}",
		test_url=f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{api_host}:{postgres_port}/{postgres_db}",
	),
	valkey=ValkeySettings(
		port=valkey_port,
		password=valkey_password,
		url=f"valkey://:{valkey_password}@{api_host}:{valkey_port}/0",
		auth_user_cache_ttl_seconds=120,
	),
	compose=ComposeSettings(infra_bind=compose_infra_bind, app_bind=compose_app_bind),
	mcp=McpSettings(
		api_base_url=f"http://{api_host}:{api_port}",
		allow_destructive=False,
		allow_remote_api=False,
	),
	deploy=DeploySettings(run_migrations=True),
)
