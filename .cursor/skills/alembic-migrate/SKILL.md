---
name: alembic-migrate
description: Run Alembic migrations via migrate.sh (upgrade, autogenerate revision, current, history). Use when changing ORM schema, applying migrations, or reviewing autogenerate output.
disable-model-invocation: true
---

# Alembic Migrate

## When to use

Use this skill when the user changes ORM models, needs to apply pending migrations, autogenerate a revision, or inspect migration history.

## Workflow

1. Ensure `DATABASE_URL` in `.env` points at the intended local database and Podman is available.
2. For schema changes:
   - Edit ORM models under `src/todos_app/infrastructure/persistence/<feature>/orm.py`.
   - Run `./.cursor/skills/alembic-migrate/scripts/run.sh revision -m "describe change"` (host `.venv` required).
   - **Review** the generated file in `alembic/versions/` — never commit autogenerate output blindly.
   - Run `./.cursor/skills/alembic-migrate/scripts/run.sh` (upgrade head via app container).
3. Other commands:
   - `./.cursor/skills/alembic-migrate/scripts/run.sh current`
   - `./.cursor/skills/alembic-migrate/scripts/run.sh history`
4. After schema changes, run the `run-tests` skill to confirm tests still pass.

## Constraints

- Do not install packages globally.
- Use `./.cursor/skills/alembic-migrate/scripts/run.sh` as the canonical migration wrapper for this skill.
- Automated tests run Alembic `upgrade head` in `tests/conftest.py` — keep migration scripts consistent with ORM models.
- `upgrade` / `current` / `history` run inside the app container; `revision` autogenerate runs on the host `.venv`.
- Apply migrations before `./scripts/start.sh` on a fresh database.
