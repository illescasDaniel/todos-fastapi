# shellcheck shell=bash
# Derive DATABASE_URL / VALKEY_URL from ports + secrets. Source after load_env.sh.

env_read_key_from_file() {
	local env_file="$1"
	local wanted_key="$2"
	local key value
	[[ -f "$env_file" ]] || return 1
	while IFS='=' read -r key value; do
		[[ "$key" =~ ^[[:space:]]*# ]] && continue
		[[ -z "$key" ]] && continue
		key="${key## }"
		key="${key%% }"
		if [[ "$key" == "$wanted_key" ]]; then
			value="${value#"${value%%[![:space:]]*}"}"
			value="${value%"${value##*[![:space:]]}"}"
			value="${value#\"}"
			value="${value%\"}"
			value="${value#\'}"
			value="${value%\'}"
			printf '%s' "$value"
			return 0
		fi
	done <"$env_file"
	return 1
}

env_resolve_database_url() {
	if [[ -n "${DATABASE_URL:-}" ]]; then
		export DATABASE_URL
		return 0
	fi
	local explicit
	explicit="$(env_read_key_from_file "${PROJECT_ROOT}/.env" DATABASE_URL 2>/dev/null || true)"
	if [[ -n "$explicit" ]]; then
		export DATABASE_URL="$explicit"
		return 0
	fi
	if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
		echo "ERROR: POSTGRES_PASSWORD not set in .env (required to derive DATABASE_URL)." >&2
		exit 1
	fi
	export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER:?set POSTGRES_USER in .env}:${POSTGRES_PASSWORD}@127.0.0.1:${POSTGRES_PORT:?set POSTGRES_PORT in config/ports.env}/${POSTGRES_DB:?set POSTGRES_DB in .env}"
}

env_resolve_valkey_url() {
	if [[ -n "${VALKEY_URL:-}" ]]; then
		export VALKEY_URL
		return 0
	fi
	local explicit
	explicit="$(env_read_key_from_file "${PROJECT_ROOT}/.env" VALKEY_URL 2>/dev/null || true)"
	if [[ -n "$explicit" ]]; then
		export VALKEY_URL="$explicit"
		return 0
	fi
	if [[ -n "${VALKEY_PASSWORD:-}" ]]; then
		export VALKEY_URL="valkey://:${VALKEY_PASSWORD}@127.0.0.1:${VALKEY_PORT:?set VALKEY_PORT in config/ports.env}/0"
	else
		export VALKEY_URL="valkey://127.0.0.1:${VALKEY_PORT:?set VALKEY_PORT in config/ports.env}/0"
	fi
}

env_resolve_urls() {
	env_resolve_database_url
	env_resolve_valkey_url
}
