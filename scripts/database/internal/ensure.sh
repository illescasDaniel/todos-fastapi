# shellcheck shell=bash
# Ensure PostgreSQL and Valkey are ready (Compose up when needed).
# Source after common.sh; requires PROJECT_ROOT and DATABASE_SCRIPTS_DIR.

database_ensure_ready() {
	# shellcheck source=scripts/database/internal/valkey.sh
	source "$DATABASE_SCRIPTS_DIR/valkey.sh"
	valkey_prepare_for_start

	# shellcheck source=scripts/database/internal/postgresql.sh
	source "$DATABASE_SCRIPTS_DIR/postgresql.sh"
	postgres_prepare_for_start
}

database_uses_container() {
	return 0
}

database_reset_container() {
	# shellcheck source=scripts/database/internal/postgresql.sh
	source "$DATABASE_SCRIPTS_DIR/postgresql.sh"
	postgres_reset_container
}

database_stop() {
	# shellcheck source=scripts/database/internal/postgresql.sh
	source "$DATABASE_SCRIPTS_DIR/postgresql.sh"
	postgres_stop_container

	# shellcheck source=scripts/database/internal/valkey.sh
	source "$DATABASE_SCRIPTS_DIR/valkey.sh"
	valkey_stop_container
}

database_stop_container() {
	local exit_code=$?
	database_stop
	return "$exit_code"
}
