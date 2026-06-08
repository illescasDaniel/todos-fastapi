#!/usr/bin/env bash

set -euo pipefail

if [[ ! -d ".venv" ]]; then
	echo "Missing .venv. Create it first: python3 -m venv .venv"
	exit 1
fi

source ".venv/bin/activate"
ruff check src tests --fix
ruff format src tests
