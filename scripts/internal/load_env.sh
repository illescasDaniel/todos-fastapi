# shellcheck shell=bash
# Load env profile via Python export. Requires PROJECT_ROOT and .venv.

env_require_venv() {
	if [[ ! -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
		echo "Missing ${PROJECT_ROOT}/.venv — run: python3 -m venv .venv && pip install -e \".[dev]\"" >&2
		exit 1
	fi
}

env_require_profile() {
	if [[ -z "${ENV_PROFILE:-}" ]]; then
		echo "ENV_PROFILE is not set." >&2
		echo "Export a profile name matching config/profiles/<name>.toml, for example:" >&2
		echo "  export ENV_PROFILE=local       # copy from config/profiles/example.toml" >&2
		echo "  export ENV_PROFILE=local2      # extra local stack (custom ports)" >&2
		echo "  export ENV_PROFILE=test        # pytest / CI" >&2
		echo "  export ENV_PROFILE=production  # copy from config/profiles/production.example.toml" >&2
		exit 1
	fi
}

env_apply_profile() {
	if [[ -z "${PROJECT_ROOT:-}" ]]; then
		echo "env_apply_profile: PROJECT_ROOT is not set" >&2
		exit 1
	fi
	env_require_profile
	env_require_venv
	PYTHONPATH="${PROJECT_ROOT}/src" \
		"${PROJECT_ROOT}/.venv/bin/python" -m todos_app.core.config.export >"${PROJECT_ROOT}/.env"
	set -a
	# shellcheck disable=SC1091
	source "${PROJECT_ROOT}/.env"
	set +a
}
