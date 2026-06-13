---
name: run-checks
description: Run the full local quality gate (Ruff, basedpyright, MCP tests, CI parity) via run_checks.sh. Use after substantive code changes before considering work done.
disable-model-invocation: true
---

# Run Checks

## When to use

Use this skill after substantive code changes to run the full local quality gate: lint/format, type checking, MCP tests, and CI-parity checks.

## Workflow

1. Ensure the project virtual environment is active (`.venv`) with dev dependencies installed (`pip install -e ".[dev]"`).
2. Run:
   - `./.cursor/skills/run-checks/scripts/run.sh`
   - Add `--full` to also run stack verification (`verify_stack.sh`) after the quality gate.
3. Fix all reported issues (Ruff, basedpyright, pytest/coverage, MCP tests, pip-audit) and rerun until the script exits successfully.
4. Do not consider the task complete while any step fails.

## Constraints

- Do not install packages globally.
- Use `./.cursor/skills/run-checks/scripts/run.sh` as the canonical combined check script for this skill.
- Steps run in order and exit on first failure: Ruff → basedpyright → MCP tests → CI parity (audit + pytest with coverage).
- `JWT_SECRET_KEY` is set in `tests/conftest.py`; tests bootstrap schema via Alembic in `tests/conftest.py`.
- Step scripts live under `scripts/checks/`; top-level wrappers (`run_ruff.sh`, `run_ci.sh`, etc.) delegate there.
