# Valkey Podman lifecycle (always-on infra via docker-compose.infra.yml).
# Expects PROJECT_ROOT.

VALKEY_CONTAINER_NAME="${VALKEY_CONTAINER_NAME:-todos-valkey}"

_valkey_container_running() {
	podman container inspect "$VALKEY_CONTAINER_NAME" --format '{{.State.Status}}' 2>/dev/null | grep -qx running
}

_valkey_wait_for_ready() {
	local retries=30
	local auth_args=()
	if [[ -n "${VALKEY_PASSWORD:-}" ]]; then
		auth_args=(-a "$VALKEY_PASSWORD")
	fi
	echo "Waiting for Valkey to accept connections..."
	while (( retries > 0 )); do
		if (
			cd "$PROJECT_ROOT"
			infra_compose exec -T valkey valkey-cli "${auth_args[@]}" ping
		) &>/dev/null; then
			return 0
		fi
		sleep 1
		(( retries-- )) || true
	done
	echo "Valkey container did not become ready in time." >&2
	return 1
}

valkey_prepare_for_start() {
	# shellcheck source=scripts/database/infra_compose.sh
	source "$DATABASE_SCRIPTS_DIR/infra_compose.sh"

	if _valkey_container_running; then
		echo "Valkey container already running."
		return 0
	fi

	echo "Starting Valkey container..."
	(
		cd "$PROJECT_ROOT"
		infra_compose up -d valkey
	)
	_valkey_wait_for_ready
}
