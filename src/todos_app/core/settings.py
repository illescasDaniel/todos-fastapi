import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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


def _repo_root() -> Path:
	return Path(__file__).resolve().parents[3]


def _settings_env_files() -> tuple[str, ...]:
	root = _repo_root()
	override = os.getenv("ENV_FILE", ".env")
	env_path = Path(override) if Path(override).is_absolute() else root / override
	candidates = (
		root / "config" / "ports.env",
		root / "config" / "ports.local.env",
		env_path,
	)
	return tuple(str(path) for path in candidates if path.is_file())


class Settings(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=_settings_env_files() or None,
		extra="ignore",
	)

	app_env: str = "local"
	database_url: str = ""
	postgres_user: str = "todos"
	postgres_db: str = "todos"
	postgres_password: str = ""
	postgres_port: int = 5432
	jwt_secret_key: str
	jwt_algorithm: str = "HS256"
	jwt_expire_minutes: int = 60
	jwt_issuer: str = "todos-api"
	jwt_audience: str = "todos-client"
	valkey_url: str = ""
	valkey_password: str = ""
	valkey_port: int = 6379
	auth_user_cache_ttl_seconds: int = 120

	@model_validator(mode="after")
	def derive_and_validate(self) -> Self:
		if not self.database_url:
			if self.app_env != "local":
				msg = (
					"DATABASE_URL must be explicitly set in non-local environments "
					"(set DATABASE_URL in .env or the environment)"
				)
				raise ValueError(msg)
			if not self.postgres_password:
				raise ValueError("POSTGRES_PASSWORD is required when DATABASE_URL is not set")
			object.__setattr__(
				self,
				"database_url",
				f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
				f"@127.0.0.1:{self.postgres_port}/{self.postgres_db}",
			)
		if not self.valkey_url:
			if self.valkey_password:
				object.__setattr__(
					self,
					"valkey_url",
					f"valkey://:{self.valkey_password}@127.0.0.1:{self.valkey_port}/0",
				)
			else:
				object.__setattr__(self, "valkey_url", f"valkey://127.0.0.1:{self.valkey_port}/0")

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
		if self.app_env != "local" and "changeme" in self.database_url:
			raise ValueError(
				"DATABASE_URL must be explicitly set in non-local environments "
				"(the changeme fallback is not allowed outside local dev)"
			)
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
