# shellcheck shell=bash
# Bare-metal stack verification (venv API + infra-only Compose: Valkey + PostgreSQL)

VERIFY_BARE_METAL_API_PID=""

verify_bare_metal_cleanup() {
	local exit_code=$?
	if [[ -n "$VERIFY_BARE_METAL_API_PID" ]] && kill -0 "$VERIFY_BARE_METAL_API_PID" 2>/dev/null; then
		kill "$VERIFY_BARE_METAL_API_PID" 2>/dev/null || true
		wait "$VERIFY_BARE_METAL_API_PID" 2>/dev/null || true
	fi
	VERIFY_BARE_METAL_API_PID=""
	database_stop_container || true
	trap - EXIT INT TERM HUP
	return "$exit_code"
}

verify_run_bare_metal() {
	local scenario_name="$1"
	local skip_http="${2:-false}"

	local start_ts end_ts elapsed
	local http_result="-"

	start_ts=$(date +%s)
	echo ""
	echo "=== ${scenario_name} ==="

	verify_load_local_profile
	cd "$PROJECT_ROOT" || return

	verify_load_database_helpers

	# Path B app container binds API_PORT; host bare-metal needs a clean port.
	podman stop todos-app 2>/dev/null || true
	podman rm -f todos-app 2>/dev/null || true

	database_reset_container
	database_ensure_ready

	trap verify_bare_metal_cleanup EXIT INT TERM HUP

	unset TODOS_COMPOSE
	database_clear_settings_cache

	verify_run_alembic_upgrade
	verify_run_seeding

	if [[ "$skip_http" != "true" ]]; then
		verify_port_available "$VERIFY_API_PORT"
		database_clear_settings_cache
		# shellcheck disable=SC1091
		source "$PROJECT_ROOT/.venv/bin/activate"
		export PYTHONPATH=src
		unset TODOS_COMPOSE
		export JWT_SECRET_KEY="${JWT_SECRET_KEY:?set JWT_SECRET_KEY via env profile}"
		export POSTGRES_URL VALKEY_URL
		fastapi run --entrypoint todos_app.main:app --host "$VERIFY_API_HOST" --port "$VERIFY_API_PORT" &
		VERIFY_BARE_METAL_API_PID=$!
		verify_wait_for_health "http://${VERIFY_API_HOST}:${VERIFY_API_PORT}"
		if verify_http_smoke "http://${VERIFY_API_HOST}:${VERIFY_API_PORT}"; then
			http_result="ok"
		else
			end_ts=$(date +%s)
			elapsed=$((end_ts - start_ts))
			verify_record_result "$scenario_name" "-" "fail" "$elapsed"
			verify_bare_metal_cleanup
			trap - EXIT INT TERM HUP
			return 1
		fi
	fi

	end_ts=$(date +%s)
	elapsed=$((end_ts - start_ts))
	verify_bare_metal_cleanup
	trap - EXIT INT TERM HUP

	verify_record_result "$scenario_name" "-" "$http_result" "$elapsed"
	echo "=== ${scenario_name}: done (${elapsed}s) ==="
}
