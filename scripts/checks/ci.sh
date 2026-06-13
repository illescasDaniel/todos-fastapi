#!/usr/bin/env bash

set -euo pipefail

# Local replay of .github/workflows/ci.yml test job (audit, Ruff, pytest with CI env).

CHECKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$(cd "${CHECKS_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SCRIPTS_DIR}/.." && pwd)"

SKIP_RUFF=false
for arg in "$@"; do
	case "${arg}" in
	--skip-ruff)
		SKIP_RUFF=true
		;;
	esac
done

cd "${REPO_ROOT}"

echo "=== ci: dependency audit ==="
"${SCRIPTS_DIR}/audit_deps.sh"

if [[ "${SKIP_RUFF}" != true ]]; then
	echo "=== ci: ruff ==="
	"${CHECKS_DIR}/ruff.sh"
fi

echo "=== ci: tests with coverage (CI env) ==="
export JWT_SECRET_KEY=test-secret-key-for-ci-suite-32bytes!
export TEST_DATABASE_URL=postgresql+asyncpg://todos:todos@127.0.0.1:5432/todos_test
"${SCRIPTS_DIR}/run_tests.sh" --coverage

echo "=== ci: parity check passed ==="
