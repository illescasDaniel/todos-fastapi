#!/usr/bin/env bash

set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-/app/src}"

JWT_EXAMPLE_PLACEHOLDER="change-me-generate-a-secure-random-value"
MIGRATE_PLACEHOLDER_SECRET="container-migrate-placeholder-secret"
JWT_MIN_LENGTH=32

reject_weak_jwt_secret_key() {
	local key="${1:-}"
	if [[ -z "$key" ]]; then
		echo "JWT_SECRET_KEY is required. Set it in .env or pass -e JWT_SECRET_KEY=..." >&2
		exit 1
	fi
	if [[ "$key" == "$JWT_EXAMPLE_PLACEHOLDER" ]] || [[ "$key" == "$MIGRATE_PLACEHOLDER_SECRET" ]]; then
		echo "JWT_SECRET_KEY must not use a placeholder value. Generate a secure secret (see .env.example)." >&2
		exit 1
	fi
	if [[ ${#key} -lt $JWT_MIN_LENGTH ]]; then
		echo "JWT_SECRET_KEY must be at least $JWT_MIN_LENGTH characters." >&2
		exit 1
	fi
}

if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
	export JWT_SECRET_KEY="${JWT_SECRET_KEY:-$MIGRATE_PLACEHOLDER_SECRET}"
	alembic upgrade head
fi

reject_weak_jwt_secret_key "${JWT_SECRET_KEY:-}"

exec "$@"
