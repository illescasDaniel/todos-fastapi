# Database

**On this page:** [PostgreSQL](#postgresql) · [Database migrations (Alembic)](#database-migrations-alembic) · [Seeding](#seeding) · [Wiping the database](#wiping-the-database)

For first-time setup (venv, `.env`, migrate, seed), see [Getting started](getting-started.md).

For layer boundaries and DI patterns, see [Architecture](architecture.md).

## PostgreSQL

Persistence is **async end-to-end**: route handlers and repository ports are `async`, and SQLAlchemy uses **asyncpg** via `DATABASE_URL` (see [`.env.example`](../.env.example)).

| Setting | Example / notes |
|---------|-----------------|
| **`DATABASE_URL`** | `postgresql+asyncpg://todos:YOUR_POSTGRES_PASSWORD@127.0.0.1:5432/todos` |
| **Local storage** | [`docker-compose.infra.yml`](../docker-compose.infra.yml) — PostgreSQL 16 on `COMPOSE_INFRA_BIND:POSTGRES_PORT` (defaults `127.0.0.1:5432`) |
| **Full-stack overlay** | App container uses `@postgres:5432` (rewritten from host `.env`) |

Set `POSTGRES_PASSWORD` in `.env` before starting database containers — Compose does not ship weak inline defaults. Use the same password in `DATABASE_URL`. These values are for **local development only**; generate fresh credentials per staging or production environment (see [Deployment](deployment.md#local-podman-compose)).

- **Configuration:** set `DATABASE_URL` in `.env`; default in `src/todos_app/core/settings.py` points at local PostgreSQL
- **Sessions:** `AsyncSession` from `async_sessionmaker`, yielded per request via FastAPI `Depends(get_db)`
- **Repositories:** SQLAlchemy adapters — no dialect-specific code in domain ports

**Local setup:** [rootless Podman](../docs/deployment.md#install-podman) (`./scripts/install_podman.sh`), set `DATABASE_URL` and `POSTGRES_PASSWORD` in `.env`, then `./scripts/migrate.sh` and optionally `./scripts/seed.sh`. Migrate and seed run inside the app container; the same commands work for host-app and full-stack workflows.

## Database migrations (Alembic)

Schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/). Migration scripts live under `alembic/versions/`; `alembic/env.py` reads `DATABASE_URL` from the same settings as the app and runs migrations with the async SQLAlchemy driver (`asyncpg`).

| Command | Action |
|---------|--------|
| `./scripts/migrate.sh` | Ensure Valkey + PostgreSQL infra, then apply pending revisions via the app container (`alembic upgrade head`) |
| `./scripts/migrate.sh revision -m "describe change"` | Autogenerate a revision on the host `.venv` (writes to `alembic/versions/`) |
| `./scripts/migrate.sh current` | Show the applied revision |
| `./scripts/migrate.sh history` | List revision history |

**Typical schema change loop:**

1. Edit ORM models under `src/todos_app/infrastructure/persistence/<feature>/orm.py`.
2. `./scripts/migrate.sh revision -m "describe change"`
3. Review the generated file in `alembic/versions/` (always inspect autogenerate output).
4. `./scripts/migrate.sh`
5. `./scripts/run/tests.sh`

Equivalent raw commands (with `.venv` active and `PYTHONPATH=src`):

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic current
```

Automated tests bootstrap schema via Alembic `upgrade head` against a PostgreSQL test database (`TEST_DATABASE_URL` in [`tests/conftest.py`](../tests/conftest.py)).

## Seeding

The project includes a SQL seed file and a manual script so defaults are applied only when you run it.
The command resets the configured database (PostgreSQL tables), then inserts the default records.

1. Make sure Podman is installed and `.env` is configured.
2. Run:

```bash
./scripts/seed.sh
```

This runs inside the app container: resets the configured database, applies Alembic migrations (`upgrade head`), then inserts bundled SQL in order: `default_users.sql`, then `default_todos.sql` (under `src/todos_app/infrastructure/persistence/seeding/`).

Use `./scripts/seed.sh` when you want demo users and todos back immediately. To wipe schema and data without re-seeding, use [Wiping the database](#wiping-the-database) instead.

**Safety:** seeding is refused when `APP_ENV` is `staging` or `production`, or when `DATABASE_URL` points at a non-local host. See [Deployment — Security notes](deployment.md#security-notes-local-and-deployed).

## Wiping the database

To remove all Compose containers and named volumes (full local reset):

```bash
./scripts/wipe.sh
```

Pass `--yes` to skip the confirmation prompt (non-interactive).

**After wiping**, recreate schema and optionally load demo data:

```bash
./scripts/migrate.sh          # required — apply migrations
./scripts/seed.sh             # optional — reset + demo users/todos
```

**Wipe vs seed:** `./scripts/wipe.sh` removes containers and volumes (`compose down -v`). `./scripts/seed.sh` resets the database, re-applies migrations, and inserts bundled SQL demo data — use seed when you want a fresh DB ready to log in with sample users.

← [Project README](../README.md)
