# shellcheck shell=bash
# Valkey Podman lifecycle via docker-compose.infra.yml (infra-only).
# Expects PROJECT_ROOT.

VALKEY_CONTAINER_NAME="${VALKEY_CONTAINER_NAME:-todos-valkey}"

_valkey_container_running() {
	podman container inspect "$VALKEY_CONTAINER_NAME" --format '{{.State.Status}}' 2>/dev/null | grep -qx running
}

_valkey_auth_ok() {
	# shellcheck source=scripts/database/internal/infra_compose.sh
	source "$DATABASE_SCRIPTS_DIR/infra_compose.sh"
	local auth_args=()
	if [[ -n "${VALKEY_PASSWORD:-}" ]]; then
		auth_args=(-a "$VALKEY_PASSWORD")
	fi
	(
		cd "$PROJECT_ROOT" || exit
		infra_compose exec -T valkey valkey-cli "${auth_args[@]}" ping
	) 2>/dev/null | grep -qx PONG
}

_valkey_wait_for_ready() {
	local retries=30
	local auth_args=()
	if [[ -n "${VALKEY_PASSWORD:-}" ]]; then
		auth_args=(-a "$VALKEY_PASSWORD")
	fi
	echo "Waiting for Valkey to accept connections..."
	while ((retries > 0)); do
		if (
			cd "$PROJECT_ROOT" || exit
			infra_compose exec -T valkey valkey-cli "${auth_args[@]}" ping
		) &>/dev/null; then
			return 0
		fi
		sleep 1
		((retries--)) || true
	done
	echo "Valkey container did not become ready in time." >&2
	return 1
}

valkey_reset_container() {
	# shellcheck source=scripts/database/internal/infra_compose.sh
	source "$DATABASE_SCRIPTS_DIR/infra_compose.sh"

	echo "Resetting Valkey container (recreate volume with current VALKEY_PASSWORD)..."
	(
		cd "$PROJECT_ROOT" || exit
		infra_compose stop valkey 2>/dev/null || true
		podman stop todos-app 2>/dev/null || true
		podman rm -f todos-app "${VALKEY_CONTAINER_NAME}" 2>/dev/null || true
		podman volume rm -f todos_todos-valkey-data 2>/dev/null || true
		infra_compose up -d valkey
	)
	_valkey_wait_for_ready
}

valkey_prepare_for_start() {
	# shellcheck source=scripts/database/internal/infra_compose.sh
	source "$DATABASE_SCRIPTS_DIR/infra_compose.sh"

	if _valkey_container_running; then
		if _valkey_auth_ok; then
			echo "Valkey container already running."
			return 0
		fi
		echo "Valkey credentials do not match env profile; recreating container..."
		valkey_reset_container
		return 0
	fi

	echo "Starting Valkey container..."
	(
		cd "$PROJECT_ROOT" || exit
		infra_compose up -d valkey
	)
	_valkey_wait_for_ready
	if ! _valkey_auth_ok; then
		echo "Valkey volume credentials do not match env profile; recreating container..."
		valkey_reset_container
	fi
}

valkey_stop_container() {
	# shellcheck source=scripts/database/internal/infra_compose.sh
	source "$DATABASE_SCRIPTS_DIR/infra_compose.sh"

	if ! _valkey_container_running; then
		echo "Valkey container is not running."
		return 0
	fi
	echo "Stopping Valkey container..."
	(
		cd "$PROJECT_ROOT" || exit
		infra_compose stop valkey
	) || true
}
