# Shared env loading for start.sh, migrate.sh, seed.sh, wipe.sh.

database_load_env() {
	DATABASE_SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
	PROJECT_ROOT="$(cd "${DATABASE_SCRIPTS_DIR}/../../.." && pwd)"
	cd "${PROJECT_ROOT}"
	# shellcheck source=scripts/database/internal/common.sh
	source "${DATABASE_SCRIPTS_DIR}/common.sh"
	# shellcheck source=scripts/database/internal/ensure.sh
	source "${DATABASE_SCRIPTS_DIR}/ensure.sh"
	load_database_url
}
