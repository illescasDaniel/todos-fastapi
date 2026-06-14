# Shared docker-compose.infra.yml helpers for infra-only Podman services.
# Expects PROJECT_ROOT.

_infra_require_podman() {
	if ! command -v podman &>/dev/null; then
		echo "Podman is required but not installed." >&2
		echo "Run: ./scripts/install_podman.sh" >&2
		exit 1
	fi
}

infra_compose() {
	_infra_require_podman
	podman compose -f "$PROJECT_ROOT/docker-compose.infra.yml" "$@"
}
