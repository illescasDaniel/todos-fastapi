from todos_app.core.config.loader import get_env_settings
from todos_app.core.config.schema import (
	EnvSettings,
)


Settings = EnvSettings


def get_settings() -> EnvSettings:
	return get_env_settings()
