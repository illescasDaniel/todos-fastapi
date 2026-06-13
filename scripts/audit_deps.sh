#!/usr/bin/env bash

set -euo pipefail

if [[ ! -d ".venv" ]]; then
	echo "Missing .venv. Create it first: python3 -m venv .venv"
	exit 1
fi

source ".venv/bin/activate"

if ! command -v pip-audit &>/dev/null; then
	pip install pip-audit
fi

REQ_FILE="$(mktemp)"
trap 'rm -f "$REQ_FILE"' EXIT

# fastapi-todos is installed editable for development and is not published on PyPI.
pip freeze | grep -viE 'fastapi-todos' >"$REQ_FILE"

pip-audit -r "$REQ_FILE"
