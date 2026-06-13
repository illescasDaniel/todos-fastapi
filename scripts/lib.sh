#!/usr/bin/env bash

# Shared helpers for scripts/run/*.sh.

LIB_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_REPO_ROOT="$(cd "${LIB_SCRIPT_DIR}/.." && pwd)"

lib_require_venv() {
	if [[ ! -d "${LIB_REPO_ROOT}/.venv" ]]; then
		echo "Missing .venv. Create it first: python3 -m venv .venv" >&2
		exit 1
	fi
}

lib_activate_venv() {
	cd "${LIB_REPO_ROOT}"
	# shellcheck disable=SC1091
	source ".venv/bin/activate"
}

lib_ensure_mcp_installed() {
	if ! python -c "import todos_mcp" 2>/dev/null; then
		echo "Installing MCP package (editable): pip install -e mcp/todos-backend/"
		pip install -q -e "mcp/todos-backend/"
	fi
}

lib_ruff_targets() {
	LIB_RUFF_TARGETS=(src tests mcp/todos-backend/src mcp/todos-backend/tests)
}
