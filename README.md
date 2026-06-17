# FastAPI ToDo List API

CI
Python 3.14+
License: MIT

A **demo / portfolio** backend that uses a small todo domain to showcase how a production-style API can be structured. The stack is intentionally full-featured — hexagonal layers, dependency injection, JWT auth, Alembic migrations, PostgreSQL persistence, Valkey auth caching, and a layered test suite — not because a todo list needs all of it, but because the patterns transfer to larger services.

Built with FastAPI, Pydantic validation, async SQLAlchemy persistence via [asyncpg](https://github.com/MagicStack/asyncpg), Valkey for auth caching, and Uvicorn as the ASGI server.

**Requires Python 3.14+** (stdlib `uuid.uuid7()` for primary keys; same version as the [Dockerfile](Dockerfile) and Podman Compose stack).

## API docs and client contracts

FastAPI generates a full **OpenAPI 3** spec from the route definitions and Pydantic models. In local dev (`APP_ENV=local`):

- **Swagger UI** at `/docs` — browse routes, inspect schemas, and send requests from the browser
- **ReDoc** at `/redoc` — alternate reference layout
- **`/openapi.json`** — machine-readable spec for codegen (Postman, OpenAPI Generator, etc.)

For **mobile apps, SPAs, and other clients** that only need request/response shapes (not HTTP metadata), export standalone **JSON Schema** files:

```bash
./scripts/export_json_schemas.sh    # writes schemas/json/
```

See [JSON Schema export](docs/json-schemas.md) for the model list, bundle format, and codegen examples. Route tables and live doc URLs: [docs/api.md](docs/api.md).

## Tech stack

- **FastAPI** — async HTTP API, OpenAPI, dependency injection
- **PostgreSQL** — async SQLAlchemy 2 + asyncpg
- **Valkey** — authenticated-user cache (required at runtime)
- **JWT + Argon2** — login and password hashing
- **Alembic** — schema migrations
- **pytest** — >**90%** line coverage gate on `todos_app`
- **Podman Compose or Docker Compose** — local Valkey + PostgreSQL (scripts accept either `podman compose` or `docker compose`)

> **Security — demo only**
>
> - Seeded users (`jane` / `changeme`, `admin` / `changeme`) are for **local development** only. Do not reuse in staging or production.
> - Interactive OpenAPI UI at `/docs` is available only when `APP_ENV=local`. Staging and production hide `/docs`, `/redoc`, and `/openapi.json`.
> - See [SECURITY.md](SECURITY.md) before publishing or exposing the API on the internet.

## Why this architecture

The todo API is the **vehicle**, not the goal. This repo demonstrates patterns you would keep when the domain grows:

- **Hexagonal layout** — domain ports at the center; HTTP and persistence are swappable adapters.
- **Dependency injection** — routes depend on port types, wired in `core/dependencies.py`.
- **PostgreSQL persistence** — async SQLAlchemy + asyncpg via `postgres.url` (`POSTGRES_URL`).
- **Auth and authorization** — JWT login, Argon2 passwords, owner-or-admin rules on todos and users.
- **Migrations and seeding** — Alembic for schema; explicit seed scripts for local demo data only.
- **Layered tests** — unit tests with fakes, integration tests for repositories and HTTP.

That depth is **intentional**: it shows how to keep business rules testable and infrastructure replaceable without rewriting the API surface.

## Quick start (primary path: infra + host app)

Daily development: Podman or Docker runs **Valkey** and **PostgreSQL** from `[docker-compose.infra.yml](docker-compose.infra.yml)`. The API runs on the host in `.venv` with hot reload.

From the project root (see [Getting started](docs/getting-started.md) for full detail):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp config/profiles/example.toml config/profiles/local.toml
# edit secrets in local.toml (JWT, POSTGRES_PASSWORD, VALKEY_PASSWORD, URLs)
export ENV_PROFILE=local
./scripts/database/migrate.sh     # ensure infra, apply Alembic migrations
./scripts/database/seed.sh        # optional — demo users jane/admin, password changeme
./scripts/start.sh       # host API with hot reload
```

Host env profile uses `127.0.0.1` for PostgreSQL and Valkey. Scripts generate a gitignored root `.env` for Compose from the profile. `./scripts/database/wipe.sh` removes containers and volumes for a full reset; `./scripts/database/migrate.sh` and `./scripts/database/seed.sh` work the same for host-app and full-stack paths.

> **OpenAPI UI** — after `./scripts/start.sh`, open `http://127.0.0.1:8000/docs` (or your `api.port` in `config/profiles/local.toml`). Local only (`APP_ENV=local`); staging and production hide `/docs`, `/redoc`, and `/openapi.json`. Route tables: [docs/api.md](docs/api.md).

### Cursor MCP (agent tools)

A separate MCP server under `[mcp/todos-backend/](mcp/todos-backend/)` lets Cursor agents call the API and run dev scripts (`auth_login`, `todos_create`, `stack_compose_up`, etc.) via typed tools.

1. Install the MCP venv: `cd mcp/todos-backend && python3.14 -m venv .venv && source .venv/bin/activate && pip install -e .`
2. Open the **repo root** in Cursor, enable **todos-backend** in the **Agents** view (config: `[.cursor/mcp.json](.cursor/mcp.json)`).
3. Start the API (`./scripts/start.sh`), then try `health_check` and `auth_login` in Agent chat.

The MCP uses its **own** `.venv` in `mcp/todos-backend/` (not global Python, not the API venv). See [docs/mcp.md](docs/mcp.md).

### Podman Compose — Path B (local full stack)

Same infra plus an app container via `[docker-compose.app.base.yml](docker-compose.app.base.yml)` + `[docker-compose.app.with-infra.yml](docker-compose.app.with-infra.yml)`:

```bash
cp config/profiles/example.toml config/profiles/local.toml
# edit secrets in local.toml (JWT, POSTGRES_PASSWORD, VALKEY_PASSWORD, URLs)
export ENV_PROFILE=local
./scripts/container/up.sh
./scripts/database/seed.sh        # optional — demo data
```

Path B rewrites loopback `POSTGRES_URL` and `VALKEY_URL` to in-network service names inside the container. Host `.env` uses `127.0.0.1`.

Local scripts: `up.sh`, `down.sh`, `logs.sh`, `build.sh`. Production deploy (Path C): copy [`production.example.toml`](config/profiles/production.example.toml) to `config/profiles/production.toml`, set `ENV_PROFILE=production` — see [Deployment](docs/deployment.md#path-c--app-only-compose-primary).

## Quality checks (CI)

The CI badge runs `[.github/workflows/ci.yml](.github/workflows/ci.yml)` on every push and pull request to `main`. The **test** job is the same gate you run locally:

```bash
./scripts/quality/checks.sh          # check-only (matches CI)
./scripts/quality/checks.sh --fix    # Ruff autofix/format, then gate
```

Steps: dependency audit → Ruff → ShellCheck + shfmt (`shellcheck.sh`) → basedpyright → MCP tests → pytest with coverage (90% line gate on `todos_app`). After substantive changes, run `--fix` once, then `checks.sh` again to confirm clean. `--fix` also runs Ruff and shfmt on shell scripts. Optional `./scripts/quality/checks.sh --full` adds local stack verification (not in CI).

Individual steps (`ruff.sh`, `shellcheck.sh`, `pyright.sh`, `tests.sh`) and stack verification are documented in [Development](docs/development.md). CI installs ShellCheck and shfmt before the gate; a separate job scans the base Python image with Trivy (CVE gate — not part of `checks.sh`).

## Documentation


| Guide                                      | Contents                                                                                                                                       |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| [Getting started](docs/getting-started.md) | venv, install, `.env`, migrate, seed, run server                                                                                               |
| [Database](docs/database.md)               | PostgreSQL, Alembic, seeding                                                                                                                   |
| [Authentication](docs/authentication.md)   | JWT login, admin provisioning, sample users, [api.http](docs/api.http)                                                                         |
| [API reference](docs/api.md)               | OpenAPI URLs, Swagger UI, pagination, route tables                                                                                             |
| [JSON Schema export](docs/json-schemas.md) | Export Pydantic API models for mobile/web clients                                                                                              |
| [Development](docs/development.md)         | `[checks.sh](docs/development.md#combined-quality-gate)`, Ruff, pytest, coverage, [stack verification](docs/development.md#stack-verification) |
| [Deployment](docs/deployment.md)           | Podman image, Compose, staging/production                                                                                                      |
| [Architecture](docs/architecture.md)       | Hexagonal layout, DI, code conventions                                                                                                         |
| [MCP server](docs/mcp.md)                  | Cursor agent tools for the API and local dev stack                                                                                             |
| [Contributing](CONTRIBUTING.md)            | How to contribute                                                                                                                              |
| [Security](SECURITY.md)                    | Demo scope, reporting, pre-deploy checklist                                                                                                    |


## Project at a glance

The app uses **ports and adapters** (hexagonal architecture): HTTP and persistence sit on the outside; business rules and port interfaces sit at the center. Dependencies point inward.

Hexagonal architecture overview — see [architecture diagrams](docs/architecture.md#architecture-diagrams) (`docs/images/hexagonal_overview.svg`).

See [docs/architecture.md](docs/architecture.md) for the full layered layout, package tree, and conventions.

```text
todo/
├── config/              # Stacked TOML: base.toml + profiles/ (example, test, local, production)
├── docs/                # Guides, architecture reference, api.http samples
├── alembic/             # Alembic env.py and version scripts
├── scripts/             # start, database, container, quality, verify
├── scripts/quality/     # checks, tests, ruff, pyright (+ internal gate helpers)
├── scripts/verify/      # verify_stack (+ internal scenario helpers)
├── scripts/container/   # Podman Compose: up, deploy, down, logs, build
├── mcp/todos-backend/   # Cursor MCP server (API + lifecycle tools)
├── tests/               # pytest unit and integration suites
├── docker-compose.infra.yml           # Path A/B infra: Valkey + PostgreSQL (127.0.0.1 ports)
├── docker-compose.app.base.yml        # App service (Path B base, Path C production)
├── docker-compose.app.with-infra.yml  # Path B overlay: depends_on bundled infra
├── Dockerfile           # Multi-stage OCI image (podman build)
├── config/profiles/example.toml       # Local dev template → copy to local.toml (gitignored)
├── config/profiles/production.example.toml   # Production template (Path C)
└── src/todos_app/       # Application package — see architecture.md
```

## Author

**Daniel Illescas Romero** — [GitHub](https://github.com/illescasDaniel)

## License

This project is licensed under the [MIT License](LICENSE).