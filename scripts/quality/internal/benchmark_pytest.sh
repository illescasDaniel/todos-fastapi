#!/usr/bin/env bash
# Time pytest suites via tests.sh. Writes a log + TSV under /tmp (or path arg).
# Internal dev tool — not part of CI. Resets local Postgres once for a clean run.
set -euo pipefail

quality_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scripts_dir="$(cd "${quality_dir}/../.." && pwd)"
repo_root="$(cd "${scripts_dir}/.." && pwd)"
TESTS_SH="${repo_root}/scripts/quality/tests.sh"

LOG_FILE="${1:-/tmp/todos-pytest-benchmark-$(date +%Y%m%dT%H%M%S).log}"
PYTHON="${repo_root}/.venv/bin/python"
CPU_COUNT="$(nproc 2>/dev/null || echo 1)"
TSV_FILE="${LOG_FILE}.tsv"

cd "${repo_root}" || exit

log() {
	echo "$*" | tee -a "${LOG_FILE}"
}

bench_run() {
	local label="$1"
	shift
	local cmd_display="$*"
	local start end elapsed exit_code

	log ""
	log "================================================================"
	log "BENCHMARK: ${label}"
	log "Command: ${cmd_display}"
	log "Started: $(date -Iseconds)"

	start="$(date +%s.%N)"
	set +e
	"$@" >>"${LOG_FILE}" 2>&1
	exit_code=$?
	set -e
	end="$(date +%s.%N)"
	elapsed="$("${PYTHON}" -c "print(round(${end} - ${start}, 3))")"

	log "Exit code: ${exit_code}"
	log "Elapsed: ${elapsed}s"
	printf '%s\t%s\t%s\t%s\n' "${label}" "${exit_code}" "${elapsed}" "${cmd_display}" >>"${TSV_FILE}"
}

: >"${LOG_FILE}"

log "pytest benchmark (serial)"
log "Repo: ${repo_root}"
log "Log: ${LOG_FILE}"
log "CPU cores (nproc): ${CPU_COUNT}"
log "Runner: ${TESTS_SH}"
log "pytest: $("${repo_root}/.venv/bin/pytest" --version 2>&1)"

echo "label	exit_code	elapsed_sec	command" >"${TSV_FILE}"

log ""
log "=== SETUP: reset PostgreSQL (match .env POSTGRES_PASSWORD) ==="
bash -c 'source scripts/database/internal/setup.sh && database_load_env && source scripts/database/internal/postgresql.sh && postgres_reset_container' >>"${LOG_FILE}" 2>&1

log ""
log "=== WARMUP ==="
"${TESTS_SH}" -m unit -q >>"${LOG_FILE}" 2>&1

log ""
log "=== BENCHMARK RUNS ==="

bench_run "full suite" \
	"${TESTS_SH}" -q

bench_run "unit only" \
	"${TESTS_SH}" -q -m unit

bench_run "integration only" \
	"${TESTS_SH}" -q -m integration

bench_run "full + coverage" \
	"${TESTS_SH}" --coverage -q

log ""
log "=== SUMMARY ==="
if command -v column >/dev/null 2>&1; then
	column -t -s $'\t' "${TSV_FILE}" | tee -a "${LOG_FILE}"
else
	tee -a "${LOG_FILE}" <"${TSV_FILE}"
fi

log ""
log "Benchmark complete."
log "Log: ${LOG_FILE}"
log "TSV:  ${TSV_FILE}"
