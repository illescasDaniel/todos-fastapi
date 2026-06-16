#!/usr/bin/env bash
# Wrapper for scripts/quality/internal/benchmark_pytest.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/internal/benchmark_pytest.sh" "$@"
