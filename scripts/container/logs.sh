#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=scripts/container/internal/common.sh
source "$SCRIPT_DIR/internal/common.sh"

cd "$PROJECT_ROOT"

prod_mode=false

usage() {
	cat <<EOF
Usage: $0 [--prod]

Follow logs from the app service.

Default: local full-stack Compose (Path B).
--prod: production app-only deploy (Path C).
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
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
else
	container_load_compose_context local
fi

container_compose "${COMPOSE_FILE_ARGS[@]}" logs -f app
