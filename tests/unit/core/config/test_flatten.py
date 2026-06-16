import pytest

from env_helpers import make_env_settings
from todos_app.core.config.flatten import field_path_to_env_name, iter_env_pairs


pytestmark = pytest.mark.unit


def test_field_path_to_env_name_uses_uppercase_sections() -> None:
	assert field_path_to_env_name("api.port") == "API_PORT"
	assert field_path_to_env_name("postgres.url") == "POSTGRES_URL"
	assert field_path_to_env_name("app_env") == "APP_ENV"


def test_iter_env_pairs_flattens_nested_settings_with_convention_names() -> None:
	settings = make_env_settings()
	pairs = dict(iter_env_pairs(settings))
	assert pairs["API_PORT"] == "8000"
	assert pairs["POSTGRES_URL"] == settings.postgres.url
	assert pairs["JWT_SECRET_KEY"] == settings.jwt.secret_key
	assert pairs["DEPLOY_RUN_MIGRATIONS"] == "true"
	assert pairs["MCP_API_BASE_URL"] == settings.mcp.api_base_url
