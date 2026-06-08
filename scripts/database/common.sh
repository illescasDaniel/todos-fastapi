# Shared database helpers for scripts/start.sh, migrate.sh, seed.sh, wipe.sh.
# Source from bash after PROJECT_ROOT is set.

load_database_url() {
	local url_override="${DATABASE_URL:-}"
	if [[ -f "$PROJECT_ROOT/.env" ]]; then
		set -a
		# shellcheck source=/dev/null
		source "$PROJECT_ROOT/.env"
		set +a
	fi
	if [[ -n "$url_override" ]]; then
		DATABASE_URL="$url_override"
	else
		DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://todos:changeme@127.0.0.1:5432/todos}"
	fi
}

database_clear_settings_cache() {
	if [[ ! -d ".venv" ]]; then
		return 0
	fi
	# shellcheck disable=SC1091
	source ".venv/bin/activate"
	PYTHONPATH=src python -c "from todos_app.core.settings import get_settings; get_settings.cache_clear()"
}

database_url_uses_postgres() {
	case "${DATABASE_URL%%://*}" in
	postgresql+* | postgres+*) return 0 ;;
	*) return 1 ;;
	esac
}
