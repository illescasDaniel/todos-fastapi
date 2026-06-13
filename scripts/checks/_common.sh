#!/usr/bin/env bash

set -euo pipefail

CHECKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$(cd "${CHECKS_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SCRIPTS_DIR}/.." && pwd)"

checks_require_venv() {
	if [[ ! -d "${REPO_ROOT}/.venv" ]]; then
		echo "Missing .venv. Create it first: python3 -m venv .venv" >&2
		exit 1
	fi
}

checks_activate_venv() {
	cd "${REPO_ROOT}"
	# shellcheck disable=SC1091
	source ".venv/bin/activate"
}

checks_ensure_mcp_installed() {
	if ! python -c "import todos_mcp" 2>/dev/null; then
		echo "Installing MCP package (editable): pip install -e mcp/todos-backend/"
		pip install -q -e "mcp/todos-backend/"
	fi
}
