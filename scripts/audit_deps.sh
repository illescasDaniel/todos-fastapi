#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/lib.sh
source "${script_dir}/lib.sh"

lib_require_venv
lib_activate_venv

python -m pip install --upgrade 'pip>=26.1.2'

if ! command -v pip-audit &>/dev/null; then
	pip install pip-audit
fi

# Audit installed PyPI packages in place; skip editable local packages (fastapi-todos, todos-mcp).
pip-audit -l --skip-editable
