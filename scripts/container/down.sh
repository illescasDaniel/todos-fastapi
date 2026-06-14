#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=scripts/container/internal/common.sh
source "$SCRIPT_DIR/internal/common.sh"

cd "$PROJECT_ROOT"

remove_containers=false
prod_mode=false

usage() {
	cat <<EOF
Usage: $0 [--remove] [--prod]

Stop the Compose stack.

Default (local full stack): compose stop for Path B (infra + app).
--prod: stop Path C app-only production deploy.
--remove: compose down — remove containers and network; named volumes kept.
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
	--remove)
		remove_containers=true
		shift
		;;
	--prod)
		prod_mode=true
		shift
		;;
	-h | --help)
		usage
		exit 0
		;;
	*)
		echo "Unknown argument: $1" >&2
		usage >&2
		exit 1
		;;
	esac
done

if [[ "$prod_mode" == "true" ]]; then
	container_load_compose_context prod
	echo "Stopping production app container..."
else
	container_load_compose_context local
	echo "Stopping local full-stack Compose..."
fi

if [[ "$remove_containers" == "true" ]]; then
	container_compose_down_remove_current
	echo "Stack torn down (containers removed; volumes and images kept)."
else
	container_compose_stop_current
	if [[ "$prod_mode" == "true" ]]; then
		echo "App stopped. Start again with: ./scripts/container/deploy.sh"
	else
		echo "Stack stopped. Start again with: ./scripts/container/up.sh"
	fi
fi
