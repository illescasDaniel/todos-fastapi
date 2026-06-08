#!/usr/bin/env bash

set -euo pipefail

if [[ ! -d ".venv" ]]; then
	echo "Missing .venv. Create it first: python3 -m venv .venv"
	exit 1
fi

source ".venv/bin/activate"

pip uninstall -y fastapi-todos || true

if [[ $# -eq 0 ]]; then
	pip install -e .
else
	extras_csv=$(IFS=,; echo "$*")
	pip install -e ".[${extras_csv}]"
fi
