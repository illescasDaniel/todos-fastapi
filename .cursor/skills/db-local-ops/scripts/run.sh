#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/../../../.." && pwd)"
cd "${REPO_ROOT}"
cmd="${1:-}"
case "${cmd}" in
wipe)
	shift
	exec ./scripts/wipe.sh "$@"
	;;
seed)
	shift
	exec ./scripts/seed.sh "$@"
	;;
*)
	echo "Usage: $0 {wipe|seed}" >&2
	exit 1
	;;
esac
