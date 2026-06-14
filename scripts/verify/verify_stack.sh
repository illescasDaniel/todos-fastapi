#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=scripts/verify/internal/common.sh
source "$SCRIPT_DIR/internal/common.sh"
# shellcheck source=scripts/verify/internal/http.sh
source "$SCRIPT_DIR/internal/http.sh"
# shellcheck source=scripts/verify/internal/bare_metal.sh
source "$SCRIPT_DIR/internal/bare_metal.sh"
# shellcheck source=scripts/verify/internal/compose.sh
source "$SCRIPT_DIR/internal/compose.sh"

ONLY=""
SKIP_HTTP=false
SKIP_COVERAGE=false
KEEP=false
FAILED=0

usage() {
	cat <<EOF
Usage: $0 [options]

Verify every local deployment path: migrate, seed, and HTTP smoke checks per
environment, then one CI-parity pytest + coverage run on PostgreSQL.

Bare-metal: venv API + infra-only docker-compose.infra.yml (Valkey + PostgreSQL).
Compose: Path B full stack via docker-compose.infra.yml + docker-compose.app.base.yml + docker-compose.app.with-infra.yml.

Options:
  --only FILTER       Run subset: postgres, compose-postgres, bare-metal,
                      compose, all (default: all)
  --skip-http         Skip HTTP smoke checks
  --skip-coverage     Skip final ./scripts/quality/tests.sh --coverage
  --keep              Leave the last Compose stack running (debug)
  -h, --help          Show this help

Requires: .venv with pip install -e ".[dev]", curl, podman, PostgreSQL on 127.0.0.1 (POSTGRES_PORT, default 5432) for pytest.
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
	--only)
		ONLY="$2"
		shift 2
		;;
	--skip-http)
		SKIP_HTTP=true
		shift
		;;
	--skip-coverage)
		SKIP_COVERAGE=true
		shift
		;;
	--keep)
		KEEP=true
		shift
		;;
	-h | --help)
		usage
		exit 0
		;;
	*)
		echo "Unknown option: $1" >&2
		usage >&2
		exit 1
		;;
	esac
done

[[ -z "$ONLY" ]] && ONLY="all"

verify_should_run() {
	local filter="$1"
	case "$ONLY" in
	all) return 0 ;;
	postgres)
		[[ "$filter" == "postgres" ]] && return 0
		;;
	"$filter") return 0 ;;
	bare-metal)
		[[ "$filter" == "postgres" ]] && return 0
		;;
	compose)
		[[ "$filter" == "compose-postgres" ]] && return 0
		;;
	esac
	return 1
}

verify_postgres_url() {
	verify_load_ports
	echo "postgresql+asyncpg://${POSTGRES_USER:?set POSTGRES_USER in .env}:${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}@127.0.0.1:${POSTGRES_PORT:?set POSTGRES_PORT in config/ports.env}/${POSTGRES_DB:?set POSTGRES_DB in .env}"
}

verify_run_scenario() {
	local filter="$1"
	shift
	if ! verify_should_run "$filter"; then
		return 0
	fi
	if ! "$@"; then
		echo "verify_stack: scenario failed: ${filter}" >&2
		FAILED=$((FAILED + 1))
	fi
}

verify_run_coverage() {
	if [[ "$SKIP_COVERAGE" == true ]]; then
		return 0
	fi
	case "$ONLY" in
	all | bare-metal | compose | coverage) ;;
	*) return 0 ;;
	esac

	local start_ts end_ts elapsed
	start_ts=$(date +%s)
	echo ""
	echo "=== ci/coverage ==="

	if JWT_SECRET_KEY=test-secret-key-for-ci-suite-32bytes! "$PROJECT_ROOT/scripts/quality/tests.sh" --coverage; then
		end_ts=$(date +%s)
		elapsed=$((end_ts - start_ts))
		verify_record_result "ci/coverage" "ok" "-" "$elapsed"
		echo "=== ci/coverage: done (${elapsed}s) ==="
	else
		end_ts=$(date +%s)
		elapsed=$((end_ts - start_ts))
		verify_record_result "ci/coverage" "fail" "-" "$elapsed"
		echo "=== ci/coverage: failed (${elapsed}s) ===" >&2
		FAILED=$((FAILED + 1))
	fi
}

cd "$PROJECT_ROOT"
verify_require_prereqs
verify_apply_defaults

if [[ "$SKIP_HTTP" != true ]]; then
	verify_port_available "$VERIFY_API_PORT"
fi

echo "verify_stack: starting (filter=${ONLY})"

verify_run_scenario postgres verify_run_bare_metal \
	"bare-metal/postgres" "$(verify_postgres_url)" "$SKIP_HTTP"

verify_run_scenario compose-postgres verify_run_compose \
	"compose/postgres" "$(verify_postgres_url)" "$SKIP_HTTP" "$KEEP"

verify_run_coverage

verify_print_summary

if [[ "$FAILED" -gt 0 ]]; then
	echo ""
	echo "verify_stack: ${FAILED} scenario(s) failed" >&2
	exit 1
fi

echo ""
echo "verify_stack: all scenarios passed"
