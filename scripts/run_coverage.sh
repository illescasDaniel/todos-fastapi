#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

if [[ ! -d "${repo_root}/.venv" ]]; then
	echo "Missing .venv. Create it first: python3 -m venv .venv"
	exit 1
fi

cd "${repo_root}"
source ".venv/bin/activate"
pytest \
	--cov=todos_app \
	--cov-report=term-missing \
	--cov-report=html:htmlcov \
	"$@"
