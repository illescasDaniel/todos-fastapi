---
name: run-tests
description: Run the project's pytest suite via run_tests.sh, including optional coverage. Use when running tests, verifying changes, or checking coverage after edits to src/todos_app/.
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
- `./scripts/run_tests.sh` starts the infra PostgreSQL container when nothing is listening on `127.0.0.1:5432`, creates `todos_test` if needed, and stops the container afterward only when the script started it. Skips container lifecycle when PostgreSQL is already up (for example CI or a running dev stack). Sets `TEST_DATABASE_URL` from `.env` (`POSTGRES_*`) when unset.
- `JWT_SECRET_KEY` is set in `tests/conftest.py`; do not rely on `.env` for the test suite.
- Every test module must declare `pytestmark = pytest.mark.unit` or `pytest.mark.integration`.
