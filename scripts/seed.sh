#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=scripts/database/setup.sh
source "$SCRIPT_DIR/database/setup.sh"

case "${1:-}" in
-h | --help)
	cat <<EOF
Usage: $0

Reset the database and load demo users/todos (jane/admin, changeme).
Runs inside the app container; starts infra when needed.

Local development only (APP_ENV=local).
EOF
	exit 0
	;;
"")
	;;
*)
	echo "Unknown argument: $1" >&2
	exit 1
	;;
esac

# shellcheck source=scripts/database/container_ops.sh
source "$SCRIPT_DIR/database/container_ops.sh"
container_ops_init
note_compose_host_override
container_ops_ensure_infra
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-$MIGRATE_PLACEHOLDER_SECRET}"
container_ops_assert_seed_allowed
echo "Seeding database..."
container_ops_run_app python -m todos_app.infrastructure.persistence.seeding
echo "Seed complete. Demo users: jane / admin (password: changeme)."
