from todos_app.shared.config.loader import get_env_settings
from todos_app.shared.config.schema import (
	EnvSettings,
)


Settings = EnvSettings


def get_settings() -> EnvSettings:
	return get_env_settings()
