from typing import Any, cast


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
	"""Recursively merge overlay into base. Overlay values win."""
	result = dict(base)
	for key, value in overlay.items():
		existing = result.get(key)
		if isinstance(existing, dict) and isinstance(value, dict):
			result[key] = deep_merge(
				cast(dict[str, Any], existing),
				cast(dict[str, Any], value),
			)
		else:
			result[key] = value
	return result
