# shellcheck shell=bash
# Load env profile exports. Requires PROJECT_ROOT.

# shellcheck source=scripts/internal/load_env.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/load_env.sh"

if [[ -z "${PROJECT_ROOT:-}" ]]; then
	echo "ports.sh: PROJECT_ROOT is not set" >&2
	exit 1
fi
env_apply_profile
