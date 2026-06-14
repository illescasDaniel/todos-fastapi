#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=scripts/database/internal/setup.sh
source "$SCRIPT_DIR/database/internal/setup.sh"

mode="${1:-dev}"

database_load_env

if [[ ! -d ".venv" ]]; then
	echo "Missing .venv. Create it first: python3 -m venv .venv"
	exit 1
fi

if database_uses_container; then
	trap database_stop_container EXIT INT TERM HUP
fi

database_ensure_ready
export DATABASE_URL VALKEY_URL
database_clear_settings_cache

source ".venv/bin/activate"

if [[ "$mode" == "pro" ]]; then
	fastapi run src/todos_app/main.py --port "$API_PORT"
else
	fastapi dev src/todos_app/main.py --port "$API_PORT"
fi
