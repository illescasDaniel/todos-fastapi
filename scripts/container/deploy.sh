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

Deploy the app container only (Path C — staging/production).

Uses docker-compose.app.base.yml with external POSTGRES_URL and VALKEY_URL from the env profile.
Set ENV_PROFILE to your production profile (e.g. production) before running — see docs/deployment.md.
Does not start bundled PostgreSQL or Valkey (see ./scripts/container/up.sh for local full stack).

Requires:
  APP_ENV=staging or APP_ENV=production
  External POSTGRES_URL and VALKEY_URL (not 127.0.0.1)
  Strong JWT_SECRET_KEY (min 32 characters)

Migrations run on container start when DEPLOY_RUN_MIGRATIONS=true in the env profile.
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

container_load_compose_context prod
container_assert_prod_deploy_allowed

if ! container_start_or_up; then
	exit 1
fi

echo "Waiting for API health check..."
if container_wait_for_health "$@"; then
	container_print_deploy_ready
else
	echo "Container started but /health did not respond in time." >&2
	echo "Check logs: ./scripts/container/logs.sh --prod" >&2
	exit 1
fi
