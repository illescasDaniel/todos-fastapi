#!/usr/bin/env bash

set -euo pipefail

run_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scripts_dir="$(cd "${run_script_dir}/.." && pwd)"
# shellcheck source=scripts/lib.sh
source "${scripts_dir}/lib.sh"

lib_require_venv
lib_activate_venv
lib_ensure_mcp_installed

pytest mcp/todos-backend/tests/ "$@"
