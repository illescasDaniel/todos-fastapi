#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
output_dir="${1:-${repo_root}/schemas/json}"

if [[ ! -d "${repo_root}/.venv" ]]; then
	echo "Missing .venv. Create it first: python3 -m venv .venv" >&2
	exit 1
fi

PYTHONPATH="${repo_root}/src" "${repo_root}/.venv/bin/python" -m todos_app.api.schema_export.export "${output_dir}"
