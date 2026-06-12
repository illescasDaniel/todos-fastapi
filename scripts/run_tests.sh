#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
SCRIPT_DIR="${script_dir}"

if [[ ! -d "${repo_root}/.venv" ]]; then
	echo "Missing .venv. Create it first: python3 -m venv .venv"
	exit 1
fi

coverage=false
args=()
for arg in "$@"; do
	case "${arg}" in
		--coverage)
			coverage=true
			;;
		*)
			args+=("${arg}")
			;;
	esac
done

_tests_started_postgres=false

_tests_postgres_port_open() {
	local host="${1:-127.0.0.1}"
	local port="${2:-5432}"
	if command -v pg_isready &>/dev/null; then
		pg_isready -h "$host" -p "$port" -U "${POSTGRES_USER:-todos}" &>/dev/null
		return $?
	fi
	(timeout 1 bash -c "echo > /dev/tcp/${host}/${port}") &>/dev/null
}

_tests_ensure_test_database() {
	local db="${1:-todos_test}"
	# shellcheck source=scripts/database/infra_compose.sh
	source "${DATABASE_SCRIPTS_DIR}/infra_compose.sh"
	if infra_compose exec -T postgres psql -U "${POSTGRES_USER:-todos}" -d postgres -tAc \
		"SELECT 1 FROM pg_database WHERE datname = '${db}'" | grep -q 1; then
		return 0
	fi
	echo "Creating PostgreSQL test database '${db}'..."
	infra_compose exec -T postgres psql -U "${POSTGRES_USER:-todos}" -d postgres -c "CREATE DATABASE ${db};"
}

_tests_cleanup_postgres() {
	local exit_code=$?
	if [[ "${_tests_started_postgres}" == true ]]; then
		# shellcheck source=scripts/database/postgresql.sh
		source "${DATABASE_SCRIPTS_DIR}/postgresql.sh"
		postgres_stop_container || true
	fi
	exit "$exit_code"
}

_tests_bootstrap_postgres() {
	# shellcheck source=scripts/database/setup.sh
	source "${script_dir}/database/setup.sh"
	database_load_env
	# shellcheck source=scripts/ports.sh
	source "${script_dir}/ports.sh"

	if [[ -z "${TEST_DATABASE_URL:-}" ]]; then
		if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
			echo "Set POSTGRES_PASSWORD in .env (or export TEST_DATABASE_URL) before running tests." >&2
			exit 1
		fi
		export TEST_DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-todos}:${POSTGRES_PASSWORD}@127.0.0.1:${POSTGRES_PORT}/todos_test"
	fi

	if _tests_postgres_port_open 127.0.0.1 "$POSTGRES_PORT"; then
		echo "PostgreSQL is already reachable on 127.0.0.1:${POSTGRES_PORT}."
		# shellcheck source=scripts/database/postgresql.sh
		source "${DATABASE_SCRIPTS_DIR}/postgresql.sh"
		if _postgres_container_running; then
			_tests_ensure_test_database todos_test
		fi
		return 0
	fi

	# shellcheck source=scripts/database/postgresql.sh
	source "${DATABASE_SCRIPTS_DIR}/postgresql.sh"
	postgres_prepare_for_start
	_tests_started_postgres=true
	trap _tests_cleanup_postgres EXIT INT TERM HUP
	_tests_ensure_test_database todos_test
}

_tests_bootstrap_postgres

cd "${repo_root}"
source ".venv/bin/activate"

if [[ "${coverage}" == true ]]; then
	"${script_dir}/run_coverage.sh" "${args[@]}"
else
	pytest "${args[@]}"
fi
