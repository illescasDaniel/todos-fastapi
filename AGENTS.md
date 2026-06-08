# Agent Working Notes

## Architecture

Before making structural or feature changes, read [docs/architecture.md](docs/architecture.md).
Follow the layer boundaries, Protocol-based ports, and Depends injection patterns described there.

- Put shared orchestration in `application/`; keep routers thin (parse/map, call use case, map response).
- Login orchestration lives in `application/auth.py` (credential lookup and token issuance).
- Register new application/domain exceptions in `core/exceptions.py`; map them from `application/errors.py`. HTTP detail strings live in `core/http_errors.py`.
- Wire concrete adapters only through `core/dependencies.py` — routes depend on port `*Dep` aliases, not `AsyncSession` or ORM types.
- For new routes, reuse `OpenAPIResponse.merge_*` helpers from `api/openapi_responses.py` for documented error responses.
- Request/response mapping belongs in `api/<feature>/mappers.py`, not in routers.

## Documentation map

| Topic | Doc |
|-------|-----|
| Layer boundaries, DI, testing layout | [docs/architecture.md](docs/architecture.md) |
| Schema, migrations, seed/wipe | [docs/database.md](docs/database.md) |
| JWT login, roles, route protection | [docs/authentication.md](docs/authentication.md) |
| Local setup, venv, Podman Compose | [docs/getting-started.md](docs/getting-started.md) |
| HTTP routes and OpenAPI | [docs/api.md](docs/api.md) |
| Manual HTTP samples (auth flow, seed IDs, request bodies) | [docs/api.http](docs/api.http) |
| Lint, tests, coverage | [docs/development.md](docs/development.md) |
| Stack verification (manual, Compose + PostgreSQL) | [docs/development.md#stack-verification](docs/development.md#stack-verification) — `./scripts/verify_stack.sh` |

## Package layout (`__init__.py`)

This project uses **implicit namespace packages** (PEP 420): layer folders such as `application/`, `domain/`, `api/`, and `infrastructure/` do **not** need `__init__.py` files for imports to work.

- **Do not** add empty or boilerplate `__init__.py` files when creating new modules or directories under `src/todos_app/`.
- **Do not** add `__init__.py` only to re-export symbols; import from the concrete module instead (for example `from todos_app.application import users`, not package-level `__all__` in `__init__.py`).
- Only add `__init__.py` when there is a concrete, documented reason (for example a deliberate public package API that cannot live in a normal module file).

## Python environment rule

- **Requires Python 3.14+** (stdlib `uuid.uuid7()`; aligned with the [Dockerfile](Dockerfile)).
- Never install Python packages globally for this project.
- Always use the project virtual environment at `.venv` before running `pip`, `python -m pip`, `uv pip`, tests, or linters.
- If `.venv` is not active, activate it first.

## Before dependency commands

- Confirm `.venv` is active (`VIRTUAL_ENV` points to `.venv`) or use the `.venv` interpreter explicitly.
- Only run install commands inside that environment (for example: `pip install -e ".[dev]"`).

## Python formatting and autofix

- Generated Python code must use **tabs** for indentation (Ruff enforces this).
- Run Ruff from the **repository root** via the `ruff-check-format` skill.
- After making Python code changes, use the `ruff-check-format` skill.

## Type checking

- [basedpyright](https://docs.basedpyright.com/) runs in **strict** mode on `src/` (`pyproject.toml` → `[tool.basedpyright]`).
- Fix type errors in `src/todos_app/` when introducing or changing typed APIs; test files may use targeted `# pyright: ignore` where pytest fixtures require it.
- For third-party types used only in annotations, use `TYPE_CHECKING` imports; lazy runtime loading belongs in factory/guard modules — see [docs/development.md#type-only-imports-and-lazy-driver-loading](docs/development.md#type-only-imports-and-lazy-driver-loading).

## Testing

Full layout, fixtures, and conventions: [docs/architecture.md#testing](docs/architecture.md#testing).

When adding or changing behavior, place tests by layer:

| Change | Location |
|--------|----------|
| Domain rules (e.g. authorization) | `tests/unit/domain/` |
| Use cases | `tests/unit/application/` with fakes from `tests/fakes/` |
| API mappers | `tests/unit/api/` |
| Repository adapters | `tests/integration/persistence/` |
| HTTP routes | `tests/integration/api/` — reuse `tests/factories.py` and `integration/api/helpers.py` |

- Set `pytestmark = pytest.mark.unit` or `pytest.mark.integration` on **every** test module.
- Tests use a PostgreSQL test database from `tests/conftest.py` via Alembic `upgrade head` — they do **not** use Compose volumes.
- `JWT_SECRET_KEY` is set in `tests/conftest.py`; the suite does not depend on `.env`.
- After substantive changes, use the `run-tests` skill. Default to `--coverage` when `src/todos_app/` changes (project enforces **90%** line coverage on `todos_app` in `pyproject.toml`).

## CI

GitHub Actions (`.github/workflows/ci.yml`) on push/PR to `main`:

1. Python **3.14**, `python -m venv .venv`, `pip install -e ".[dev]"`
2. `./scripts/run_ruff.sh`
3. `./scripts/run_tests.sh --coverage` with `JWT_SECRET_KEY=test-secret-key-for-ci-suite-32bytes!`

CI does not use Podman Compose; Compose is for local full-stack dev only (see `podman-compose` skill).

## Stack verification (manual only)

Do **not** run `./scripts/verify_stack.sh` after routine code changes — use the `run-tests` skill instead (PostgreSQL test DB, fast).

Run stack verification only when:

- Changing Compose, container scripts, Alembic, or `DATABASE_URL` wiring
- The user explicitly asks to validate all local deployment paths
- Preparing a demo or release and you need bare-metal and full-stack Compose checked

See [docs/development.md#stack-verification](docs/development.md#stack-verification). Targeted runs: `--only postgres`, `--only compose-postgres`, etc.

## Schema changes (Alembic)

ORM models live under `src/todos_app/infrastructure/persistence/<feature>/orm.py`. Use the `alembic-migrate` skill:

1. Edit ORM models.
2. `./scripts/migrate.sh revision -m "describe change"` — **review** autogenerate output in `alembic/versions/`.
3. `./scripts/migrate.sh` (upgrade head).
4. Run the `run-tests` skill.

See [docs/database.md](docs/database.md) for PostgreSQL-specific notes.

## Local development paths

| Path | When | Compose / run | DB / cache in `.env` |
|------|------|---------------|----------------------|
| **A — Host app** | Day-to-day API dev (default) | `docker-compose.infra.yml` + `./scripts/start.sh` | `127.0.0.1` |
| **B — Local full stack** | Prod-like local smoke | `docker-compose.infra.yml` + `docker-compose.app.base.yml` + `docker-compose.app.with-infra.yml` via `./scripts/container/up.sh` | `127.0.0.1` (rewritten inside app container) |
| **C — Production** | Staging / production | `docker-compose.app.base.yml` only via `./scripts/container/deploy.sh` | External managed URLs |

- **Migrate / seed / wipe** (`./scripts/migrate.sh`, `./scripts/seed.sh`, `./scripts/wipe.sh`): local Paths A and B only; run DB ops via the app container for Path B. Use the `alembic-migrate` and `db-local-ops` skills.
- **Path B lifecycle** (`up.sh`, `down.sh`, `logs.sh`): use the `podman-compose` skill.
- **Path C lifecycle** (`deploy.sh`, `down.sh --prod`, `logs.sh --prod`): copy [`.env.production.example`](.env.production.example) to `.env` on the deploy host — see [docs/deployment.md](docs/deployment.md#path-c--app-only-compose-primary).

## Identifiers

User and todo primary keys are **UUID v7** via `domain/ids.new_id()` (not `uuid4`). Repositories assign IDs on insert when `entity.id is None`. Stable seed UUIDs live in `domain/ids.py`.

## Project skills

Store project-specific Cursor skills under `.cursor/skills/<skill-name>/SKILL.md`.
Keep shared runnable tooling in repo paths (for example `./scripts/run_ruff.sh`, `./scripts/run_tests.sh`, `./scripts/migrate.sh`) so both humans and agents can execute the same command.

| Skill | Wrapper | Delegates to |
|-------|---------|--------------|
| `ruff-check-format` | `./.cursor/skills/ruff-check-format/scripts/run.sh` | `./scripts/run_ruff.sh` |
| `run-tests` | `./.cursor/skills/run-tests/scripts/run.sh` | `./scripts/run_tests.sh` |
| `alembic-migrate` | `./.cursor/skills/alembic-migrate/scripts/run.sh` | `./scripts/migrate.sh` |
| `db-local-ops` | `./.cursor/skills/db-local-ops/scripts/run.sh` | `./scripts/wipe.sh`, `./scripts/seed.sh` |
| `podman-compose` | `./.cursor/skills/podman-compose/scripts/run.sh` | `./scripts/container/*.sh` (up, down, logs, build); seed/wipe delegate to root scripts |

Optional future skill: `local-dev` (bare-metal API server lifecycle via `start.sh`). Not required for routine agent work.
