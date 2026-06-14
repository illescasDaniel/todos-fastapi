# shellcheck shell=bash
# Load port/bind defaults from config/ports.env (+ optional ports.local.env).
# Requires PROJECT_ROOT. Prefer env_load_ports from scripts/internal/load_env.sh.

# shellcheck source=scripts/internal/load_env.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/load_env.sh"

if [[ -z "${PROJECT_ROOT:-}" ]]; then
	echo "ports.sh: PROJECT_ROOT is not set" >&2
	exit 1
fi
env_load_ports
