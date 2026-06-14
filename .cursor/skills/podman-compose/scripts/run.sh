#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../../.." && pwd)"
cd "${REPO_ROOT}"
cmd="${1:-}"
case "${cmd}" in
up)
	shift
	exec ./scripts/container/up.sh "$@"
	;;
down)
	shift
	exec ./scripts/container/down.sh "$@"
	;;
wipe)
	shift
	exec ./scripts/database/wipe.sh "$@"
	;;
seed)
	shift
	exec ./scripts/database/seed.sh "$@"
	;;
logs)
	shift
	exec ./scripts/container/logs.sh "$@"
	;;
build)
	shift
	exec ./scripts/container/build.sh "$@"
	;;
*)
	echo "Usage: $0 {up|down|wipe|seed|logs|build}" >&2
	exit 1
	;;
esac
