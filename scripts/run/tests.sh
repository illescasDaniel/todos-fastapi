#!/usr/bin/env bash

set -euo pipefail

run_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scripts_dir="$(cd "${run_script_dir}/.." && pwd)"
script_dir="${scripts_dir}"
repo_root="$(cd "${scripts_dir}/.." && pwd)"
SCRIPT_DIR="${scripts_dir}"

# shellcheck source=scripts/lib.sh
source "${scripts_dir}/lib.sh"

lib_require_venv

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

_tests_postgres_auth_ok() {
	local host="${1:-127.0.0.1}"
	local port="${2:-5432}"
	local user="${3:-todos}"
	local password="${4:-}"
	if [[ -z "${password}" ]]; then
		return 1
	fi
	"${repo_root}/.venv/bin/python" -c "
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
	local preset_test_url="${TEST_DATABASE_URL:-}"

	# shellcheck source=scripts/database/setup.sh
	source "${script_dir}/database/setup.sh"
	database_load_env
	# shellcheck source=scripts/ports.sh
	source "${script_dir}/ports.sh"

	if [[ -z "${preset_test_url}" ]]; then
		if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
			echo "Set POSTGRES_PASSWORD in .env (or export TEST_DATABASE_URL) before running tests." >&2
			exit 1
		fi
		export TEST_DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-todos}:${POSTGRES_PASSWORD}@127.0.0.1:${POSTGRES_PORT}/todos_test"
	else
		export TEST_DATABASE_URL="${preset_test_url}"
	fi

	local test_db_port="${POSTGRES_PORT}"
	local test_db_user="${POSTGRES_USER:-todos}"
	local test_db_password="${POSTGRES_PASSWORD:-}"
	if [[ -n "${TEST_DATABASE_URL:-}" ]]; then
		test_db_port="$(echo "${TEST_DATABASE_URL}" | sed -n 's|.*@[^:]*:\([0-9]*\)/.*|\1|p')"
		test_db_port="${test_db_port:-5432}"
		test_db_user="$(echo "${TEST_DATABASE_URL}" | sed -n 's|.*://\([^:]*\):.*|\1|p')"
		test_db_user="${test_db_user:-todos}"
		test_db_password="$(echo "${TEST_DATABASE_URL}" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')"
		if [[ -n "${test_db_password}" ]]; then
			export POSTGRES_USER="${test_db_user}"
			export POSTGRES_PASSWORD="${test_db_password}"
			export POSTGRES_PORT="${test_db_port}"
		fi
	fi

	if [[ -n "${preset_test_url}" ]]; then
		if _tests_postgres_auth_ok 127.0.0.1 "${test_db_port}" "${test_db_user}" "${test_db_password}"; then
			echo "PostgreSQL is already reachable on 127.0.0.1:${test_db_port} with TEST_DATABASE_URL credentials."
			# shellcheck source=scripts/database/postgresql.sh
			source "${DATABASE_SCRIPTS_DIR}/postgresql.sh"
			if _postgres_container_running; then
				_tests_ensure_test_database todos_test
			fi
			return 0
		fi

		echo "Preparing PostgreSQL for CI-parity tests (credentials from TEST_DATABASE_URL)..."
		# shellcheck source=scripts/database/postgresql.sh
		source "${DATABASE_SCRIPTS_DIR}/postgresql.sh"
		postgres_reset_container
		_tests_started_postgres=true
		trap _tests_cleanup_postgres EXIT INT TERM HUP
		_tests_ensure_test_database todos_test
		return 0
	fi

	if _tests_postgres_port_open 127.0.0.1 "${test_db_port}" \
		&& _tests_postgres_auth_ok 127.0.0.1 "${test_db_port}" "${test_db_user}" "${test_db_password}"; then
		echo "PostgreSQL is already reachable on 127.0.0.1:${test_db_port}."
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
	pytest \
		--cov=todos_app \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		"${args[@]}"
else
	pytest "${args[@]}"
fi
