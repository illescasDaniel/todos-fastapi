#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=scripts/database/setup.sh
source "$SCRIPT_DIR/database/setup.sh"

cmd="${1:-upgrade}"

case "$cmd" in
revision)
	shift
	message=""
	while [[ $# -gt 0 ]]; do
		case "$1" in
		-m)
			message="$2"
			shift 2
			;;
		*)
			echo "Unknown revision argument: $1" >&2
			exit 1
			;;
		esac
	done
	if [[ -z "$message" ]]; then
		echo "Usage: $0 revision -m \"describe change\"" >&2
		exit 1
	fi

	database_load_env
	database_ensure_ready
	export DATABASE_URL
	database_clear_settings_cache

	if [[ ! -d ".venv" ]]; then
		echo "Missing .venv. Create it first: python3 -m venv .venv" >&2
		exit 1
	fi
	# shellcheck disable=SC1091
	source ".venv/bin/activate"
	export PYTHONPATH="src"
	export JWT_SECRET_KEY="${JWT_SECRET_KEY:-local-dev-migrate-placeholder-secret}"
	alembic revision --autogenerate -m "$message"
	;;
upgrade | current | history)
	# shellcheck source=scripts/database/container_ops.sh
	source "$SCRIPT_DIR/database/container_ops.sh"
	container_ops_init
	note_compose_host_override
	container_ops_ensure_infra
	export JWT_SECRET_KEY="${JWT_SECRET_KEY:-$MIGRATE_PLACEHOLDER_SECRET}"
	case "$cmd" in
	upgrade)
		container_ops_run_app alembic upgrade head
		;;
	current)
		container_ops_run_app alembic current
		;;
	history)
		container_ops_run_app alembic history
		;;
	esac
	;;
-h | --help)
	cat <<EOF
Usage: $0 [upgrade|revision -m "msg"|current|history]

Apply or inspect Alembic migrations via the app container (upgrade/current/history).
Autogenerate revisions run on the host .venv (writes to alembic/versions/).

Run before ./scripts/start.sh or after ./scripts/wipe.sh.
EOF
	exit 0
	;;
*)
	echo "Usage: $0 [upgrade|revision -m \"msg\"|current|history]" >&2
	exit 1
	;;
esac
