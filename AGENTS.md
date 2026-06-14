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
| Stack verification (manual, Compose + PostgreSQL) | [docs/development.md#stack-verification](docs/development.md#stack-verification) — `./scripts/verify/verify_stack.sh` |
| Cursor MCP (API + lifecycle tools) | [docs/mcp.md](docs/mcp.md) — config at `.cursor/mcp.json`, package at `mcp/todos-backend/` |

## Cursor MCP (prefer over shell skills)

When the **todos-backend** MCP server is enabled in Cursor, **use MCP tools first** for local dev and API interaction. They wrap the same repo scripts as the skills below but are easier for agents to invoke (typed tools, structured JSON responses, no shell quoting).

1. **Read tool schemas** under `mcps/project-0-todo-todos-backend/tools/` before calling.
2. **Prefer MCP** when the server is connected; fall back to project skills or `./scripts/*.sh` only if MCP is disabled or a tool fails.
3. **Destructive MCP tools** (`db_seed`, `db_wipe`, `stack_compose_down` with `remove=true`) require `MCP_ALLOW_DESTRUCTIVE=true` in repo `.env` (preferred for local dev) — see [docs/mcp.md](docs/mcp.md).

| Task | MCP tool | Fallback |
|------|----------|----------|
| Start compose stack (Path B) | `stack_compose_up` | `podman-compose` skill |
| Stop compose stack | `stack_compose_down` | `podman-compose` skill |
| Migrate database | `db_migrate` | `alembic-migrate` skill |
| Seed demo data | `db_seed` | `db-local-ops` skill |
| Wipe local DB volumes | `db_wipe` | `db-local-ops` skill |
| Open Swagger UI | `open_api_docs` | `xdg-open http://127.0.0.1:${API_PORT}/docs` |
| Start host API (Path A) | `stack_start_host` | `./scripts/start.sh` |
| Check API health | `stack_health` or `health_check` | curl `/health` |
| Login / todos / users | `auth_login`, `todos_*`, `users_*` | HTTP or [docs/api.http](docs/api.http) |

Typical full-stack bring-up via MCP: `stack_compose_up` → `db_migrate` → `db_seed` → `open_api_docs`.

### Keep MCP in sync

When you change **HTTP routes**, **request/response shapes**, or **repo scripts** that agents run (migrate, seed, compose, start), update the MCP package in the same change:

| Change | Update |
|--------|--------|
| New/changed route or query param | Matching tool in `mcp/todos-backend/src/todos_mcp/tools/`; refresh [`openapi.snapshot.json`](mcp/todos-backend/openapi.snapshot.json) |
| Script moved/renamed | Paths in `tools/lifecycle.py` and `scripts_runner.py` |
| Env/ports loading | `mcp/todos-backend/src/todos_mcp/config.py`; subprocess allowlist in `scripts_runner.py` if scripts need new vars |
| Tool behavior/docs | Docstrings on `@mcp.tool()` handlers; [`docs/mcp.md`](docs/mcp.md) and [`mcp/todos-backend/README.md`](mcp/todos-backend/README.md) |

Run `./scripts/quality/checks.sh` — MCP tests are part of the gate. `.cursor/mcp.json` rarely changes (only interpreter path or server `env` overrides).

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
- After making Python code changes, use the `run-checks` skill after substantive work (`--fix`, then confirm without `--fix`). Use `ruff-check-format` for Ruff-only autofix.

## Type checking

- [basedpyright](https://docs.basedpyright.com/) runs in **strict** mode on `src/`, `tests/`, and `mcp/todos-backend/` (root `pyproject.toml` → `[tool.basedpyright]`).
- Run from the repository root via `./scripts/quality/pyright.sh` or the `run-pyright` skill.
- Fix type errors in `src/todos_app/` when introducing or changing typed APIs; test files may use targeted `# pyright: ignore` where pytest fixtures require it.
- For third-party types used only in annotations, use `TYPE_CHECKING` imports; lazy runtime loading belongs in factory/guard modules — see [docs/development.md#type-only-imports-and-lazy-driver-loading](docs/development.md#type-only-imports-and-lazy-driver-loading).

## Quality gate (after substantive changes)

After substantive code changes, run the combined check script and fix **all** reported issues before considering work done.

**Local agent workflow** (two steps — do not skip `--fix` on the first run):

1. `./scripts/quality/checks.sh --fix` — Ruff autofix + format, then full gate (audit, basedpyright, MCP tests, pytest with coverage).
2. `./scripts/quality/checks.sh` — confirm clean (Ruff check-only, same as CI). Repeat step 1 and fix remaining issues until this passes.

Or use the `run-checks` skill with the same sequence: `run.sh --fix`, then `run.sh`.

**Cursor agent sandbox:** run `./scripts/quality/checks.sh` (and `--full` / `verify_stack.sh`) via the Shell tool with **full permissions** (`required_permissions: ["all"]`). Default sandbox blocks repo `.env` (secrets) and `.venv/` (see `.cursorignore`); gate needs both for audit, pytest bootstrap, and Podman. Do not remove those ignore entries — unsandbox the command instead. Shell-only lint (`./scripts/quality/shellcheck.sh`) usually passes in the default sandbox.

- Runs all steps each time; prints a final summary report; emits GHA annotations when `GITHUB_ACTIONS=true`. Exit 1 only on errors (warnings-only passes).
- `./scripts/quality/checks.sh --full` — `--fix` plus `./scripts/verify/verify_stack.sh` (local only, not CI); still re-run without flags afterward to confirm if you changed code during the gate.
- Individual steps: `ruff-check-format`, `run-pyright`, `run-tests`, `./scripts/quality/ruff.sh`, `./scripts/quality/pyright.sh` (MCP tests and dependency audit run only via `checks.sh`).

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
- After substantive changes, use the `run-checks` skill (preferred): `./scripts/quality/checks.sh --fix`, then `./scripts/quality/checks.sh` until clean. Use `run-tests` with `--coverage` only when the gate is not needed.

## CI

GitHub Actions (`.github/workflows/ci.yml`) on push/PR to `main`:

1. Python **3.14**, `python -m venv .venv`, `pip install -e ".[dev]"`
2. `./scripts/quality/checks.sh` — check-only (no `--fix`); same command as CI

**Local agents:** run `./scripts/quality/checks.sh --fix`, then `./scripts/quality/checks.sh` until the confirm pass is clean. Add `--full` on the first run only when stack verification is needed (local only).

CI does not use Podman Compose; Compose is for local full-stack dev only (see `podman-compose` skill).

## Stack verification (manual only)

Do **not** run `./scripts/verify/verify_stack.sh` after routine code changes — use the `run-checks` skill (`--fix` then confirm) instead (PostgreSQL test DB, fast).

Run stack verification when:

- Changing Compose, container scripts, Alembic, or `DATABASE_URL` wiring
- The user explicitly asks to validate all local deployment paths
- Preparing a demo or release and you need bare-metal and full-stack Compose checked

Use `./scripts/quality/checks.sh --full` for `--fix`, gate, and stack verification in one command (then `./scripts/quality/checks.sh` to confirm). Or `./scripts/verify/verify_stack.sh` alone for targeted runs (`--only postgres`, `--only compose-postgres`, etc.).

See [docs/development.md#stack-verification](docs/development.md#stack-verification).

## Schema changes (Alembic)

ORM models live under `src/todos_app/infrastructure/persistence/<feature>/orm.py`. Prefer MCP `db_migrate` for upgrades; use the `alembic-migrate` skill as fallback:

1. Edit ORM models.
2. `./scripts/database/migrate.sh revision -m "describe change"` — **review** autogenerate output in `alembic/versions/` (host `.venv`; no MCP wrapper for autogenerate).
3. `db_migrate` MCP tool or `./scripts/database/migrate.sh` (upgrade head).
4. Run the `run-checks` skill: `./scripts/quality/checks.sh --fix`, then `./scripts/quality/checks.sh` (or `run-tests` if only tests changed).

See [docs/database.md](docs/database.md) for PostgreSQL-specific notes.

## Local development paths

| Path | When | Compose / run | DB / cache in `.env` |
|------|------|---------------|----------------------|
| **A — Host app** | Day-to-day API dev (default) | `docker-compose.infra.yml` + `./scripts/start.sh` | `127.0.0.1` |
| **B — Local full stack** | Prod-like local smoke | `docker-compose.infra.yml` + `docker-compose.app.base.yml` + `docker-compose.app.with-infra.yml` via `./scripts/container/up.sh` | `127.0.0.1` (rewritten inside app container) |
| **C — Production** | Staging / production | `docker-compose.app.base.yml` only via `./scripts/container/deploy.sh` | External managed URLs |

- **Migrate / seed / wipe** (`./scripts/database/migrate.sh`, `./scripts/database/seed.sh`, `./scripts/database/wipe.sh`): local Paths A and B only; run DB ops via the app container for Path B. Prefer MCP (`db_migrate`, `db_seed`, `db_wipe`); fall back to `alembic-migrate` and `db-local-ops` skills.
- **Path B lifecycle** (`up.sh`, `down.sh`, `logs.sh`): prefer MCP (`stack_compose_up`, `stack_compose_down`); fall back to the `podman-compose` skill.
- **Path C lifecycle** (`deploy.sh`, `down.sh --prod`, `logs.sh --prod`): copy [`.env.production.example`](.env.production.example) to `.env` on the deploy host — see [docs/deployment.md](docs/deployment.md#path-c--app-only-compose-primary).

## Identifiers

User and todo primary keys are **UUID v7** via `domain/ids.new_id()` (not `uuid4`). Repositories assign IDs on insert when `entity.id is None`. Stable seed UUIDs live in `domain/ids.py`.

## Project skills

Store project-specific Cursor skills under `.cursor/skills/<skill-name>/SKILL.md`.
Keep shared runnable tooling in repo paths (for example `./scripts/quality/checks.sh`, `./scripts/quality/ruff.sh`, `./scripts/quality/tests.sh`, `./scripts/database/migrate.sh`, `./scripts/verify/verify_stack.sh`) so both humans and agents can execute the same command.

**MCP first:** for stack, database, and API tasks, use [Cursor MCP](#cursor-mcp-prefer-over-shell-skills) when `todos-backend` is enabled. Skills below are fallbacks and cover tasks without MCP wrappers (lint, tests, autogenerate revisions).

| Skill | Wrapper | Delegates to |
|-------|---------|--------------|
| `run-checks` | `./.cursor/skills/run-checks/scripts/run.sh` | `./scripts/quality/checks.sh` |
| `ruff-check-format` | `./.cursor/skills/ruff-check-format/scripts/run.sh` | `./scripts/quality/ruff.sh` |
| `run-pyright` | `./.cursor/skills/run-pyright/scripts/run.sh` | `./scripts/quality/pyright.sh` |
| `run-tests` | `./.cursor/skills/run-tests/scripts/run.sh` | `./scripts/quality/tests.sh` |
| `alembic-migrate` | `./.cursor/skills/alembic-migrate/scripts/run.sh` | `./scripts/database/migrate.sh` |
| `db-local-ops` | `./.cursor/skills/db-local-ops/scripts/run.sh` | `./scripts/database/wipe.sh`, `./scripts/database/seed.sh` |
| `podman-compose` | `./.cursor/skills/podman-compose/scripts/run.sh` | `./scripts/container/*.sh` (up, down, logs, build); seed/wipe delegate to root scripts |

Optional future skill: `local-dev` (bare-metal API server lifecycle via `start.sh`). Not required for routine agent work.
