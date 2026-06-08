import os
import re
from functools import lru_cache
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_env_file = os.getenv("ENV_FILE", ".env")
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


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=_env_file or None, extra="ignore")

	app_env: str = "local"
	database_url: str = "postgresql+asyncpg://todos:changeme@127.0.0.1:5432/todos"
	jwt_secret_key: str
	jwt_algorithm: str = "HS256"
	jwt_expire_minutes: int = 60
	valkey_url: str = "valkey://127.0.0.1:6379/0"
	auth_user_cache_ttl_seconds: int = 120

	@model_validator(mode="after")
	def validate_jwt_configuration(self) -> Self:
		normalized = self.jwt_secret_key.strip().lower()
		if len(self.jwt_secret_key) < MIN_JWT_SECRET_LENGTH:
			msg = f"JWT_SECRET_KEY must be at least {MIN_JWT_SECRET_LENGTH} characters"
			raise ValueError(msg)
		if normalized in WEAK_JWT_SECRETS:
			raise ValueError("JWT_SECRET_KEY must not use a placeholder or weak value")
		for prefix in WEAK_JWT_SECRET_PREFIXES:
			if normalized.startswith(prefix):
				raise ValueError("JWT_SECRET_KEY must not use a placeholder or weak value")
		if re.fullmatch(r"x+", normalized):
			raise ValueError("JWT_SECRET_KEY must not use a placeholder or weak value")
		if self.jwt_algorithm != "HS256":
			raise ValueError("JWT_ALGORITHM must be HS256")
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


@lru_cache
def get_settings() -> Settings:
	return Settings.model_validate({})
