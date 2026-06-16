#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
output_path="${1:-${repo_root}/.cursor/openapi.snapshot.json}"

if [[ ! -d "${repo_root}/.venv" ]]; then
	echo "Missing .venv. Create it first: python3 -m venv .venv" >&2
	exit 1
fi

mkdir -p "$(dirname "${output_path}")"

ENV_PROFILE=test PYTHONPATH="${repo_root}/src" "${repo_root}/.venv/bin/python" - "${output_path}" <<'PY'
import json
import os
import sys

from env_config.loader import clear_env_settings_cache

clear_env_settings_cache()

from todos_app.main import app

output_path = sys.argv[1]
schema = app.openapi()
with open(output_path, "w", encoding="utf-8") as f:
	json.dump(schema, f, indent=2, ensure_ascii=False)
	f.write("\n")
PY

echo "Wrote ${output_path}"
