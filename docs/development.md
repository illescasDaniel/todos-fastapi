# Development

## Code quality and linting (Ruff)

This project uses [Ruff](https://github.com/astral-sh/ruff) for lightning-fast Python linting, import sorting, and formatting.

With your virtual environment active and development dependencies installed, you can run:

- **Check code for linting/style issues:**
  ```bash
  ./scripts/run_ruff.sh
  ```

## Type checking (basedpyright)

[basedpyright](https://docs.basedpyright.com/) runs in **strict** mode on `src/` (`pyproject.toml` → `[tool.basedpyright]`). This is a **local developer** check (editor integration or manual `basedpyright` runs) — CI currently runs Ruff and pytest only, not basedpyright. Fix type errors in `src/todos_app/` when introducing or changing typed APIs; test files may use targeted `# pyright: ignore` where pytest fixtures require it.

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

## Running tests

Automated tests use [pytest](https://docs.pytest.org/) with [pytest-asyncio](https://pytest-asyncio.readthedocs.io/). Install dev dependencies first (`pip install -e ".[dev]"`).

With `.venv` active:

```bash
chmod +x scripts/run_tests.sh   # once, if needed
./scripts/run_tests.sh
./scripts/run_tests.sh -m unit
./scripts/run_tests.sh -m integration
./scripts/run_tests.sh --coverage
./scripts/run_tests.sh --coverage -m unit
```

Tests use a PostgreSQL test database and a fixed JWT secret from [`tests/conftest.py`](../tests/conftest.py); they do not use Compose volumes or a host dev database. Default `TEST_DATABASE_URL` uses `POSTGRES_PORT` from `.env` (default `5432`) — ensure PostgreSQL is reachable on `127.0.0.1:${POSTGRES_PORT}` (the infra Compose stack provides this locally).

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

Requires dev dependencies (`pytest-cov` is included in `.[dev]`). Pass `--coverage` to `run_tests.sh`, or call `run_coverage.sh` directly:

```bash
./scripts/run_tests.sh --coverage
./scripts/run_coverage.sh
```

Both run the suite with a terminal report (missed lines) and an HTML report under `htmlcov/`. Extra pytest arguments are forwarded (for example `./scripts/run_tests.sh --coverage -m unit`).

## Stack verification

[`scripts/verify_stack.sh`](../scripts/verify_stack.sh) exercises every local deployment path in one run (~5–15 min with image builds). This is **manual, slow stack verification** — not a quick smoke test and not part of routine development or CI.

| Scenario | pytest | HTTP smoke |
|----------|--------|------------|
| Bare-metal PostgreSQL (venv API + infra-only Compose) | — | yes (Valkey + PostgreSQL) |
| Full-stack Compose (Path B: `docker-compose.infra.yml` + `docker-compose.app.base.yml` + `docker-compose.app.with-infra.yml`) | — | yes |
| CI parity (once at end) | `./scripts/run_tests.sh --coverage` on PostgreSQL | — |

Per environment: migrate, seed, then **HTTP smoke checks** — `GET /health`, `POST /auth/login` (seeded `jane` / `changeme`), `GET /todos?limit=5`. The full unit + integration suite runs **once** at the end (same as CI), against the PostgreSQL test database from [`tests/conftest.py`](../tests/conftest.py).

**When to run:** after changes to Compose, container scripts, Alembic, or `DATABASE_URL` wiring; before a demo or release; when you explicitly want all local deployment paths checked.

**When not to run:** routine feature work (use `./scripts/run_tests.sh` instead).

**Prerequisites:** `.venv` with `pip install -e ".[dev]"`, `curl`, rootless Podman, `API_PORT` free (default `8000`), PostgreSQL on `127.0.0.1:${POSTGRES_PORT}` (default `5432`). Set `POSTGRES_PASSWORD` in `.env`.

```bash
./scripts/verify_stack.sh                         # all scenarios + coverage
./scripts/verify_stack.sh --only postgres         # bare-metal PostgreSQL only
./scripts/verify_stack.sh --only compose-postgres # full-stack Compose only
./scripts/verify_stack.sh --skip-coverage         # skip final coverage gate
```

← [Project README](../README.md)
