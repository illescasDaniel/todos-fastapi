import re
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator


MIN_JWT_SECRET_LENGTH = 32
WEAK_JWT_SECRET_PREFIXES = ("change-me", "your-secret")
WEAK_JWT_SECRETS = frozenset(
	{
		"change-me-generate-a-secure-random-value",
		"changeme",
		"secret",
		"your-secret-key",
		"local-dev-migrate-placeholder-secret",
		"container-migrate-placeholder-secret",
	}
)

AppEnv = Literal["local", "staging", "production"]
JwtAlgorithm = Literal["HS256"]


class ApiSettings(BaseModel):
	host: str
	port: int = Field(ge=1, le=65535)
	pagination_default_limit: int = Field(ge=1)
	pagination_max_limit: int = Field(ge=1)
	body_max_bytes: int = Field(gt=0)
	rate_limit_auth_per_minute: int = Field(gt=0)
	rate_limit_users_per_minute: int = Field(gt=0)

	@model_validator(mode="after")
	def validate_pagination_limits(self) -> Self:
		if self.pagination_max_limit < self.pagination_default_limit:
			raise ValueError("pagination_max_limit must be greater than or equal to pagination_default_limit")
		return self


class JwtSettings(BaseModel):
	secret_key: str
	algorithm: JwtAlgorithm
	expire_minutes: int = Field(gt=0)
	issuer: str
	audience: str

	@field_validator("secret_key")
	@classmethod
	def validate_secret_key(cls, value: str) -> str:
		normalized = value.strip().lower()
		if len(value) < MIN_JWT_SECRET_LENGTH:
			msg = f"JWT_SECRET_KEY must be at least {MIN_JWT_SECRET_LENGTH} characters"
			raise ValueError(msg)
		if normalized in WEAK_JWT_SECRETS:
			raise ValueError("JWT_SECRET_KEY must not use a placeholder or weak value")
		for prefix in WEAK_JWT_SECRET_PREFIXES:
			if normalized.startswith(prefix):
				raise ValueError("JWT_SECRET_KEY must not use a placeholder or weak value")
		if re.fullmatch(r"x+", normalized):
			raise ValueError("JWT_SECRET_KEY must not use a placeholder or weak value")
		return value


class Argon2Settings(BaseModel):
	time_cost: int = Field(gt=0)
	memory_cost: int = Field(gt=0)
	parallelism: int = Field(gt=0)


class PostgresSettings(BaseModel):
	port: int = Field(ge=1, le=65535)
	user: str
	db: str
	password: str
	url: str
	test_url: str


class ValkeySettings(BaseModel):
	port: int = Field(ge=1, le=65535)
	password: str
	url: str
	auth_user_cache_ttl_seconds: int = Field(gt=0)


class ComposeSettings(BaseModel):
	infra_bind: str
	app_bind: str


class McpSettings(BaseModel):
	api_base_url: str
	allow_destructive: bool
	allow_remote_api: bool


class DeploySettings(BaseModel):
	run_migrations: bool


class EnvSettings(BaseModel):
	"""Runtime configuration. Values live in env profiles — no field defaults here."""

	app_env: AppEnv
	api: ApiSettings
	jwt: JwtSettings
	argon2: Argon2Settings
	postgres: PostgresSettings
	valkey: ValkeySettings
	compose: ComposeSettings
	mcp: McpSettings
	deploy: DeploySettings

	@model_validator(mode="after")
	def validate_production_urls(self) -> Self:
		if self.app_env != "local" and "127.0.0.1" in self.postgres.url:
			raise ValueError(
				"DATABASE_URL must not use loopback in non-local profiles "
				"(set managed DATABASE_URL in profiles/production.py)"
			)
		if self.app_env != "local" and "changeme" in self.postgres.url.lower():
			raise ValueError("DATABASE_URL must not use placeholder values outside local profiles")
		return self

	def is_local(self) -> bool:
		return self.app_env == "local"

	def is_staging(self) -> bool:
		return self.app_env == "staging"

	def is_production(self) -> bool:
		return self.app_env == "production"

	def exposes_error_details(self) -> bool:
		return self.is_local()

	def exposes_api_docs(self) -> bool:
		return self.is_local()
