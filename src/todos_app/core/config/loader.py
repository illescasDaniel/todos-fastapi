import os
import re
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import cast

from todos_app.core.config.merge import deep_merge
from todos_app.core.config.schema import EnvSettings


_PROFILE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")

_RESERVED_PROFILES = frozenset({"example"})

_PROFILE_FIX_HINTS: dict[str, str] = {
	"local": (
		"Missing config/profiles/local.toml.\n"
		"Copy the template on the host:\n"
		"  cp config/profiles/example.toml config/profiles/local.toml\n"
		"Edit secrets, export ENV_PROFILE=local, then rebuild the app image:\n"
		"  ./scripts/container/up.sh"
	),
	"production": (
		"Missing config/profiles/production.toml.\n"
		"Copy the template on the deploy host:\n"
		"  cp config/profiles/production.example.toml config/profiles/production.toml\n"
		"Edit secrets, export ENV_PROFILE=production, then rebuild:\n"
		"  ./scripts/container/deploy.sh"
	),
}


def _find_repo_root() -> Path:
	if raw := os.environ.get("TODOS_REPO_ROOT"):
		root = Path(raw).resolve()
		if not (root / "config" / "base.toml").is_file():
			msg = f"TODOS_REPO_ROOT={root} does not contain config/base.toml"
			raise RuntimeError(msg)
		return root

	start = Path(__file__).resolve().parent
	for parent in (start, *start.parents):
		if (parent / "config" / "base.toml").is_file():
			return parent

	msg = "Could not find config/base.toml. Run from the repository tree or set TODOS_REPO_ROOT to the project root."
	raise RuntimeError(msg)


def _config_root() -> Path:
	if raw := os.environ.get("TODOS_CONFIG_DIR"):
		return Path(raw).resolve()
	return _find_repo_root() / "config"


def _profiles_dir() -> Path:
	return _config_root() / "profiles"


def _require_profile() -> str:
	profile = os.environ.get("ENV_PROFILE")
	if not profile:
		msg = (
			"ENV_PROFILE is not set. "
			"Export a profile name that matches config/profiles/<name>.toml, "
			"for example: export ENV_PROFILE=local"
		)
		raise RuntimeError(msg)
	if not _PROFILE_NAME_RE.match(profile):
		msg = (
			f"ENV_PROFILE={profile!r} is invalid. "
			"Use a lowercase identifier: letters, digits, underscores; "
			"must start with a letter (e.g. local, local2, production)."
		)
		raise RuntimeError(msg)
	if profile in _RESERVED_PROFILES:
		msg = (
			f"ENV_PROFILE={profile!r} is reserved (template overlay). "
			"Copy config/profiles/example.toml to a new profile file "
			"and export that name instead."
		)
		raise RuntimeError(msg)
	return profile


def _load_toml(path: Path) -> dict[str, object]:
	with path.open("rb") as handle:
		return tomllib.load(handle)


def _missing_profile_message(profile: str) -> str:
	if hint := _PROFILE_FIX_HINTS.get(profile):
		return hint
	return (
		f"Missing env profile overlay: config/profiles/{profile}.toml\n"
		f"Create config/profiles/{profile}.toml (stacked on config/base.toml), "
		f"then export ENV_PROFILE={profile}"
	)


def _require_compose_url(section: dict[str, object], env_name: str) -> str:
	raw = section.get("compose_url")
	if not isinstance(raw, str) or not raw.strip():
		msg = (
			f"{env_name} is required when TODOS_COMPOSE=1. "
			f"Set postgres.compose_url / valkey.compose_url in config/profiles/{_require_profile()}.toml"
		)
		raise RuntimeError(msg)
	return raw


def _apply_compose_urls(data: dict[str, object]) -> None:
	postgres = data.get("postgres")
	valkey = data.get("valkey")
	if not isinstance(postgres, dict):
		msg = "Invalid profile data: expected [postgres] table"
		raise RuntimeError(msg)
	if not isinstance(valkey, dict):
		msg = "Invalid profile data: expected [valkey] table"
		raise RuntimeError(msg)
	postgres_section = cast(dict[str, object], postgres)
	valkey_section = cast(dict[str, object], valkey)
	postgres_section["url"] = _require_compose_url(postgres_section, "POSTGRES_COMPOSE_URL")
	valkey_section["url"] = _require_compose_url(valkey_section, "VALKEY_COMPOSE_URL")


def _load_profile_data(profile: str, *, resolve_compose_urls: bool) -> dict[str, object]:
	base_path = _config_root() / "base.toml"
	if not base_path.is_file():
		msg = f"Missing base config: {base_path}"
		raise RuntimeError(msg)

	overlay_path = _profiles_dir() / f"{profile}.toml"
	if not overlay_path.is_file():
		raise RuntimeError(_missing_profile_message(profile))

	data = deep_merge(_load_toml(base_path), _load_toml(overlay_path))
	if resolve_compose_urls:
		_apply_compose_urls(data)
	return data


def _load_settings(profile: str, *, resolve_compose_urls: bool) -> EnvSettings:
	return EnvSettings.model_validate(_load_profile_data(profile, resolve_compose_urls=resolve_compose_urls))


def apply_dotted_overrides(base: EnvSettings, overrides: dict[str, object]) -> EnvSettings:
	data = base.model_dump()
	for path, value in overrides.items():
		parts = path.split(".")
		target = data
		for part in parts[:-1]:
			target = target[part]
		target[parts[-1]] = value
	return EnvSettings.model_validate(data)


@lru_cache
def get_profile_settings() -> EnvSettings:
	"""Merged base + profile TOML — host URLs for export (postgres.url, not compose_url)."""
	return _load_settings(_require_profile(), resolve_compose_urls=False)


@lru_cache
def get_env_settings() -> EnvSettings:
	"""Runtime settings; uses compose_url as postgres.url / valkey.url when TODOS_COMPOSE=1."""
	resolve_compose_urls = os.environ.get("TODOS_COMPOSE") == "1"
	return _load_settings(_require_profile(), resolve_compose_urls=resolve_compose_urls)


def clear_env_settings_cache() -> None:
	get_env_settings.cache_clear()
	get_profile_settings.cache_clear()
