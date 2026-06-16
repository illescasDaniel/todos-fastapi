# shellcheck shell=bash
# Shared database helpers for scripts/start.sh and scripts/database/*.sh.
# Source from bash after PROJECT_ROOT is set.

load_database_url() {
	local internal_dir="${DATABASE_SCRIPTS_DIR}/../../internal"
	# shellcheck source=scripts/internal/load_env.sh
	source "${internal_dir}/load_env.sh"
	env_load_stack
}

database_clear_settings_cache() {
	if [[ ! -d ".venv" ]]; then
		return 0
	fi
	# shellcheck disable=SC1091
	source ".venv/bin/activate"
	PYTHONPATH=src python -c "from env_config.loader import clear_env_settings_cache; clear_env_settings_cache()"
}

database_url_uses_postgres() {
	case "${DATABASE_URL%%://*}" in
	postgresql+* | postgres+*) return 0 ;;
	*) return 1 ;;
	esac
}
