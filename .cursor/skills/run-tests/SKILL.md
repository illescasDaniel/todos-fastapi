---
name: run-tests
description: Run the project's pytest suite via scripts/quality/tests.sh, including optional coverage. Use when running tests, verifying changes, or checking coverage after edits to src/todos_app/.
disable-model-invocation: true
---

# Run Tests

## When to use

Use this skill when the user asks to run tests, verify behavior after code changes, or check line coverage on `todos_app`.

## Workflow

1. Ensure the project virtual environment is active (`.venv`).
2. Run:
   - `./.cursor/skills/run-tests/scripts/run.sh` — full suite
   - `./.cursor/skills/run-tests/scripts/run.sh --coverage` — with coverage (default after `src/todos_app/` changes)
   - `./.cursor/skills/run-tests/scripts/run.sh -m unit` or `-m integration` — filter by marker
3. Review failures; fix code or tests, then rerun until green (or report remaining failures to the user).
4. When coverage may drop, always pass `--coverage` (project enforces **90%** on `todos_app`).

## Constraints

- Do not install packages globally.
- Use `./.cursor/skills/run-tests/scripts/run.sh` as the canonical test runner for this skill.
- Tests bootstrap schema via Alembic `upgrade head` in `tests/conftest.py`.
- `./scripts/quality/tests.sh` sets `ENV_PROFILE=test`, recreates the PostgreSQL container when test-profile credentials do not match, creates `todos_test` if needed, and stops the container afterward only when the script started it. Skips reset when PostgreSQL already accepts test credentials.
- Tests load config from [`config/profiles/test.toml`](config/profiles/test.toml) via `tests/conftest.py`; do not rely on `local.toml` or hand-edited `.env`.
- Every test module must declare `pytestmark = pytest.mark.unit` or `pytest.mark.integration`.
