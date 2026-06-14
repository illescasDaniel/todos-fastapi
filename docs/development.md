# Development

## Code quality and linting (Ruff)

This project uses [Ruff](https://github.com/astral-sh/ruff) for lightning-fast Python linting, import sorting, and formatting.

With your virtual environment active and development dependencies installed, you can run:

- **Check code for linting/style issues:**
  ```bash
  ./scripts/quality/ruff.sh
  ```

## Type checking (basedpyright)

[basedpyright](https://docs.basedpyright.com/) runs in **strict** mode on `src/`, `tests/`, and `mcp/todos-backend/` (root `pyproject.toml` → `[tool.basedpyright]`). Included in the quality gate (`./scripts/quality/checks.sh`). Fix type errors in `src/todos_app/` when introducing or changing typed APIs; test and MCP files may use targeted `# pyright: ignore` where pytest fixtures or third-party stubs require it.

From the repo root with `.venv` active:

```bash
./scripts/quality/pyright.sh
```

The script auto-installs `mcp/todos-backend/` editable when `todos_mcp` is not importable. For MCP-only development with `mcp/todos-backend/.venv`, run `basedpyright` from that directory (see `mcp/todos-backend/pyproject.toml` → `[tool.basedpyright]`).

### Type-only imports and lazy driver loading

Infrastructure adapters sometimes need a **third-party type in annotations** without importing that package at module load time. Use the standard `TYPE_CHECKING` pattern:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from valkey.asyncio import Valkey


class ValkeyUserAuthCache:
    def __init__(self, client: Valkey) -> None:
        self._client = client
```

- **`TYPE_CHECKING`** is `False` at runtime and `True` when basedpyright analyzes the file, so the import runs only for the type checker.
- **Python 3.14+** (this project’s minimum) defers annotation evaluation ([PEP 649](https://peps.python.org/pep-0649/)), so `Valkey` does not need to exist at runtime when the class body runs.

When code must **construct** or **call** a third-party client, import it at the use site (or via `importlib.import_module`) after an explicit guard:

| Module | Guard | Runtime import |
|--------|-------|----------------|
| [`valkey_client.py`](../src/todos_app/infrastructure/cache/valkey_client.py) | `require_valkey_driver()` | `from valkey.asyncio import Valkey` inside `create_valkey_client` |
| [`database.py`](../src/todos_app/infrastructure/persistence/database.py) | `require_async_db_driver(url)` | `importlib.import_module("asyncpg")` when the URL needs it |

`valkey_user_auth_cache.py` only receives an already-built client, so it uses **`TYPE_CHECKING` only** — no runtime `valkey` import in that module.

Use this split for new infrastructure adapters: **factory / guard module** owns lazy loading; **adapter modules** type against the client with `TYPE_CHECKING` when they do not import the driver themselves.

## Combined quality gate

After substantive changes, run the full local check sequence. All steps run even when one fails; a summary report prints at the end. Exit 1 only when errors exist (warnings-only passes):

```bash
./scripts/quality/checks.sh
```

Steps (see `scripts/quality/checks.sh`): dependency audit → Ruff → basedpyright → MCP tests → pytest with coverage. Default: Ruff check-only. Use `--fix` for Ruff autofix before the gate; `--full` adds stack verification (implies `--fix`, local only).

For deployment-path smoke (Compose, bare-metal, HTTP checks — slow):

```bash
./scripts/quality/checks.sh --fix   # Ruff autofix, then gate
./scripts/quality/checks.sh --full  # --fix + verify_stack
```

Individual steps:

```bash
./scripts/quality/ruff.sh
./scripts/quality/pyright.sh
./scripts/quality/tests.sh --coverage
```

MCP tests and dependency audit are gate-only (no standalone scripts); run `./scripts/quality/checks.sh`.

## Running tests

Automated tests use [pytest](https://docs.pytest.org/) with [pytest-asyncio](https://pytest-asyncio.readthedocs.io/). Install dev dependencies first (`pip install -e ".[dev]"`).

With `.venv` active:

```bash
chmod +x scripts/quality/tests.sh   # once, if needed
./scripts/quality/tests.sh
./scripts/quality/tests.sh -m unit
./scripts/quality/tests.sh -m integration
./scripts/quality/tests.sh --coverage
./scripts/quality/tests.sh --coverage -m unit
```

Tests use a PostgreSQL test database and a fixed JWT secret from [`tests/conftest.py`](../tests/conftest.py); they do not use Compose volumes or a host dev database. When `TEST_DATABASE_URL` is unset, the test runner derives it from `.env` secrets and `POSTGRES_PORT` in [`config/ports.env`](../config/ports.env). CI sets `TEST_DATABASE_URL` explicitly in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

**Valkey is not required for tests** — `conftest.py` overrides `UserAuthCache` with `FakeUserAuthCache` so CI stays fast without a Valkey service.

| Suite | Location | What it covers |
|-------|----------|----------------|
| **Unit** | `tests/unit/domain/` | Authorization helpers (`list_owner_filter`, owner resolution, `require_admin`) |
| **Unit** | `tests/unit/application/` | Todo and user use cases with in-memory fakes (`tests/fakes/`) |
| **Unit** | `tests/unit/api/` | Request/response mappers for todos and users |
| **Unit** | `tests/unit/infrastructure/` | JWT access-token verifier edge cases |
| **Integration** | `tests/integration/persistence/` | `SqlAlchemyTodoRepository` and `SqlAlchemyUserRepository` (including `owner_id` scope and cascade delete) |
| **Integration** | `tests/integration/api/` | Auth login, todo and user HTTP routes via `httpx.AsyncClient` |

Shared helpers: [`tests/factories.py`](../tests/factories.py) (JSON payloads), [`tests/integration/api/helpers.py`](../tests/integration/api/helpers.py) (`register_and_login`, `auth_headers`).

See [Testing](architecture.md#testing) for the full test tree, fixtures, and conventions.

### Coverage (optional)

Requires dev dependencies (`pytest-cov` is included in `.[dev]`). Pass `--coverage` to `run_tests.sh`:

```bash
./scripts/quality/tests.sh --coverage
```

Runs the suite with a terminal report (missed lines) and an HTML report under `htmlcov/`. Extra pytest arguments are forwarded (for example `./scripts/quality/tests.sh --coverage -m unit`).

## Stack verification

[`scripts/verify/verify_stack.sh`](../scripts/verify/verify_stack.sh) exercises every local deployment path in one run (~5–15 min with image builds). This is **manual, slow stack verification** — not a quick smoke test and not part of routine development or CI.

| Scenario | pytest | HTTP smoke |
|----------|--------|------------|
| `bare-metal/postgres` | — | migrate, seed, host API, smoke |
| `compose/postgres` | — | Path B up, seed, smoke |
| `ci/coverage` (unless `--skip-coverage`) | `./scripts/quality/tests.sh --coverage` on PostgreSQL | — |

Per environment: migrate, seed, then **HTTP smoke checks** — `GET /health`, `POST /auth/login` (seeded `jane` / `changeme`), `GET /todos?limit=5`. The full unit + integration suite runs **once** at the end (same as CI), against the PostgreSQL test database from [`tests/conftest.py`](../tests/conftest.py).

**When to run:** after changes to Compose, container scripts, Alembic, or `DATABASE_URL` wiring; before a demo or release; when you explicitly want all local deployment paths checked.

**When not to run:** routine feature work (use `./scripts/quality/tests.sh` instead).

**Prerequisites:** `.venv` with `pip install -e ".[dev]"`, `curl`, rootless Podman, `API_PORT` free (from `config/ports.env`), PostgreSQL on `127.0.0.1:${POSTGRES_PORT}`. Set `POSTGRES_PASSWORD`, `POSTGRES_USER`, and `POSTGRES_DB` in `.env` (ports in `config/ports.env`).

```bash
./scripts/verify/verify_stack.sh                         # all scenarios + coverage
./scripts/verify/verify_stack.sh --only postgres         # bare-metal PostgreSQL only
./scripts/verify/verify_stack.sh --only compose-postgres # full-stack Compose only
./scripts/verify/verify_stack.sh --skip-coverage         # skip final coverage gate
```

## Dependency auditing and lockfiles

### pip-audit

Audits installed PyPI packages in the active `.venv` (editable local packages such as `fastapi-todos` and `todos-mcp` are skipped). Run via the quality gate:

```bash
./scripts/quality/checks.sh
```

Included in `[dev]` dependencies (`pip-audit`). Invoked by the quality gate (`./scripts/quality/checks.sh`).

### uv lockfile (reproducible installs)

If you have [`uv`](https://github.com/astral-sh/uv) installed you can generate a lockfile for reproducible installs:

```bash
uv lock          # generate / refresh uv.lock
uv sync --frozen # install exact pinned versions
```

`uv.lock` is committed to the repository and should be kept up to date when dependencies change. It is **not** in `.gitignore`.

← [Project README](../README.md)
