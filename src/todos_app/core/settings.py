from env_config.loader import clear_env_settings_cache, get_env_settings
from env_config.schema import EnvSettings


Settings = EnvSettings


def get_settings() -> EnvSettings:
	return get_env_settings()


__all__ = ["Settings", "clear_env_settings_cache", "get_settings"]
