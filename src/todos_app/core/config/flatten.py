from collections.abc import Iterator, Mapping
from typing import cast

from todos_app.core.config.schema import EnvSettings


def field_path_to_env_name(field_path: str) -> str:
	"""Map nested settings path to process env name (api.port → API_PORT)."""
	return field_path.upper().replace(".", "_")


def _format_env_value(value: object) -> str:
	if isinstance(value, bool):
		return "true" if value else "false"
	return str(value)


def iter_env_pairs(settings: EnvSettings) -> Iterator[tuple[str, str]]:
	"""Flatten EnvSettings to convention-based KEY=value pairs for shell and Compose."""

	def walk(prefix: str, value: object) -> Iterator[tuple[str, str]]:
		if isinstance(value, Mapping):
			mapping = cast(Mapping[str, object], value)
			for key, nested in mapping.items():
				path = f"{prefix}.{key}" if prefix else key
				yield from walk(path, nested)
			return
		yield field_path_to_env_name(prefix), _format_env_value(value)

	yield from walk("", settings.model_dump())
