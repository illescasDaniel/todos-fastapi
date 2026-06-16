# Database

**On this page:** [PostgreSQL](#postgresql) · [Database migrations (Alembic)](#database-migrations-alembic) · [Seeding](#seeding) · [Wiping the database](#wiping-the-database)

For first-time setup (venv, env profile, migrate, seed), see [Getting started](getting-started.md).

For layer boundaries and DI patterns, see [Architecture](architecture.md).

## PostgreSQL

Persistence is **async end-to-end**: route handlers and repository ports are `async`, and SQLAlchemy uses **asyncpg** via `DATABASE_URL` (set in your env profile — see [`src/env_config/profiles/example.py`](../src/env_config/profiles/example.py)).

| Setting | Example / notes |
|---------|-----------------|
| **`DATABASE_URL`** | Required — e.g. `postgresql+asyncpg://todos:PASSWORD@127.0.0.1:5432/todos` in `profiles/local.py` |
| **Local storage** | [`docker-compose.infra.yml`](../docker-compose.infra.yml) — PostgreSQL 16 on `COMPOSE_INFRA_BIND:POSTGRES_PORT` (from env profile) |
| **Full-stack overlay** | App container uses `@postgres:5432` (rewritten from host profile URLs) |

Set `postgres_password`, `postgres_user`, `postgres_db`, and `database_url` in [`src/env_config/profiles/local.py`](../src/env_config/profiles/local.py) before starting database containers — Compose and scripts fail fast when required vars are missing. These values are for **local development only**; generate fresh credentials per staging or production environment (see [Deployment](deployment.md#local-podman-compose)).

- **Configuration:** env profile (`ENV_PROFILE=local`) supplies `DATABASE_URL` and PostgreSQL credentials
- **Sessions:** `AsyncSession` from `async_sessionmaker`, yielded per request via FastAPI `Depends(get_db)`
- **Repositories:** SQLAlchemy adapters — no dialect-specific code in domain ports

**Local setup:** [rootless Podman](../docs/deployment.md#install-podman) (`./scripts/install_podman.sh`), configure [`src/env_config/profiles/local.py`](../src/env_config/profiles/local.py), then `./scripts/database/migrate.sh` and optionally `./scripts/database/seed.sh`. Migrate and seed run inside the app container; the same commands work for host-app and full-stack workflows.

## Database migrations (Alembic)

Schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/). Migration scripts live under `alembic/versions/`; `alembic/env.py` reads `DATABASE_URL` from the same settings as the app and runs migrations with the async SQLAlchemy driver (`asyncpg`).

| Command | Action |
|---------|--------|
| `./scripts/database/migrate.sh` | Ensure Valkey + PostgreSQL infra, then apply pending revisions via the app container (`alembic upgrade head`) |
| `./scripts/database/migrate.sh revision -m "describe change"` | Autogenerate a revision on the host `.venv` (writes to `alembic/versions/`) |
| `./scripts/database/migrate.sh current` | Show the applied revision |
| `./scripts/database/migrate.sh history` | List revision history |

**Typical schema change loop:**

1. Edit ORM models under `src/todos_app/infrastructure/persistence/<feature>/orm.py`.
2. `./scripts/database/migrate.sh revision -m "describe change"`
3. Review the generated file in `alembic/versions/` (always inspect autogenerate output).
4. `./scripts/database/migrate.sh`
5. `./scripts/quality/tests.sh`

Equivalent raw commands (with `.venv` active and `PYTHONPATH=src`):

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic current
```

Automated tests bootstrap schema via Alembic `upgrade head` against a PostgreSQL test database (`ENV_PROFILE=test`, `test_database_url` in [`src/env_config/profiles/test.py`](../src/env_config/profiles/test.py); loaded in [`tests/conftest.py`](../tests/conftest.py)).

## Seeding

The project includes a SQL seed file and a manual script so defaults are applied only when you run it.
The command resets the configured database (PostgreSQL tables), then inserts the default records.

1. Configure [`src/env_config/profiles/local.py`](../src/env_config/profiles/local.py) and `export ENV_PROFILE=local` (Podman required for bundled PostgreSQL).
2. Run:

```bash
./scripts/database/seed.sh
```

This runs inside the app container: resets the configured database, applies Alembic migrations (`upgrade head`), then inserts bundled SQL in order: `default_users.sql`, then `default_todos.sql` (under `src/todos_app/infrastructure/persistence/seeding/`).

Use `./scripts/database/seed.sh` when you want demo users and todos back immediately. To wipe schema and data without re-seeding, use [Wiping the database](#wiping-the-database) instead.

**Safety:** seeding is refused when `APP_ENV` is `staging` or `production`, or when `DATABASE_URL` points at a non-local host. See [Deployment — Security notes](deployment.md#security-notes-local-and-deployed).

## Wiping the database

To remove all Compose containers and named volumes (full local reset):

```bash
./scripts/database/wipe.sh
```

Pass `--yes` to skip the confirmation prompt (non-interactive).

**After wiping**, recreate schema and optionally load demo data:

```bash
./scripts/database/migrate.sh          # required — apply migrations
./scripts/database/seed.sh             # optional — reset + demo users/todos
```

**Wipe vs seed:** `./scripts/database/wipe.sh` removes containers and volumes (`compose down -v`). `./scripts/database/seed.sh` resets the database, re-applies migrations, and inserts bundled SQL demo data — use seed when you want a fresh DB ready to log in with sample users.

← [Project README](../README.md)
