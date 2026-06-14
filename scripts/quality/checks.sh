#!/usr/bin/env bash

set -u

# Quality gate — same steps locally and in GitHub Actions.
# --fix: ruff autofix+format; --full: --fix plus verify_stack (local only).

quality_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
internal_dir="${quality_dir}/internal"
scripts_dir="$(cd "${quality_dir}/.." && pwd)"
repo_root="$(cd "${scripts_dir}/.." && pwd)"

# shellcheck source=scripts/quality/internal/gate.sh
source "${internal_dir}/gate.sh"

FULL=false
FIX=false
forwarded_args=()
for arg in "$@"; do
	case "${arg}" in
	--full)
		FULL=true
		FIX=true
		;;
	--fix)
		FIX=true
		;;
	*)
		forwarded_args+=("${arg}")
		;;
	esac
done

if [[ "${CI:-}" == "true" && "${FIX}" == true ]]; then
	echo "note: --fix ignored in CI (check-only mode)"
	FIX=false
fi

GATE_PLANNED_STEPS=6
if [[ "${FULL}" == true ]]; then
	GATE_PLANNED_STEPS=7
fi

gate_init

# shellcheck source=scripts/quality/internal/lib.sh
source "${internal_dir}/lib.sh"
lib_require_venv
PYTHON="${LIB_REPO_ROOT}/.venv/bin/python"
cd "${repo_root}" || exit

set +e

# --- 1. audit ---
gate_step_start "audit"
audit_output="$("${internal_dir}/audit_deps.sh" 2>&1)"
audit_exit=$?
printf '%s\n' "${audit_output}"
if [[ "${audit_exit}" -eq 0 ]]; then
	emit_out="$(printf '%s' "${audit_output}" | "${PYTHON}" "${internal_dir}/gate_emit.py" audit 2>&1)"
	while IFS= read -r line; do
		if [[ "${line}" == GATE_SUMMARY* ]]; then
			summary="${line}"
		elif [[ "${line}" == ::* ]]; then
			echo "${line}"
		fi
	done <<<"${emit_out}"
	gate_apply_emit_summary "${summary:-GATE_SUMMARY errors=0 warnings=0}"
else
	gate_gha_error "" "" "" "pip-audit" "dependency audit failed (exit ${audit_exit})"
	gate_record_fail 1 0
	gate_add_detail "[audit] exit ${audit_exit}"
fi

# --- 2. ruff ---
gate_step_start "ruff"
if [[ "${FIX}" == true ]]; then
	ruff_output="$("${quality_dir}/ruff.sh" 2>&1)"
	ruff_exit=$?
	printf '%s\n' "${ruff_output}"
	if [[ "${ruff_exit}" -eq 0 ]]; then
		gate_record_pass
	else
		gate_gha_error "" "" "" "ruff" "ruff fix/format failed (exit ${ruff_exit})"
		gate_record_fail 1 0
		gate_add_detail "[ruff] exit ${ruff_exit}"
	fi
else
	# shellcheck source=scripts/quality/internal/lib.sh
	source "${internal_dir}/lib.sh"
	lib_require_venv
	lib_activate_venv
	lib_ruff_targets
	ruff_check_out="$(ruff check "${LIB_RUFF_TARGETS[@]}" --output-format=github 2>&1)"
	printf '%s\n' "${ruff_check_out}"
	emit_out="$(printf '%s\n' "${ruff_check_out}" | "${PYTHON}" "${internal_dir}/gate_emit.py" ruff-github 2>&1)"
	summary=""
	while IFS= read -r line; do
		if [[ "${line}" == GATE_SUMMARY* ]]; then
			summary="${line}"
		elif [[ "${line}" == ::* ]]; then
			: # already printed via ruff_check_out for github format
		fi
	done <<<"${emit_out}"
	ruff_format_out="$(ruff format --check "${LIB_RUFF_TARGETS[@]}" 2>&1)"
	ruff_format_exit=$?
	if [[ -n "${ruff_format_out}" ]]; then
		printf '%s\n' "${ruff_format_out}"
	fi
	ruff_errors=0
	ruff_warnings=0
	if [[ -n "${summary}" ]]; then
		ruff_errors="$(echo "${summary}" | sed -n 's/.*errors=\([0-9]*\).*/\1/p')"
		ruff_warnings="$(echo "${summary}" | sed -n 's/.*warnings=\([0-9]*\).*/\1/p')"
	fi
	if [[ "${ruff_format_exit}" -ne 0 ]]; then
		ruff_errors=$((ruff_errors + 1))
		gate_gha_error "" "" "" "ruff" "format check failed"
		gate_add_detail "[ruff] format check failed"
	fi
	if [[ "${ruff_errors}" -gt 0 || "${ruff_format_exit}" -ne 0 ]]; then
		gate_record_fail "${ruff_errors:-1}" "${ruff_warnings:-0}"
	elif [[ "${ruff_warnings:-0}" -gt 0 ]]; then
		gate_record_step "warn" 0 "${ruff_warnings}"
	else
		gate_record_pass
	fi
fi

# --- 3. shell ---
gate_step_start "shell"
if [[ "${FIX}" == true ]]; then
	shell_output="$("${quality_dir}/shellcheck.sh" --fix 2>&1)"
else
	shell_output="$("${quality_dir}/shellcheck.sh" 2>&1)"
fi
shell_exit=$?
printf '%s\n' "${shell_output}"
if [[ "${shell_exit}" -eq 0 ]]; then
	gate_record_pass
else
	gate_gha_error "" "" "" "shell" "shell lint/format failed (exit ${shell_exit})"
	gate_record_fail 1 0
	gate_add_detail "[shell] exit ${shell_exit}"
fi

# --- 4. pyright ---
gate_step_start "basedpyright"
pyright_json="$("${quality_dir}/pyright.sh" --outputjson 2>/dev/null)"
pyright_exit=$?
emit_out="$(printf '%s' "${pyright_json}" | "${PYTHON}" "${internal_dir}/gate_emit.py" pyright 2>&1)"
summary=""
while IFS= read -r line; do
	if [[ "${line}" == GATE_SUMMARY* ]]; then
		summary="${line}"
	elif [[ "${line}" == ::* ]]; then
		echo "${line}"
	fi
done <<<"${emit_out}"
if [[ -n "${summary}" ]]; then
	gate_apply_emit_summary "${summary}"
else
	if [[ "${pyright_exit}" -eq 0 ]]; then
		gate_record_pass
	else
		gate_gha_error "" "" "" "basedpyright" "type check failed (exit ${pyright_exit})"
		gate_record_fail 1 0
	fi
fi

# --- 5. mcp tests ---
gate_step_start "mcp tests"
mcp_output="$("${internal_dir}/mcp_tests.sh" "${forwarded_args[@]}" 2>&1)"
mcp_exit=$?
printf '%s\n' "${mcp_output}"
emit_out="$(printf '%s' "${mcp_output}" | "${PYTHON}" "${internal_dir}/gate_emit.py" pytest 2>&1)"
summary=""
while IFS= read -r line; do
	if [[ "${line}" == GATE_SUMMARY* ]]; then
		summary="${line}"
	elif [[ "${line}" == ::* ]]; then
		echo "${line}"
	fi
done <<<"${emit_out}"
if [[ -n "${summary}" ]]; then
	gate_apply_emit_summary "${summary}"
elif [[ "${mcp_exit}" -eq 0 ]]; then
	gate_record_pass
else
	gate_record_fail 1 0
fi

# --- 6. pytest ---
gate_step_start "pytest"
export JWT_SECRET_KEY=test-secret-key-for-ci-suite-32bytes!
export POSTGRES_USER=todos
export POSTGRES_PASSWORD=todos
export POSTGRES_PORT=5432
export TEST_DATABASE_URL=postgresql+asyncpg://todos:todos@127.0.0.1:5432/todos_test
pytest_output="$("${quality_dir}/tests.sh" --coverage 2>&1)"
pytest_exit=$?
printf '%s\n' "${pytest_output}"
emit_out="$(printf '%s' "${pytest_output}" | "${PYTHON}" "${internal_dir}/gate_emit.py" pytest 2>&1)"
summary=""
while IFS= read -r line; do
	if [[ "${line}" == GATE_SUMMARY* ]]; then
		summary="${line}"
	elif [[ "${line}" == ::* ]]; then
		echo "${line}"
	fi
done <<<"${emit_out}"
if [[ -n "${summary}" ]]; then
	gate_apply_emit_summary "${summary}"
elif [[ "${pytest_exit}" -eq 0 ]]; then
	gate_record_pass
else
	gate_record_fail 1 0
fi

# --- 7. verify_stack (optional) ---
if [[ "${FULL}" == true ]]; then
	gate_step_start "verify_stack"
	verify_output="$("${scripts_dir}/verify/verify_stack.sh" --skip-coverage 2>&1)"
	verify_exit=$?
	printf '%s\n' "${verify_output}"
	if [[ "${verify_exit}" -eq 0 ]]; then
		gate_record_pass
	else
		gate_gha_error "" "" "" "verify_stack" "stack verification failed (exit ${verify_exit})"
		gate_record_fail 1 0
		gate_add_detail "[verify_stack] exit ${verify_exit}"
	fi
fi

gate_exit
