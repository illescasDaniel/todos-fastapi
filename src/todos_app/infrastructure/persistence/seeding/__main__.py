from todos_app.core.settings import get_settings
from todos_app.infrastructure.persistence.seeding.runner import reset_and_seed_defaults


def main() -> None:
	get_settings.cache_clear()
	reset_and_seed_defaults()
	print("Local database was reset and seeded with default users and todos.")


if __name__ == "__main__":
	main()
