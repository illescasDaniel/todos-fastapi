#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/checks/_common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

checks_require_venv
checks_activate_venv
checks_ensure_mcp_installed

basedpyright
