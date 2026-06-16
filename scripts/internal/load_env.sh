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
		echo "Export a profile name matching src/env_config/profiles/<name>.py, for example:" >&2
		echo "  export ENV_PROFILE=local       # copy from profiles/example.py" >&2
		echo "  export ENV_PROFILE=local2      # extra local stack (custom ports)" >&2
		echo "  export ENV_PROFILE=test        # pytest / CI" >&2
		echo "  export ENV_PROFILE=production  # copy from profiles/production.example.py" >&2
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
	# shellcheck disable=SC1090
	eval "$(
		PYTHONPATH="${PROJECT_ROOT}/src" \
			"${PROJECT_ROOT}/.venv/bin/python" -m env_config.export --shell
	)"
}

env_write_dotenv() {
	if [[ -z "${PROJECT_ROOT:-}" ]]; then
		echo "env_write_dotenv: PROJECT_ROOT is not set" >&2
		exit 1
	fi
	env_require_venv
	PYTHONPATH="${PROJECT_ROOT}/src" \
		"${PROJECT_ROOT}/.venv/bin/python" -m env_config.export --dotenv >"${PROJECT_ROOT}/.env"
}

# Patch generated .env with in-network URLs for Path B app + compose interpolation.
# Host scripts (Path A) reload from the Python profile via env_load_stack — not from .env.
compose_sync_dotenv_urls() {
	local dotenv="${PROJECT_ROOT}/.env"
	if [[ ! -f "$dotenv" ]]; then
		echo "compose_sync_dotenv_urls: missing ${dotenv} — run env_write_dotenv first" >&2
		exit 1
	fi
	if [[ -z "${COMPOSE_DATABASE_URL:-}" ]] || [[ -z "${COMPOSE_VALKEY_URL:-}" ]]; then
		echo "compose_sync_dotenv_urls: COMPOSE_DATABASE_URL and COMPOSE_VALKEY_URL must be set" >&2
		exit 1
	fi
	local tmp
	tmp="$(mktemp)"
	grep -v -E '^(COMPOSE_DATABASE_URL|COMPOSE_VALKEY_URL|DATABASE_URL|VALKEY_URL)=' "$dotenv" >"$tmp" || true
	{
		cat "$tmp"
		printf 'DATABASE_URL=%s\n' "$COMPOSE_DATABASE_URL"
		printf 'VALKEY_URL=%s\n' "$COMPOSE_VALKEY_URL"
		printf 'COMPOSE_DATABASE_URL=%s\n' "$COMPOSE_DATABASE_URL"
		printf 'COMPOSE_VALKEY_URL=%s\n' "$COMPOSE_VALKEY_URL"
	} >"$dotenv"
	rm -f "$tmp"
}

env_load_stack() {
	env_apply_profile
}
