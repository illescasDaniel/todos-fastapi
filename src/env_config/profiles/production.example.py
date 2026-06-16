"""Copy to profiles/production.py on the deploy host — never commit filled production profiles."""

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
valkey_port = 6380
compose_infra_bind = "127.0.0.1"
compose_app_bind = "127.0.0.1"

db_host = "db-host.example.com"
cache_host = "cache-host.example.com"
postgres_user = "todos"
postgres_db = "todos"
postgres_password = "change-me"
valkey_password = "change-me-valkey-password"

settings = EnvSettings(
	app_env="production",
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
		secret_key="change-me-generate-a-secure-random-value",
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
		url=f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{db_host}:{postgres_port}/{postgres_db}",
		test_url=f"postgresql+asyncpg://{postgres_user}:{postgres_password}@{api_host}:{postgres_port}/todos_test",
	),
	valkey=ValkeySettings(
		port=valkey_port,
		password=valkey_password,
		url=f"rediss://:{valkey_password}@{cache_host}:{valkey_port}/0",
		auth_user_cache_ttl_seconds=120,
	),
	compose=ComposeSettings(infra_bind=compose_infra_bind, app_bind=compose_app_bind),
	mcp=McpSettings(
		api_base_url="https://api.example.com",
		allow_destructive=False,
		allow_remote_api=False,
	),
	deploy=DeploySettings(run_migrations=False),
)
