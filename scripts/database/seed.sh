#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=scripts/database/internal/setup.sh
source "$SCRIPT_DIR/internal/setup.sh"

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

# shellcheck source=scripts/database/internal/container_ops.sh
source "$SCRIPT_DIR/internal/container_ops.sh"
container_ops_init
container_ops_ensure_infra
if [[ -z "${JWT_SECRET_KEY:-}" ]]; then
	echo "JWT_SECRET_KEY must be set (load via ENV_PROFILE and env_apply_profile)." >&2
	exit 1
fi
container_ops_assert_seed_allowed
echo "Seeding database..."
container_ops_run_app python -m todos_app.infrastructure.persistence.seeding
echo "Seed complete. Demo users: jane / admin (password: changeme)."
