#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=scripts/database/internal/setup.sh
source "$SCRIPT_DIR/internal/setup.sh"

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
	export POSTGRES_URL
	database_clear_settings_cache

	if [[ ! -d ".venv" ]]; then
		echo "Missing .venv. Create it first: python3 -m venv .venv" >&2
		exit 1
	fi
	# shellcheck disable=SC1091
	source ".venv/bin/activate"
	export PYTHONPATH="src"
	if [[ -z "${JWT_SECRET_KEY:-}" ]]; then
		echo "JWT_SECRET_KEY must be set (load via ENV_PROFILE and env_apply_profile)." >&2
		exit 1
	fi
	alembic revision --autogenerate -m "$message"
	;;
upgrade | current | history)
	# shellcheck source=scripts/database/internal/container_ops.sh
	source "$SCRIPT_DIR/internal/container_ops.sh"
	container_ops_init
	container_ops_ensure_infra
	if [[ -z "${JWT_SECRET_KEY:-}" ]]; then
		echo "JWT_SECRET_KEY must be set (load via ENV_PROFILE and env_apply_profile)." >&2
		exit 1
	fi
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

Run before ./scripts/start.sh or after ./scripts/database/wipe.sh.
EOF
	exit 0
	;;
*)
	echo "Usage: $0 [upgrade|revision -m \"msg\"|current|history]" >&2
	exit 1
	;;
esac
