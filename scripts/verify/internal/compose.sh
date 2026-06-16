# shellcheck shell=bash
# Full-stack Compose verification (Path B; HTTP smoke only)

verify_run_compose() {
	local scenario_name="$1"
	local skip_http="${2:-false}"
	local keep_stack="${3:-false}"

	local start_ts end_ts elapsed
	local http_result="-"

	start_ts=$(date +%s)
	echo ""
	echo "=== ${scenario_name} ==="

	verify_load_local_profile
	cd "$PROJECT_ROOT" || return

	"$PROJECT_ROOT/scripts/database/wipe.sh" --yes
	if ! "$PROJECT_ROOT/scripts/container/up.sh"; then
		end_ts=$(date +%s)
		elapsed=$((end_ts - start_ts))
		verify_record_result "$scenario_name" "-" "fail" "$elapsed"
		if [[ "$keep_stack" != "true" ]]; then
			"$PROJECT_ROOT/scripts/container/down.sh" --remove || true
		fi
		return 1
	fi
	"$PROJECT_ROOT/scripts/database/seed.sh"

	if [[ "$skip_http" != "true" ]]; then
		if verify_http_smoke "http://${VERIFY_API_HOST}:${VERIFY_API_PORT}"; then
			http_result="ok"
		else
			end_ts=$(date +%s)
			elapsed=$((end_ts - start_ts))
			verify_record_result "$scenario_name" "-" "fail" "$elapsed"
			if [[ "$keep_stack" != "true" ]]; then
				"$PROJECT_ROOT/scripts/container/down.sh" --remove || true
			fi
			return 1
		fi
	fi

	if [[ "$keep_stack" != "true" ]]; then
		"$PROJECT_ROOT/scripts/container/down.sh" --remove
	fi

	end_ts=$(date +%s)
	elapsed=$((end_ts - start_ts))

	verify_record_result "$scenario_name" "-" "$http_result" "$elapsed"
	echo "=== ${scenario_name}: done (${elapsed}s) ==="
}
