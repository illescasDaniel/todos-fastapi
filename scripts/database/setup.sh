# Shared env loading for start.sh, seed.sh, migrate.sh, wipe.sh.
# Set SCRIPT_DIR to the scripts/ directory before sourcing.

database_load_env() {
	PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
	DATABASE_SCRIPTS_DIR="$SCRIPT_DIR/database"
	cd "$PROJECT_ROOT"
	# shellcheck source=scripts/database/common.sh
	source "$DATABASE_SCRIPTS_DIR/common.sh"
	# shellcheck source=scripts/database/ensure.sh
	source "$DATABASE_SCRIPTS_DIR/ensure.sh"
	load_database_url
}
