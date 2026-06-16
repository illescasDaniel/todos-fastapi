import pytest

from todos_app.core.config.merge import deep_merge


pytestmark = pytest.mark.unit


def test_deep_merge_overlays_nested_sections() -> None:
	base = {
		"app_env": "local",
		"api": {"host": "127.0.0.1", "port": 8000},
		"postgres": {"db": "todos", "password": "base"},
	}
	overlay = {
		"postgres": {"password": "overlay", "url": "postgresql+asyncpg://x"},
		"jwt": {"secret_key": "x" * 32},
	}

	merged = deep_merge(base, overlay)

	assert merged["app_env"] == "local"
	assert merged["api"] == {"host": "127.0.0.1", "port": 8000}
	assert merged["postgres"] == {
		"db": "todos",
		"password": "overlay",
		"url": "postgresql+asyncpg://x",
	}
	assert merged["jwt"] == {"secret_key": "x" * 32}
