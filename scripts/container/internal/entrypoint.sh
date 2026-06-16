#!/usr/bin/env bash

set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-/app/src}"

# WARNING: Running migrations on container start is only safe for single-replica deployments.
# For multi-replica or zero-downtime deploys, run migrations as a one-shot pre-deploy step
# in CI/CD instead (set DEPLOY_RUN_MIGRATIONS=false and run: alembic upgrade head before rolling out).
if [[ "${DEPLOY_RUN_MIGRATIONS:?set DEPLOY_RUN_MIGRATIONS in env profile}" == "true" ]]; then
	if [[ -z "${JWT_SECRET_KEY:-}" ]]; then
		echo "JWT_SECRET_KEY must be set before running migrations." >&2
		exit 1
	fi
	alembic upgrade head
fi

# L6: Validate all settings (including JWT_SECRET_KEY strength) via the Python Settings model.
# This reuses the full application validation logic rather than a partial shell reimplementation.
python -c "
import os, sys
sys.path.insert(0, os.environ.get('PYTHONPATH', 'src'))
from todos_app.core.settings import get_settings
get_settings()
print('Settings validation passed', flush=True)
" || exit 1

exec "$@"
