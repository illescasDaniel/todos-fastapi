# HTTP smoke checks for scripts/verify/verify_stack.sh

verify_wait_for_health() {
	local base_url="${1:-http://${VERIFY_API_HOST}:${VERIFY_API_PORT}}"
	local attempts="${2:-45}"
	local i
	for ((i = 1; i <= attempts; i++)); do
		if curl -sf "${base_url}/health" >/dev/null 2>&1; then
			return 0
		fi
		sleep 1
	done
	echo "verify_stack: ${base_url}/health did not respond in time" >&2
	return 1
}

verify_http_smoke() {
	local base_url="${1:-http://${VERIFY_API_HOST}:${VERIFY_API_PORT}}"
	local tmp code token

	tmp="$(mktemp)"
	trap '[[ -n "${tmp:-}" ]] && rm -f "$tmp"' RETURN

	code="$(curl -sS -o "$tmp" -w '%{http_code}' "${base_url}/health")"
	if [[ "$code" != "200" ]]; then
		echo "verify_stack: GET /health expected 200, got ${code}" >&2
		return 1
	fi

	code="$(curl -sS -o "$tmp" -w '%{http_code}' \
		-X POST "${base_url}/auth/login" \
		-H 'Content-Type: application/json' \
		-d '{"username":"jane","password":"changeme"}')"
	if [[ "$code" != "200" ]]; then
		echo "verify_stack: POST /auth/login expected 200, got ${code}" >&2
		cat "$tmp" >&2
		return 1
	fi

	token="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['access_token'])" "$tmp")"

	code="$(curl -sS -o "$tmp" -w '%{http_code}' \
		-H "Authorization: Bearer ${token}" \
		"${base_url}/todos?limit=5")"
	if [[ "$code" != "200" ]]; then
		echo "verify_stack: GET /todos expected 200, got ${code}" >&2
		cat "$tmp" >&2
		return 1
	fi

	return 0
}
