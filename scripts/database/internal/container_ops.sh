# shellcheck shell=bash
# Run migrate/seed commands inside the app container (shared by migrate.sh and seed.sh).

container_ops_init() {
	local ops_dir
	ops_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
	PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${ops_dir}/../../.." && pwd)}"
	DATABASE_SCRIPTS_DIR="${DATABASE_SCRIPTS_DIR:-${PROJECT_ROOT}/scripts/database/internal}"
	cd "$PROJECT_ROOT" || exit

	local container_script_dir="${PROJECT_ROOT}/scripts/container"
	SCRIPT_DIR="$container_script_dir"
	# shellcheck source=scripts/container/internal/common.sh
	source "$container_script_dir/internal/common.sh"
	container_load_compose_context local
	export DATABASE_URL COMPOSE_DATABASE_URL COMPOSE_VALKEY_URL

	# shellcheck source=scripts/database/internal/common.sh
	source "${DATABASE_SCRIPTS_DIR}/common.sh"
	# shellcheck source=scripts/database/internal/ensure.sh
	source "${DATABASE_SCRIPTS_DIR}/ensure.sh"
}

container_ops_ensure_infra() {
	database_ensure_ready
}

container_ops_run_app() {
	local jwt="${JWT_SECRET_KEY:?set JWT_SECRET_KEY via env profile}"
	if container_app_running; then
		container_compose "${COMPOSE_FILE_ARGS[@]}" exec -T \
			-e "JWT_SECRET_KEY=${jwt}" \
			app "$@"
	else
		container_compose "${COMPOSE_FILE_ARGS[@]}" run --rm \
			-e "JWT_SECRET_KEY=${jwt}" \
			-e "RUN_MIGRATIONS=false" \
			app "$@"
	fi
}

container_ops_assert_seed_allowed() {
	container_ops_run_app python -c "
from todos_app.infrastructure.persistence.seeding.runner import assert_seed_allowed
assert_seed_allowed()
print('Confirmed: seeding is allowed for this environment.')
"
}
