# Shared Podman Compose helpers for scripts/container/*.sh
# Callers must set SCRIPT_DIR, then: source common.sh && cd "$PROJECT_ROOT"

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"

COMPOSE_FILE_ARGS=()
COMPOSE_STACK_MODE=""
DATABASE_URL=""
COMPOSE_DATABASE_URL=""
VALKEY_URL=""
COMPOSE_VALKEY_URL=""

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

JWT_EXAMPLE_PLACEHOLDER="change-me-generate-a-secure-random-value"
MIGRATE_PLACEHOLDER_SECRET="container-migrate-placeholder-secret"
JWT_MIN_LENGTH=32

jwt_secret_key_is_weak() {
	local key="${1:-}"
	if [[ -z "$key" ]]; then
		return 0
	fi
	if [[ "$key" == "$JWT_EXAMPLE_PLACEHOLDER" ]] || [[ "$key" == "$MIGRATE_PLACEHOLDER_SECRET" ]]; then
		return 0
	fi
	if [[ ${#key} -lt $JWT_MIN_LENGTH ]]; then
		return 0
	fi
	return 1
}

require_env_file() {
	local template="${1:?require_env_file: template filename required}"
	if [[ -f "$PROJECT_ROOT/.env" ]]; then
		return 0
	fi
	echo "Missing .env in $PROJECT_ROOT." >&2
	echo "Create it from the template, then set your secrets:" >&2
	echo "  cp ${template} .env" >&2
	exit 1
}

load_compose_env() {
	local saved_database_url="${DATABASE_URL:-}"
	local saved_valkey_url="${VALKEY_URL:-}"
	# shellcheck source=scripts/ports.sh
	source "$PROJECT_ROOT/scripts/ports.sh"
	if [[ -f "$PROJECT_ROOT/.env" ]]; then
		set -a
		# shellcheck source=/dev/null
		source "$PROJECT_ROOT/.env"
		set +a
	fi
	if [[ -n "$saved_database_url" ]]; then
		export DATABASE_URL="$saved_database_url"
	fi
	if [[ -n "$saved_valkey_url" ]]; then
		export VALKEY_URL="$saved_valkey_url"
	fi
}

load_database_url() {
	if [[ -n "${DATABASE_URL:-}" ]]; then
		return 0
	fi
	local line
	line="$(
		cd "$PROJECT_ROOT"
		grep -E '^[[:space:]]*DATABASE_URL=' .env | grep -v '^[[:space:]]*#' | tail -n 1 || true
	)"
	if [[ -z "$line" ]]; then
		DATABASE_URL="postgresql+asyncpg://todos:changeme@127.0.0.1:${POSTGRES_PORT:-5432}/todos"
		return 0
	fi
	DATABASE_URL="${line#DATABASE_URL=}"
	DATABASE_URL="${DATABASE_URL#"${DATABASE_URL%%[![:space:]]*}"}"
	DATABASE_URL="${DATABASE_URL%"${DATABASE_URL##*[![:space:]]}"}"
	DATABASE_URL="${DATABASE_URL#\"}"
	DATABASE_URL="${DATABASE_URL%\"}"
	DATABASE_URL="${DATABASE_URL#\'}"
	DATABASE_URL="${DATABASE_URL%\'}"
}

load_valkey_url() {
	if [[ -n "${VALKEY_URL:-}" ]]; then
		return 0
	fi
	local line
	line="$(
		cd "$PROJECT_ROOT"
		grep -E '^[[:space:]]*VALKEY_URL=' .env | grep -v '^[[:space:]]*#' | tail -n 1 || true
	)"
	if [[ -z "$line" ]]; then
		VALKEY_URL="valkey://127.0.0.1:${VALKEY_PORT:-6379}/0"
		return 0
	fi
	VALKEY_URL="${line#VALKEY_URL=}"
	VALKEY_URL="${VALKEY_URL#"${VALKEY_URL%%[![:space:]]*}"}"
	VALKEY_URL="${VALKEY_URL%"${VALKEY_URL##*[![:space:]]}"}"
	VALKEY_URL="${VALKEY_URL#\"}"
	VALKEY_URL="${VALKEY_URL%\"}"
	VALKEY_URL="${VALKEY_URL#\'}"
	VALKEY_URL="${VALKEY_URL%\'}"
}

database_url_uses_local_host() {
	[[ "$1" == *@127.0.0.1:* ]]
}

valkey_url_uses_local_host() {
	[[ "$1" == valkey://127.0.0.1:* ]] || [[ "$1" == redis://127.0.0.1:* ]]
}

export_compose_database_url() {
	if database_url_uses_local_host "$DATABASE_URL"; then
		COMPOSE_DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:-todos}:${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}@postgres:5432/${POSTGRES_DB:-todos}"
	else
		COMPOSE_DATABASE_URL="$DATABASE_URL"
	fi
	export COMPOSE_DATABASE_URL
}

export_compose_valkey_url() {
	if valkey_url_uses_local_host "$VALKEY_URL"; then
		COMPOSE_VALKEY_URL="valkey://valkey:6379/0"
	else
		COMPOSE_VALKEY_URL="$VALKEY_URL"
	fi
	export COMPOSE_VALKEY_URL
}

note_compose_host_override() {
	if database_url_uses_local_host "$DATABASE_URL"; then
		echo "Note: app overlay rewrites DATABASE_URL host to postgres (127.0.0.1 is for host app / infra-only)." >&2
	fi
	if valkey_url_uses_local_host "$VALKEY_URL"; then
		echo "Note: app overlay rewrites VALKEY_URL host to valkey (127.0.0.1 is for host app / infra-only)." >&2
	fi
}

container_set_compose_mode_local() {
	COMPOSE_STACK_MODE=local
	COMPOSE_FILE_ARGS=(-f docker-compose.infra.yml -f docker-compose.app.base.yml -f docker-compose.app.with-infra.yml)
}

container_set_compose_mode_prod() {
	COMPOSE_STACK_MODE=prod
	COMPOSE_FILE_ARGS=(-f docker-compose.app.base.yml)
}

export_compose_prod_urls() {
	COMPOSE_DATABASE_URL="$DATABASE_URL"
	COMPOSE_VALKEY_URL="$VALKEY_URL"
	export COMPOSE_DATABASE_URL COMPOSE_VALKEY_URL
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
	if [[ "$mode" == "local" ]]; then
		require_env_file ".env.example"
	else
		require_env_file ".env.production.example"
	fi
	load_compose_env
	load_database_url
	load_valkey_url
	if [[ "$mode" == "local" ]]; then
		export_compose_database_url
		export_compose_valkey_url
	else
		export_compose_prod_urls
	fi
}

container_assert_prod_deploy_allowed() {
	local app_env="${APP_ENV:-local}"
	case "$app_env" in
	staging | production) ;;
	*)
		echo "Production deploy requires APP_ENV=staging or APP_ENV=production (got: ${app_env})." >&2
		exit 1
		;;
	esac
	if database_url_uses_local_host "$DATABASE_URL"; then
		echo "Production deploy requires an external DATABASE_URL (127.0.0.1 is for local development)." >&2
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
	if container_app_exists; then
		container_compose "${COMPOSE_FILE_ARGS[@]}" start
	else
		container_compose "${COMPOSE_FILE_ARGS[@]}" up -d --build
	fi
}

container_ensure_stack_running() {
	if container_app_exists; then
		container_compose "${COMPOSE_FILE_ARGS[@]}" start
	else
		container_compose "${COMPOSE_FILE_ARGS[@]}" up -d --build
	fi
}

container_wait_for_health() {
	local attempts="${1:-45}"
	local i
	for ((i = 1; i <= attempts; i++)); do
		if curl -sf "http://localhost:${API_PORT:-8000}/health" >/dev/null 2>&1; then
			return 0
		fi
		sleep 2
	done
	return 1
}

container_print_stack_ready() {
	echo ""
	echo "Stack is up."
	echo "  API docs: http://localhost:${API_PORT:-8000}/docs"
	echo "  Health:   http://localhost:${API_PORT:-8000}/health"
	echo "  Logs:     ./scripts/container/logs.sh"
	echo "  Stop:     ./scripts/container/down.sh"
}

container_print_deploy_ready() {
	echo ""
	echo "App is up (production compose)."
	echo "  Health: http://localhost:${API_PORT:-8000}/health"
	echo "  Logs:   ./scripts/container/logs.sh --prod"
	echo "  Stop:   ./scripts/container/down.sh --prod"
}
