# Shared database helpers for scripts/start.sh, migrate.sh, seed.sh, wipe.sh.
# Source from bash after PROJECT_ROOT is set.

_safe_source_env() {
	local env_file="$1"
	local key value
	while IFS='=' read -r key value; do
		[[ "$key" =~ ^[[:space:]]*# ]] && continue
		[[ -z "$key" ]] && continue
		key="${key## }"
		key="${key%% }"
		if [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
			export "$key"="$value"
		fi
	done < "$env_file"
}

load_database_url() {
	local url_override="${DATABASE_URL:-}"
	# shellcheck source=scripts/ports.sh
	source "$DATABASE_SCRIPTS_DIR/../ports.sh"
	if [[ -f "$PROJECT_ROOT/.env" ]]; then
		_safe_source_env "$PROJECT_ROOT/.env"
	fi
	if [[ -n "$url_override" ]]; then
		DATABASE_URL="$url_override"
	else
		if [[ -z "${DATABASE_URL:-}" ]]; then
			echo "ERROR: DATABASE_URL not set and no .env found. Set DATABASE_URL in .env." >&2
			exit 1
		fi
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
