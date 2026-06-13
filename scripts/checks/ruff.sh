#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/checks/_common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

checks_require_venv
checks_activate_venv

ruff check src tests mcp/todos-backend/src mcp/todos-backend/tests --fix
ruff format src tests mcp/todos-backend/src mcp/todos-backend/tests
