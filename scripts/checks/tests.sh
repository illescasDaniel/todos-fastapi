#!/usr/bin/env bash

set -euo pipefail

# shellcheck source=scripts/checks/_common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

"${SCRIPTS_DIR}/run_tests.sh" --coverage "$@"
