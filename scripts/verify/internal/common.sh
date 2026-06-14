# Shared helpers for scripts/verify/verify_stack.sh.

VERIFY_API_HOST="${VERIFY_API_HOST:-127.0.0.1}"
VERIFY_JWT_SECRET="${VERIFY_JWT_SECRET:-test-secret-key-for-verify-stack-32bytes!}"
# M6: No changeme default — VERIFY_POSTGRES_PASSWORD must be set explicitly or match .env
VERIFY_POSTGRES_PASSWORD="${VERIFY_POSTGRES_PASSWORD:-}"

VERIFY_SUMMARY_NAMES=()
VERIFY_SUMMARY_PYTEST=()
VERIFY_SUMMARY_HTTP=()
VERIFY_SUMMARY_SECONDS=()

verify_require_cmd() {
	local cmd="$1"
	if ! command -v "$cmd" &>/dev/null; then
		echo "verify_stack: required command not found: $cmd" >&2
		exit 1
	fi
}

verify_require_prereqs() {
	verify_require_cmd curl
	verify_require_cmd podman
	if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
		echo "verify_stack: missing .venv — run: python3 -m venv .venv && pip install -e \".[dev]\"" >&2
		exit 1
	fi
}

verify_load_ports() {
	# shellcheck source=scripts/internal/load_env.sh
	source "${PROJECT_ROOT}/scripts/internal/load_env.sh"
	# shellcheck source=scripts/internal/env_urls.sh
	source "${PROJECT_ROOT}/scripts/internal/env_urls.sh"
	env_load_stack
	env_resolve_valkey_url
	VERIFY_API_PORT="${VERIFY_API_PORT:-$API_PORT}"
	export VERIFY_API_PORT
}

verify_apply_defaults() {
	verify_load_ports
	export APP_ENV=local
	export JWT_SECRET_KEY="${JWT_SECRET_KEY:-$VERIFY_JWT_SECRET}"
	if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
		echo "ERROR: POSTGRES_PASSWORD not set. Set it in .env or export POSTGRES_PASSWORD." >&2
		exit 1
	fi
	export POSTGRES_PASSWORD
}

verify_port_available() {
	local port="$1"
	if curl -sf --max-time 1 "http://${VERIFY_API_HOST}:${port}/health" &>/dev/null; then
		echo "verify_stack: port ${port} already serves /health — stop the other stack first" >&2
		return 1
	fi
	if command -v ss &>/dev/null; then
		if ss -ltn "( sport = :${port} )" 2>/dev/null | grep -q LISTEN; then
			echo "verify_stack: port ${port} is already in use" >&2
			return 1
		fi
	fi
	return 0
}

verify_record_result() {
	local name="$1"
	local pytest_status="$2"
	local http_status="$3"
	local seconds="$4"
	VERIFY_SUMMARY_NAMES+=("$name")
	VERIFY_SUMMARY_PYTEST+=("$pytest_status")
	VERIFY_SUMMARY_HTTP+=("$http_status")
	VERIFY_SUMMARY_SECONDS+=("$seconds")
}

verify_print_summary() {
	local i
	echo ""
	printf "%-24s %-8s %-8s %s\n" "SCENARIO" "PYTEST" "HTTP" "TIME"
	printf "%-24s %-8s %-8s %s\n" "------------------------" "--------" "--------" "----"
	for i in "${!VERIFY_SUMMARY_NAMES[@]}"; do
		printf "%-24s %-8s %-8s %ss\n" \
			"${VERIFY_SUMMARY_NAMES[$i]}" \
			"${VERIFY_SUMMARY_PYTEST[$i]}" \
			"${VERIFY_SUMMARY_HTTP[$i]}" \
			"${VERIFY_SUMMARY_SECONDS[$i]}"
	done
}

verify_load_database_helpers() {
	DATABASE_SCRIPTS_DIR="$PROJECT_ROOT/scripts/database/internal"
	# shellcheck source=scripts/database/internal/common.sh
	source "$PROJECT_ROOT/scripts/database/internal/common.sh"
	# shellcheck source=scripts/database/internal/ensure.sh
	source "$PROJECT_ROOT/scripts/database/internal/ensure.sh"
}

verify_run_seeding() {
	# shellcheck disable=SC1091
	source "$PROJECT_ROOT/.venv/bin/activate"
	PYTHONPATH=src python -c "
from todos_app.infrastructure.persistence.seeding.runner import assert_seed_allowed
from todos_app.core.settings import get_settings
get_settings.cache_clear()
assert_seed_allowed()
"
	PYTHONPATH=src python -m todos_app.infrastructure.persistence.seeding
}

verify_run_alembic_upgrade() {
	# shellcheck disable=SC1091
	source "$PROJECT_ROOT/.venv/bin/activate"
	export PYTHONPATH=src
	alembic upgrade head
}
