#!/usr/bin/env bash

set -euo pipefail

internal_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/quality/internal/lib.sh
source "${internal_dir}/lib.sh"

lib_require_venv
lib_activate_venv
lib_ensure_mcp_installed

if [[ "${CI:-}" != "true" ]]; then
	"${LIB_REPO_ROOT}/scripts/mcp/export_openapi.sh"
fi

pytest mcp/todos-backend/tests/ "$@"
