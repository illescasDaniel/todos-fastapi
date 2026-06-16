# Development

## Ruff

[Ruff](https://github.com/astral-sh/ruff) for lint, imports, format. `.venv` + dev deps:

```bash
./scripts/quality/ruff.sh
```

## basedpyright

**Strict** on `src/`, `tests/`, `mcp/todos-backend/` (`pyproject.toml` → `[tool.basedpyright]`). In quality gate. Fix types in `src/todos_app/`; tests/MCP may use `# pyright: ignore`.

```bash
./scripts/quality/pyright.sh
```

Auto-installs MCP editable when `todos_mcp` missing. MCP-only: run from `mcp/todos-backend/` with that `.venv`.

### Type-only imports and lazy drivers

Third-party types in annotations without runtime import — `TYPE_CHECKING`:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from valkey.asyncio import Valkey


class ValkeyUserAuthCache:
    def __init__(self, client: Valkey) -> None:
        self._client = client
```

- `TYPE_CHECKING` false at runtime, true for pyright
- Python 3.14+ defers annotations (PEP 649) — no runtime `Valkey` needed in class body

Construct/call third-party clients after guard:

| Module | Guard | Runtime import |
|--------|-------|----------------|
| [`valkey_client.py`](../src/todos_app/infrastructure/cache/valkey_client.py) | `require_valkey_driver()` | `from valkey.asyncio import Valkey` in `create_valkey_client` |
| [`database.py`](../src/todos_app/infrastructure/persistence/database.py) | `require_async_db_driver(url)` | `importlib.import_module("asyncpg")` |

`valkey_user_auth_cache.py`: `TYPE_CHECKING` only — receives built client.

Pattern: **factory/guard** lazy-loads; **adapter** types client via `TYPE_CHECKING`.

## Quality gate

```bash
./scripts/quality/checks.sh
```

All steps run; summary at end; exit 1 on errors. Steps: audit → Ruff → pyright → MCP tests → pytest+coverage. `--fix` for Ruff autofix; `--full` adds stack verify (local, implies `--fix`).

```bash
./scripts/quality/checks.sh --fix
./scripts/quality/checks.sh --full
```

Individual:

```bash
./scripts/quality/ruff.sh
./scripts/quality/pyright.sh
./scripts/quality/tests.sh --coverage
```

MCP tests + audit: gate only (`checks.sh`).

## Tests

[pytest](https://docs.pytest.org/) + [pytest-asyncio](https://pytest-asyncio.readthedocs.io/). `pip install -e ".[dev]"`.

```bash
chmod +x scripts/quality/tests.sh   # once
./scripts/quality/tests.sh
./scripts/quality/tests.sh -m unit
./scripts/quality/tests.sh -m integration
./scripts/quality/tests.sh --coverage
./scripts/quality/tests.sh --coverage -m unit
```

PostgreSQL test DB via [`conftest.py`](../tests/conftest.py), `ENV_PROFILE=test` ([`test.toml`](../config/profiles/test.toml)) — no Compose volumes or host dev DB. CI: same in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

[`tests.sh`](../scripts/quality/tests.sh) recreates infra Postgres when creds mismatch test profile.

**No Valkey in tests** — `FakeUserAuthCache` override in `conftest.py`.

| Suite | Location | Covers |
|-------|----------|--------|
| Unit | `tests/unit/domain/` | Authorization helpers |
| Unit | `tests/unit/application/` | Use cases + `tests/fakes/` |
| Unit | `tests/unit/api/` | Mappers |
| Unit | `tests/unit/infrastructure/` | JWT verifier |
| Integration | `tests/integration/persistence/` | SQLAlchemy repos (`owner_id`, cascade) |
| Integration | `tests/integration/api/` | HTTP routes via `httpx` |

Helpers: [`factories.py`](../tests/factories.py), [`helpers.py`](../tests/integration/api/helpers.py).

Full tree: [Testing](architecture.md#testing), [GWT naming](architecture.md#gwt-naming).

Benchmark: [test-benchmark.md](test-benchmark.md). Re-run: `./scripts/quality/benchmark_pytest.sh`.

### Coverage

`--coverage` → terminal report + `htmlcov/`. 90% line coverage on `todos_app` (`pyproject.toml`).

## Stack verification

[`verify_stack.sh`](../scripts/verify/verify_stack.sh) — all local deploy paths (~5–15 min). Manual only; not CI; not routine dev.

| Scenario | pytest | HTTP smoke |
|----------|--------|------------|
| `bare-metal/postgres` | — | migrate, seed, host API |
| `compose/postgres` | — | Path B up, seed |
| `ci/coverage` (unless `--skip-coverage`) | `tests.sh --coverage` | — |

Per env: migrate, seed, smoke `GET /health`, `POST /auth/login` (jane/changeme), `GET /todos?limit=5`. Full suite once at end (PostgreSQL test DB).

**Run when:** Compose/container/Alembic/`POSTGRES_URL` changes; pre-demo/release; explicit full-path check.

**Skip for:** routine features — use `tests.sh`.

**Needs:** `.venv` + dev deps, `curl`, rootless Podman, free `api.port`, Postgres on `127.0.0.1:${POSTGRES_PORT}`, `ENV_PROFILE=local`, [`local.toml`](../config/profiles/local.toml).

```bash
./scripts/verify/verify_stack.sh
./scripts/verify/verify_stack.sh --only postgres
./scripts/verify/verify_stack.sh --only compose-postgres
./scripts/verify/verify_stack.sh --skip-coverage
```

## Dependency audit and lockfile

**pip-audit** — active `.venv`; skips editable locals. Via gate:

```bash
./scripts/quality/checks.sh
```

**uv lock** (optional):

```bash
uv lock
uv sync --frozen
```

`uv.lock` committed; update when deps change.

← [Project README](../README.md)
