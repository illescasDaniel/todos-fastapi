#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=scripts/container/internal/common.sh
source "$SCRIPT_DIR/internal/common.sh"

cd "$PROJECT_ROOT"

usage() {
	cat <<EOF
Usage: $0

Start the full Podman Compose stack (Valkey + PostgreSQL + app).

Uses docker-compose.infra.yml + docker-compose.app.base.yml + docker-compose.app.with-infra.yml.
Uses compose start when stopped containers exist; otherwise up -d --build.
Migrations run on container start when RUN_MIGRATIONS=true in the env profile.

Requires rootless Podman (see docs/deployment.md#install-podman).
EOF
}

case "${1:-}" in
-h | --help)
	usage
	exit 0
	;;
"")
	;;
*)
	echo "Unknown argument: $1" >&2
	usage >&2
	exit 1
	;;
esac

container_load_compose_context local
note_compose_host_override

DATABASE_SCRIPTS_DIR="$PROJECT_ROOT/scripts/database/internal"
# shellcheck source=scripts/database/internal/ensure.sh
source "$PROJECT_ROOT/scripts/database/internal/ensure.sh"
database_ensure_ready

if ! container_start_or_up; then
	exit 1
fi

echo "Waiting for API health check..."
if container_wait_for_health "$@"; then
	container_print_stack_ready
else
	echo "Containers started but /health did not respond in time." >&2
	echo "Check logs: ./scripts/container/logs.sh" >&2
	exit 1
fi
