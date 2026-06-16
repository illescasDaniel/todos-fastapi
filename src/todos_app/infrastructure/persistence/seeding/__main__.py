from todos_app.core.config.loader import clear_env_settings_cache
from todos_app.infrastructure.persistence.seeding.runner import reset_and_seed_defaults


def main() -> None:
	clear_env_settings_cache()
	reset_and_seed_defaults()
	print("Local database was reset and seeded with default users and todos.")


if __name__ == "__main__":
	main()
