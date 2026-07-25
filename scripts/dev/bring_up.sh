#!/usr/bin/env bash
# Orchestrate Path A (host API) or Path B (compose app) bring-up.
# Clean: wipe volumes, rebuild app image, seed demo data, then start/up.
# Reuse: start/up only (Path A stops Path B containers first to free the API port).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

path=""
clean=false

usage() {
	cat <<EOF
Usage: $0 a|b [--clean]

Bring up local Path A (host API) or Path B (compose app).

  a         Path A: infra + host API (./scripts/start.sh)
  b         Path B: full compose stack (./scripts/container/up.sh)
  --clean   Wipe volumes, rebuild app image, seed demo data, then bring up

Reuse (default) keeps volumes. Path A reuse stops Path B containers first
(no volume wipe) so the API port is free.

Requires ENV_PROFILE (e.g. export ENV_PROFILE=local).
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
	a | b)
		path="$1"
		shift
		;;
	--clean)
		clean=true
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

if [[ -z "$path" ]]; then
	usage >&2
	exit 1
fi

if [[ -z "${ENV_PROFILE:-}" ]]; then
	echo "ENV_PROFILE is not set." >&2
	echo "Export a profile name matching config/profiles/<name>.toml, for example:" >&2
	echo "  export ENV_PROFILE=local" >&2
	exit 1
fi

wipe_sh="$PROJECT_ROOT/scripts/database/wipe.sh"
seed_sh="$PROJECT_ROOT/scripts/database/seed.sh"
start_sh="$PROJECT_ROOT/scripts/start.sh"
up_sh="$PROJECT_ROOT/scripts/container/up.sh"
down_sh="$PROJECT_ROOT/scripts/container/down.sh"

build_app_image() {
	local container_script_dir="$PROJECT_ROOT/scripts/container"
	SCRIPT_DIR="$container_script_dir"
	# shellcheck source=scripts/container/internal/common.sh
	source "$container_script_dir/internal/common.sh"
	container_load_compose_context local
	echo "Building app image..."
	container_compose "${COMPOSE_FILE_ARGS[@]}" build app
}

case "$path" in
a)
	if [[ "$clean" == true ]]; then
		echo "Path A clean: wipe → build app → seed → start"
		"$wipe_sh" --yes
		build_app_image
		"$seed_sh"
		exec "$start_sh"
	fi
	echo "Path A reuse: stop Path B (keep volumes) → start"
	"$down_sh" || true
	exec "$start_sh"
	;;
b)
	if [[ "$clean" == true ]]; then
		echo "Path B clean: wipe → up → seed"
		"$wipe_sh" --yes
		"$up_sh"
		"$seed_sh"
		exit 0
	fi
	echo "Path B reuse: up"
	exec "$up_sh"
	;;
esac
