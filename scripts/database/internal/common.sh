# Shared database helpers for scripts/start.sh and scripts/database/*.sh.
# Source from bash after PROJECT_ROOT is set.

load_database_url() {
	local url_override="${DATABASE_URL:-}"
	local valkey_override="${VALKEY_URL:-}"
	local internal_dir="${DATABASE_SCRIPTS_DIR}/../../internal"
	# shellcheck source=scripts/internal/load_env.sh
	source "${internal_dir}/load_env.sh"
	# shellcheck source=scripts/internal/env_urls.sh
	source "${internal_dir}/env_urls.sh"
	env_load_stack
	if [[ -z "$url_override" ]]; then
		env_resolve_database_url
	else
		export DATABASE_URL="$url_override"
	fi
	if [[ -z "$valkey_override" ]]; then
		env_resolve_valkey_url
	else
		export VALKEY_URL="$valkey_override"
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
