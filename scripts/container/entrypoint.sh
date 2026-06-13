#!/usr/bin/env bash

set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-/app/src}"

MIGRATE_PLACEHOLDER_SECRET="container-migrate-placeholder-secret"

# WARNING: Running migrations on container start is only safe for single-replica deployments.
# For multi-replica or zero-downtime deploys, run migrations as a one-shot pre-deploy step
# in CI/CD instead (set RUN_MIGRATIONS=false and run: alembic upgrade head before rolling out).
if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
	export JWT_SECRET_KEY="${JWT_SECRET_KEY:-$MIGRATE_PLACEHOLDER_SECRET}"
	alembic upgrade head
fi

# L6: Validate all settings (including JWT_SECRET_KEY strength) via the Python Settings model.
# This reuses the full application validation logic rather than a partial shell reimplementation.
python -c "
import os, sys
sys.path.insert(0, os.environ.get('PYTHONPATH', 'src'))
from todos_app.core.settings import Settings
Settings()
print('Settings validation passed', flush=True)
" || exit 1

exec "$@"
