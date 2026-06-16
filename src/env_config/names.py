"""Map EnvSettings fields to process / Compose environment variable names."""

from collections.abc import Iterator

from env_config.schema import EnvSettings


ENV_FIELD_NAMES: tuple[tuple[str, str], ...] = (
	("app_env", "APP_ENV"),
	("api.host", "API_HOST"),
	("api.port", "API_PORT"),
	("postgres.port", "POSTGRES_PORT"),
	("valkey.port", "VALKEY_PORT"),
	("compose.infra_bind", "COMPOSE_INFRA_BIND"),
	("compose.app_bind", "COMPOSE_APP_BIND"),
	("postgres.user", "POSTGRES_USER"),
	("postgres.db", "POSTGRES_DB"),
	("postgres.password", "POSTGRES_PASSWORD"),
	("postgres.url", "DATABASE_URL"),
	("valkey.password", "VALKEY_PASSWORD"),
	("valkey.url", "VALKEY_URL"),
	("valkey.auth_user_cache_ttl_seconds", "AUTH_USER_CACHE_TTL_SECONDS"),
	("jwt.secret_key", "JWT_SECRET_KEY"),
	("jwt.algorithm", "JWT_ALGORITHM"),
	("jwt.expire_minutes", "JWT_EXPIRE_MINUTES"),
	("jwt.issuer", "JWT_ISSUER"),
	("jwt.audience", "JWT_AUDIENCE"),
	("deploy.run_migrations", "RUN_MIGRATIONS"),
	("api.pagination_default_limit", "API_PAGINATION_DEFAULT_LIMIT"),
	("api.pagination_max_limit", "API_PAGINATION_MAX_LIMIT"),
	("api.body_max_bytes", "API_BODY_MAX_BYTES"),
	("api.rate_limit_auth_per_minute", "RATE_LIMIT_AUTH_PER_MINUTE"),
	("api.rate_limit_users_per_minute", "RATE_LIMIT_USERS_PER_MINUTE"),
	("argon2.time_cost", "ARGON2_TIME_COST"),
	("argon2.memory_cost", "ARGON2_MEMORY_COST"),
	("argon2.parallelism", "ARGON2_PARALLELISM"),
	("mcp.api_base_url", "TODOS_API_BASE_URL"),
	("mcp.allow_destructive", "MCP_ALLOW_DESTRUCTIVE"),
	("mcp.allow_remote_api", "MCP_ALLOW_REMOTE_API"),
	("postgres.test_url", "TEST_DATABASE_URL"),
)


def get_nested_attr(obj: object, path: str) -> object:
	value = obj
	for part in path.split("."):
		value = getattr(value, part)
	return value


def iter_env_pairs(settings: EnvSettings) -> Iterator[tuple[str, str]]:
	for field_path, env_name in ENV_FIELD_NAMES:
		value = get_nested_attr(settings, field_path)
		if isinstance(value, bool):
			formatted = "true" if value else "false"
		else:
			formatted = str(value)
		yield env_name, formatted
