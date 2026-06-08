# PostgreSQL Podman lifecycle via docker-compose.infra.yml (infra-only).
# Expects PROJECT_ROOT; sources infra_compose.sh.

POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-todos-postgres}"

_postgres_container_running() {
	podman container inspect "$POSTGRES_CONTAINER_NAME" --format '{{.State.Status}}' 2>/dev/null | grep -qx running
}

_postgres_wait_for_ready() {
	local retries=30
	echo "Waiting for PostgreSQL to accept connections..."
	while (( retries > 0 )); do
		if (
			cd "$PROJECT_ROOT"
			infra_compose exec -T postgres pg_isready -U "${POSTGRES_USER:-todos}" -d "${POSTGRES_DB:-todos}"
		) &>/dev/null; then
			return 0
		fi
		sleep 1
		(( retries-- )) || true
	done
	echo "PostgreSQL container did not become ready in time." >&2
	return 1
}

postgres_prepare_for_start() {
	# shellcheck source=scripts/database/infra_compose.sh
	source "$DATABASE_SCRIPTS_DIR/infra_compose.sh"

	if _postgres_container_running; then
		echo "PostgreSQL container already running."
		return 0
	fi

	echo "Starting PostgreSQL container..."
	(
		cd "$PROJECT_ROOT"
		infra_compose up -d postgres
	)
	_postgres_wait_for_ready
}

postgres_reset_container() {
	# shellcheck source=scripts/database/infra_compose.sh
	source "$DATABASE_SCRIPTS_DIR/infra_compose.sh"

	echo "Resetting PostgreSQL container (recreate volume with current POSTGRES_PASSWORD)..."
	(
		cd "$PROJECT_ROOT"
		infra_compose rm -fsv postgres 2>/dev/null || true
		infra_compose up -d postgres
	)
	_postgres_wait_for_ready
}

postgres_stop_container() {
	# shellcheck source=scripts/database/infra_compose.sh
	source "$DATABASE_SCRIPTS_DIR/infra_compose.sh"

	if ! _postgres_container_running; then
		echo "PostgreSQL container is not running."
		return 0
	fi
	echo "Stopping PostgreSQL container..."
	(
		cd "$PROJECT_ROOT"
		infra_compose stop postgres
	) || true
}

postgres_cleanup_on_exit() {
	local exit_code=$?
	postgres_stop_container
	return "$exit_code"
}
