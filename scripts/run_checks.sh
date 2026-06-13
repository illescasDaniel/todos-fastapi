#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
checks_dir="${script_dir}/checks"

FULL=false
forwarded_args=()
for arg in "$@"; do
	case "${arg}" in
	--full)
		FULL=true
		;;
	*)
		forwarded_args+=("${arg}")
		;;
	esac
done

cd "${repo_root}"

"${checks_dir}/ruff.sh"
"${checks_dir}/pyright.sh"
"${checks_dir}/mcp_tests.sh" "${forwarded_args[@]}"
"${checks_dir}/ci.sh" --skip-ruff

if [[ "${FULL}" == true ]]; then
	echo "=== full: stack verification ==="
	# Coverage already ran in ci.sh; verify_stack only exercises deployment paths.
	"${script_dir}/verify_stack.sh" --skip-coverage
fi
