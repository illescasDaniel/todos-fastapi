#!/usr/bin/env bash
# Remove all Compose containers and named volumes (full local reset).
# Re-apply schema with ./scripts/migrate.sh; optionally ./scripts/seed.sh for demo data.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=scripts/container/common.sh
source "$PROJECT_ROOT/scripts/container/common.sh"
SCRIPT_DIR="$PROJECT_ROOT/scripts/container"

cd "$PROJECT_ROOT"

assume_yes=false

usage() {
	cat <<EOF
Usage: $0 [--yes]

Remove all local full-stack Compose containers and named volumes (PostgreSQL, Valkey data).
Does not apply to production app-only deploy (Path C — use ./scripts/container/down.sh --prod --remove).

Use before a full reset; then run ./scripts/migrate.sh (and optionally ./scripts/seed.sh).

Requires confirmation unless --yes is passed.
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
	--yes)
		assume_yes=true
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

if [[ "$assume_yes" != "true" ]]; then
	read -r -p "Remove all Compose containers and volumes (database data)? [y/N] " reply
	if [[ ! "$reply" =~ ^[yY]$ ]]; then
		echo "Aborted."
		exit 0
	fi
fi

echo "Wiping local full-stack Compose stack and volumes..."
container_load_compose_context local
container_compose_wipe_all_profiles
echo "Wipe complete. Next: ./scripts/migrate.sh (and optionally ./scripts/seed.sh or ./scripts/container/up.sh)"
