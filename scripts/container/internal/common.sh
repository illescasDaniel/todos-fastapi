# shellcheck shell=bash
# Shared Podman Compose helpers for scripts/container/*.sh (source from scripts/container/internal/).
# Callers must set SCRIPT_DIR, then: source common.sh && cd "$PROJECT_ROOT"

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"

COMPOSE_FILE_ARGS=()

require_podman() {
	if ! command -v podman &>/dev/null; then
		echo "podman is not installed." >&2
		echo "Run: ./scripts/install_podman.sh" >&2
		exit 1
	fi
}

container_compose() {
	require_podman
	podman compose "$@"
}

JWT_MIN_LENGTH=32

jwt_secret_key_is_weak() {
	local key="${1:-}"
	if [[ -z "$key" ]] || [[ ${#key} -lt $JWT_MIN_LENGTH ]]; then
		return 0
	fi
	return 1
}

load_compose_env() {
	# shellcheck source=scripts/internal/load_env.sh
	source "$PROJECT_ROOT/scripts/internal/load_env.sh"
	env_apply_profile
}

postgres_url_uses_local_host() {
	[[ "$1" == *@127.0.0.1:* ]]
}

valkey_url_uses_local_host() {
	[[ "$1" == valkey://127.0.0.1:* ]] || [[ "$1" == redis://127.0.0.1:* ]] \
		|| [[ "$1" == valkey://*@127.0.0.1:* ]] || [[ "$1" == redis://*@127.0.0.1:* ]]
}

container_set_compose_mode_local() {
	COMPOSE_FILE_ARGS=(-f docker-compose.infra.yml -f docker-compose.app.base.yml -f docker-compose.app.with-infra.yml)
}

container_set_compose_mode_prod() {
	COMPOSE_FILE_ARGS=(-f docker-compose.app.base.yml)
}

container_load_compose_context() {
	local mode="${1:-local}"
	case "$mode" in
	local)
		container_set_compose_mode_local
		;;
	prod)
		container_set_compose_mode_prod
		;;
	*)
		echo "Unknown compose mode: $mode (expected local or prod)." >&2
		exit 1
		;;
	esac
	load_compose_env
	if [[ "$mode" == "local" ]]; then
		if [[ -z "${POSTGRES_COMPOSE_URL:-}" ]] || [[ -z "${VALKEY_COMPOSE_URL:-}" ]]; then
			echo "Path B requires postgres.compose_url and valkey.compose_url in config/profiles/${ENV_PROFILE:?set ENV_PROFILE}.toml" >&2
			exit 1
		fi
	fi
}

container_assert_prod_deploy_allowed() {
	local app_env="${APP_ENV:?set APP_ENV in env profile}"
	case "$app_env" in
	staging | production) ;;
	*)
		echo "Production deploy requires APP_ENV=staging or APP_ENV=production (got: ${app_env})." >&2
		exit 1
		;;
	esac
	if postgres_url_uses_local_host "$POSTGRES_URL"; then
		echo "Production deploy requires an external POSTGRES_URL (127.0.0.1 is for local development)." >&2
		exit 1
	fi
	if valkey_url_uses_local_host "$VALKEY_URL"; then
		echo "Production deploy requires an external VALKEY_URL (127.0.0.1 is for local development)." >&2
		exit 1
	fi
	if jwt_secret_key_is_weak "${JWT_SECRET_KEY:-}"; then
		echo "Production deploy requires a strong JWT_SECRET_KEY (min $JWT_MIN_LENGTH chars, not a placeholder)." >&2
		exit 1
	fi
}

APP_CONTAINER_NAME="${APP_CONTAINER_NAME:-todos-app}"

# podman-compose does not accept "ps -q <service>" (unlike docker compose v2).
container_app_exists() {
	podman container exists "$APP_CONTAINER_NAME" 2>/dev/null
}

container_app_running() {
	podman container inspect "$APP_CONTAINER_NAME" --format '{{.State.Status}}' 2>/dev/null | grep -qx running
}

container_compose_stop_current() {
	container_compose "${COMPOSE_FILE_ARGS[@]}" stop "$@"
}

container_compose_down_remove_current() {
	container_compose "${COMPOSE_FILE_ARGS[@]}" down --remove-orphans "$@"
}

container_compose_wipe_all_profiles() {
	container_set_compose_mode_local
	container_compose "${COMPOSE_FILE_ARGS[@]}" down --remove-orphans -v || true
	container_compose -f docker-compose.infra.yml down --remove-orphans -v || true
}

container_start_or_up() {
	# Always up (not start) so env_file / environment changes apply; --build picks up image changes.
	container_compose "${COMPOSE_FILE_ARGS[@]}" up -d --build --remove-orphans
}

container_wait_for_health() {
	local attempts="${1:-45}"
	local i
	for ((i = 1; i <= attempts; i++)); do
		if curl -sf "http://localhost:${API_PORT:?set API_PORT in env profile}/health" >/dev/null 2>&1; then
			return 0
		fi
		sleep 2
	done
	return 1
}

container_print_stack_ready() {
	echo ""
	echo "Stack is up."
	echo "  API docs: http://localhost:${API_PORT:?set API_PORT in env profile}/docs"
	echo "  Health:   http://localhost:${API_PORT:?set API_PORT in env profile}/health"
	echo "  Logs:     ./scripts/container/logs.sh"
	echo "  Stop:     ./scripts/container/down.sh"
}

container_print_deploy_ready() {
	echo ""
	echo "App is up (production compose)."
	echo "  Health: http://localhost:${API_PORT:?set API_PORT in env profile}/health"
	echo "  Logs:   ./scripts/container/logs.sh --prod"
	echo "  Stop:   ./scripts/container/down.sh --prod"
}
