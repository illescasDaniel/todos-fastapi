#!/usr/bin/env bash

set -euo pipefail

quality_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scripts_dir="$(cd "${quality_dir}/.." && pwd)"
script_dir="${scripts_dir}"
repo_root="$(cd "${scripts_dir}/.." && pwd)"

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

_tests_bootstrap_postgres() {
	if [[ -z "${ENV_PROFILE:-}" ]]; then
		echo "ENV_PROFILE is not set. checks.sh sets ENV_PROFILE=test for pytest." >&2
		exit 1
	fi

	# shellcheck source=scripts/database/internal/setup.sh
	source "${script_dir}/database/internal/setup.sh"
	database_load_env

	local test_db_port="${POSTGRES_PORT:?set POSTGRES_PORT via ENV_PROFILE test profile}"
	local test_db_user="${POSTGRES_USER:?set POSTGRES_USER via ENV_PROFILE test profile}"
	local test_db_password="${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD via ENV_PROFILE test profile}"

	if _tests_postgres_auth_ok 127.0.0.1 "${test_db_port}" "${test_db_user}" "${test_db_password}"; then
		echo "PostgreSQL is already reachable on 127.0.0.1:${test_db_port} with test profile credentials."
		# shellcheck source=scripts/database/internal/postgresql.sh
		source "${DATABASE_SCRIPTS_DIR}/postgresql.sh"
		if _postgres_container_running; then
			_tests_ensure_test_database todos_test
		fi
		return 0
	fi

	echo "Preparing PostgreSQL for tests (ENV_PROFILE=test credentials)..."
	# shellcheck source=scripts/database/internal/postgresql.sh
	source "${DATABASE_SCRIPTS_DIR}/postgresql.sh"
	postgres_reset_container
	_tests_started_postgres=true
	trap _tests_cleanup_postgres EXIT INT TERM HUP
	_tests_ensure_test_database todos_test
}

_tests_bootstrap_postgres

cd "${repo_root}" || exit
# shellcheck disable=SC1091
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
