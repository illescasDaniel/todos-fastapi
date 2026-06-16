import importlib
import os
import re
from functools import lru_cache
from typing import Literal, get_args, get_origin

from pydantic import BaseModel

from env_config.names import ENV_FIELD_NAMES, iter_env_pairs
from env_config.schema import EnvSettings


_PROFILE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")

_RESERVED_PROFILES = frozenset({"example"})

_PROFILE_FIX_HINTS: dict[str, str] = {
	"local": (
		"Missing profiles/local.py.\n"
		"Copy the template on the host:\n"
		"  cp src/env_config/profiles/example.py src/env_config/profiles/local.py\n"
		"Edit secrets, export ENV_PROFILE=local, then rebuild the app image:\n"
		"  ./scripts/container/up.sh"
	),
	"production": (
		"Missing profiles/production.py.\n"
		"Copy the template on the deploy host:\n"
		"  cp src/env_config/profiles/production.example.py "
		"src/env_config/profiles/production.py\n"
		"Edit secrets, export ENV_PROFILE=production, then rebuild:\n"
		"  ./scripts/container/deploy.sh"
	),
}


def _require_profile() -> str:
	profile = os.environ.get("ENV_PROFILE")
	if not profile:
		msg = (
			"ENV_PROFILE is not set. "
			"Export a profile name that matches src/env_config/profiles/<name>.py, "
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
			f"ENV_PROFILE={profile!r} is reserved (template module). "
			"Copy src/env_config/profiles/example.py to a new profile file "
			"and export that name instead."
		)
		raise RuntimeError(msg)
	return profile


def apply_to_environ(settings: EnvSettings) -> None:
	for env_name, value in iter_env_pairs(settings):
		os.environ[env_name] = value


def _resolve_field_annotation(path: str) -> type[object]:
	parts = path.split(".")
	model: type[BaseModel] = EnvSettings
	for part in parts[:-1]:
		field = model.model_fields[part]
		annotation = field.annotation
		if not isinstance(annotation, type) or not issubclass(annotation, BaseModel):
			msg = f"Expected nested settings model at {part!r} in {path!r}"
			raise TypeError(msg)
		model = annotation
	field = model.model_fields[parts[-1]]
	annotation = field.annotation
	if annotation is None:
		msg = f"Missing annotation for settings field {path!r}"
		raise TypeError(msg)
	origin = get_origin(annotation)
	if origin is Literal:
		return str
	if origin is not None:
		args = get_args(annotation)
		if args:
			annotation = args[0]
	if not isinstance(annotation, type):
		msg = f"Unsupported settings field type for {path!r}"
		raise TypeError(msg)
	return annotation


def _parse_env_override(path: str, raw: str) -> object:
	annotation = _resolve_field_annotation(path)
	if annotation is bool:
		return raw.lower() in ("1", "true", "yes")
	if annotation is int:
		return int(raw)
	return raw


def apply_dotted_overrides(base: EnvSettings, overrides: dict[str, object]) -> EnvSettings:
	data = base.model_dump()
	for path, value in overrides.items():
		parts = path.split(".")
		target = data
		for part in parts[:-1]:
			target = target[part]
		target[parts[-1]] = value
	return EnvSettings.model_validate(data)


def _merge_profile_with_environ(profile: str) -> EnvSettings:
	"""Profile module is source of truth; process env overrides win (Compose / orchestrator)."""
	base = _load_profile_settings(profile)
	overrides: dict[str, object] = {}
	for field_path, env_name in ENV_FIELD_NAMES:
		raw = os.environ.get(env_name)
		if raw is None or raw == "":
			continue
		overrides[field_path] = _parse_env_override(field_path, raw)
	if not overrides:
		return base
	return apply_dotted_overrides(base, overrides)


def _missing_profile_message(profile: str) -> str:
	if hint := _PROFILE_FIX_HINTS.get(profile):
		return hint
	return (
		f"Missing env profile module: env_config.profiles.{profile}\n"
		f"Create src/env_config/profiles/{profile}.py with settings = EnvSettings(...), "
		f"then export ENV_PROFILE={profile}"
	)


def _load_profile_settings(profile: str) -> EnvSettings:
	module_path = f"env_config.profiles.{profile}"
	try:
		module = importlib.import_module(module_path)
	except ModuleNotFoundError as exc:
		raise RuntimeError(_missing_profile_message(profile)) from exc

	raw = getattr(module, "settings", None)
	if not isinstance(raw, EnvSettings):
		msg = f"{module_path} must define settings = EnvSettings(...)"
		raise RuntimeError(msg)
	return raw


@lru_cache
def get_profile_settings() -> EnvSettings:
	"""Profile module values only — for export to shell/.env (no process env merge)."""
	return _load_profile_settings(_require_profile())


@lru_cache
def get_env_settings() -> EnvSettings:
	profile = _require_profile()
	settings = _merge_profile_with_environ(profile)
	apply_to_environ(settings)
	return settings


def clear_env_settings_cache() -> None:
	get_env_settings.cache_clear()
	get_profile_settings.cache_clear()
