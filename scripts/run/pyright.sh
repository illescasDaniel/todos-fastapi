#!/usr/bin/env bash

set -euo pipefail

run_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scripts_dir="$(cd "${run_script_dir}/.." && pwd)"
# shellcheck source=scripts/lib.sh
source "${scripts_dir}/lib.sh"

OUTPUT_JSON=false
for arg in "$@"; do
	case "${arg}" in
	--outputjson)
		OUTPUT_JSON=true
		;;
	esac
done

lib_require_venv
lib_activate_venv
lib_ensure_mcp_installed

if [[ "${OUTPUT_JSON}" == true ]]; then
	basedpyright --outputjson
else
	basedpyright
fi
