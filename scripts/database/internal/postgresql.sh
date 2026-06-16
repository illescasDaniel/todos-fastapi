# shellcheck shell=bash
# PostgreSQL Podman lifecycle via docker-compose.infra.yml (infra-only).
# Expects PROJECT_ROOT; sources infra_compose.sh.

POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-todos-postgres}"

_postgres_container_running() {
	podman container inspect "$POSTGRES_CONTAINER_NAME" --format '{{.State.Status}}' 2>/dev/null | grep -qx running
}

_postgres_auth_ok() {
	local host="127.0.0.1"
	local port="${POSTGRES_PORT:?set POSTGRES_PORT in env profile}"
	local user="${POSTGRES_USER:?set POSTGRES_USER in env profile}"
	local password="${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in env profile}"
	if [[ -z "${password}" ]]; then
		return 1
	fi
	"${PROJECT_ROOT}/.venv/bin/python" -c "
import asyncio
import asyncpg
import sys

async def main() -> None:
	try:
		conn = await asyncpg.connect(
			host='${host}',
			port=${port},
			user='${user}',
			password='${password}',
			database='postgres',
		)
		await conn.close()
	except Exception:
		sys.exit(1)

asyncio.run(main())
" 2>/dev/null
}

_postgres_wait_for_ready() {
	local retries=30
	echo "Waiting for PostgreSQL to accept connections..."
	while ((retries > 0)); do
		if (
			cd "$PROJECT_ROOT" || exit
			infra_compose exec -T postgres pg_isready -U "${POSTGRES_USER:?set POSTGRES_USER in .env}" -d "${POSTGRES_DB:?set POSTGRES_DB in .env}"
		) &>/dev/null; then
			return 0
		fi
		sleep 1
		((retries--)) || true
	done
	echo "PostgreSQL container did not become ready in time." >&2
	return 1
}

postgres_prepare_for_start() {
	# shellcheck source=scripts/database/internal/infra_compose.sh
	source "$DATABASE_SCRIPTS_DIR/infra_compose.sh"

	if _postgres_container_running; then
		if _postgres_auth_ok; then
			echo "PostgreSQL container already running."
			return 0
		fi
		echo "PostgreSQL credentials do not match env profile; recreating container..."
		postgres_reset_container
		return 0
	fi

	echo "Starting PostgreSQL container..."
	(
		cd "$PROJECT_ROOT" || exit
		infra_compose up -d postgres
	)
	_postgres_wait_for_ready
	if ! _postgres_auth_ok; then
		echo "PostgreSQL volume credentials do not match env profile; recreating container..."
		postgres_reset_container
	fi
}

postgres_reset_container() {
	# shellcheck source=scripts/database/internal/infra_compose.sh
	source "$DATABASE_SCRIPTS_DIR/infra_compose.sh"

	echo "Resetting PostgreSQL container (recreate volume with current POSTGRES_PASSWORD)..."
	(
		cd "$PROJECT_ROOT" || exit
		infra_compose stop postgres 2>/dev/null || true
		# Path B app container shares the infra network and blocks postgres removal.
		podman stop todos-app 2>/dev/null || true
		podman rm -f todos-app "${POSTGRES_CONTAINER_NAME}" 2>/dev/null || true
		podman volume rm -f todos_todos-postgres-data postgresql_todos-postgres-data 2>/dev/null || true
		infra_compose up -d postgres
	)
	_postgres_wait_for_ready
}

postgres_stop_container() {
	# shellcheck source=scripts/database/internal/infra_compose.sh
	source "$DATABASE_SCRIPTS_DIR/infra_compose.sh"

	if ! _postgres_container_running; then
		echo "PostgreSQL container is not running."
		return 0
	fi
	echo "Stopping PostgreSQL container..."
	(
		cd "$PROJECT_ROOT" || exit
		infra_compose stop postgres
	) || true
}

postgres_cleanup_on_exit() {
	local exit_code=$?
	postgres_stop_container
	return "$exit_code"
}
