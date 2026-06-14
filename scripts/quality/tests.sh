#!/usr/bin/env bash

set -euo pipefail

quality_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scripts_dir="$(cd "${quality_dir}/.." && pwd)"
script_dir="${scripts_dir}"
repo_root="$(cd "${scripts_dir}/.." && pwd)"
SCRIPT_DIR="${scripts_dir}"

# shellcheck source=scripts/quality/internal/lib.sh
source "${quality_dir}/internal/lib.sh"

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
		pg_isready -h "$host" -p "$port" -U "${POSTGRES_USER:?set POSTGRES_USER in .env}" &>/dev/null
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
	# shellcheck source=scripts/database/internal/infra_compose.sh
	source "${DATABASE_SCRIPTS_DIR}/infra_compose.sh"
	if infra_compose exec -T postgres psql -U "${POSTGRES_USER:?set POSTGRES_USER in .env}" -d postgres -tAc \
		"SELECT 1 FROM pg_database WHERE datname = '${db}'" | grep -q 1; then
		return 0
	fi
	echo "Creating PostgreSQL test database '${db}'..."
	infra_compose exec -T postgres psql -U "${POSTGRES_USER:?set POSTGRES_USER in .env}" -d postgres -c "CREATE DATABASE ${db};"
}

_tests_cleanup_postgres() {
	local exit_code=$?
	if [[ "${_tests_started_postgres}" == true ]]; then
		# shellcheck source=scripts/database/internal/postgresql.sh
		source "${DATABASE_SCRIPTS_DIR}/postgresql.sh"
		postgres_stop_container || true
	fi
	exit "$exit_code"
}

_tests_apply_test_database_url() {
	local url="$1"
	local parsed_port parsed_user parsed_password parsed_db
	parsed_port="$(echo "${url}" | sed -n 's|.*@[^:]*:\([0-9]*\)/.*|\1|p')"
	parsed_user="$(echo "${url}" | sed -n 's|.*://\([^:]*\):.*|\1|p')"
	parsed_password="$(echo "${url}" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')"
	parsed_db="$(echo "${url}" | sed -n 's|.*/\([^/?]*\)\(?:\?.*\)\?$|\1|p')"
	if [[ -z "${parsed_port}" || -z "${parsed_user}" || -z "${parsed_password}" || -z "${parsed_db}" ]]; then
		echo "Invalid TEST_DATABASE_URL: ${url}" >&2
		exit 1
	fi
	export POSTGRES_USER="${parsed_user}"
	export POSTGRES_PASSWORD="${parsed_password}"
	export POSTGRES_PORT="${parsed_port}"
	export POSTGRES_DB="${parsed_db}"
	export TEST_DATABASE_URL="${url}"
}

_tests_bootstrap_postgres() {
	local preset_test_url="${TEST_DATABASE_URL:-}"

	if [[ -n "${preset_test_url}" ]]; then
		export DATABASE_URL="${preset_test_url}"
	fi

	# shellcheck source=scripts/database/internal/setup.sh
	source "${script_dir}/database/internal/setup.sh"
	database_load_env
	# shellcheck source=scripts/internal/ports.sh
	source "${script_dir}/internal/ports.sh"

	local test_db_port test_db_user test_db_password
	if [[ -n "${preset_test_url}" ]]; then
		_tests_apply_test_database_url "${preset_test_url}"
		test_db_port="${POSTGRES_PORT}"
		test_db_user="${POSTGRES_USER}"
		test_db_password="${POSTGRES_PASSWORD}"
	else
		if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
			echo "Set POSTGRES_PASSWORD in .env (or export TEST_DATABASE_URL) before running tests." >&2
			exit 1
		fi
		export TEST_DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:?set POSTGRES_USER in .env}:${POSTGRES_PASSWORD}@127.0.0.1:${POSTGRES_PORT:?set POSTGRES_PORT in config/ports.env}/todos_test"
		test_db_port="${POSTGRES_PORT}"
		test_db_user="${POSTGRES_USER:?set POSTGRES_USER in .env}"
		test_db_password="${POSTGRES_PASSWORD}"
	fi

	if [[ -n "${preset_test_url}" ]]; then
		if _tests_postgres_auth_ok 127.0.0.1 "${test_db_port}" "${test_db_user}" "${test_db_password}"; then
			echo "PostgreSQL is already reachable on 127.0.0.1:${test_db_port} with TEST_DATABASE_URL credentials."
			# shellcheck source=scripts/database/internal/postgresql.sh
			source "${DATABASE_SCRIPTS_DIR}/postgresql.sh"
			if _postgres_container_running; then
				_tests_ensure_test_database todos_test
			fi
			return 0
		fi

		echo "Preparing PostgreSQL for CI-parity tests (credentials from TEST_DATABASE_URL)..."
		# shellcheck source=scripts/database/internal/postgresql.sh
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
		# shellcheck source=scripts/database/internal/postgresql.sh
		source "${DATABASE_SCRIPTS_DIR}/postgresql.sh"
		if _postgres_container_running; then
			_tests_ensure_test_database todos_test
		fi
		return 0
	fi

	# shellcheck source=scripts/database/internal/postgresql.sh
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
