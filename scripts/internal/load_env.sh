# Safe dotenv loading for scripts. Requires PROJECT_ROOT before env_load_ports / env_load_secrets.

env_safe_source() {
	local env_file="$1"
	local key value
	while IFS='=' read -r key value; do
		[[ "$key" =~ ^[[:space:]]*# ]] && continue
		[[ -z "$key" ]] && continue
		key="${key## }"
		key="${key%% }"
		if [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
			export "$key"="$value"
		fi
	done < "$env_file"
}

env_require_ports() {
	: "${API_HOST:?set API_HOST in config/ports.env}"
	: "${API_PORT:?set API_PORT in config/ports.env}"
	: "${POSTGRES_PORT:?set POSTGRES_PORT in config/ports.env}"
	: "${VALKEY_PORT:?set VALKEY_PORT in config/ports.env}"
	: "${COMPOSE_APP_BIND:?set COMPOSE_APP_BIND in config/ports.env}"
	: "${COMPOSE_INFRA_BIND:?set COMPOSE_INFRA_BIND in config/ports.env}"
	export API_HOST API_PORT POSTGRES_PORT VALKEY_PORT COMPOSE_APP_BIND COMPOSE_INFRA_BIND
}

env_load_ports() {
	if [[ -z "${PROJECT_ROOT:-}" ]]; then
		echo "env_load_ports: PROJECT_ROOT is not set" >&2
		exit 1
	fi
	if [[ ! -f "${PROJECT_ROOT}/config/ports.env" ]]; then
		echo "env_load_ports: missing ${PROJECT_ROOT}/config/ports.env" >&2
		exit 1
	fi
	env_safe_source "${PROJECT_ROOT}/config/ports.env"
	if [[ -f "${PROJECT_ROOT}/config/ports.local.env" ]]; then
		env_safe_source "${PROJECT_ROOT}/config/ports.local.env"
	fi
	env_require_ports
}

env_load_secrets() {
	if [[ -z "${PROJECT_ROOT:-}" ]]; then
		echo "env_load_secrets: PROJECT_ROOT is not set" >&2
		exit 1
	fi
	if [[ -f "${PROJECT_ROOT}/.env" ]]; then
		env_safe_source "${PROJECT_ROOT}/.env"
	fi
}

env_load_stack() {
	env_load_ports
	env_load_secrets
}
