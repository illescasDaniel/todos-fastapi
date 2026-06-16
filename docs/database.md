# Database

**On this page:** [PostgreSQL](#postgresql) · [Migrations](#database-migrations-alembic) · [Seeding](#seeding) · [Wipe](#wiping-the-database)

Setup: [Getting started](getting-started.md). Layers/DI: [Architecture](architecture.md).

## PostgreSQL

Async end-to-end: async routes/repos, SQLAlchemy + **asyncpg** via **`postgres.url`** (`POSTGRES_URL`).

| Setting | Notes |
|---------|-------|
| **`postgres.url`** | Required — e.g. `postgresql+asyncpg://todos:PASSWORD@127.0.0.1:5432/todos` in `local.toml` |
| **Local storage** | [`docker-compose.infra.yml`](../docker-compose.infra.yml) — Postgres 16 on `COMPOSE_INFRA_BIND:POSTGRES_PORT` |
| **Path B** | App container uses `@postgres:5432` (host URLs rewritten) |

Set `postgres.password`, `user`, `db`, `url` in [`local.toml`](../config/profiles/local.toml) before containers — scripts fail fast if missing. Local creds only; generate fresh per staging/production ([Deployment](deployment.md#local-podman-compose)).

- **Config:** `ENV_PROFILE=local` → `POSTGRES_URL`
- **Sessions:** `AsyncSession` per request via `Depends(get_db)`
- **Repos:** SQLAlchemy adapters — no dialect code in domain ports

**Local:** rootless Podman ([`install_podman.sh`](../scripts/install_podman.sh)), `local.toml`, `./scripts/database/migrate.sh`, optional `seed.sh`. Migrate/seed run in app container; same commands for host-app and full-stack.

## Database migrations (Alembic)

Revisions in `alembic/versions/`; `alembic/env.py` reads `postgres.url`, runs async (`asyncpg`).

| Command | Action |
|---------|--------|
| `./scripts/database/migrate.sh` | Ensure infra, `alembic upgrade head` in app container |
| `./scripts/database/migrate.sh revision -m "…"` | Autogenerate on host `.venv` |
| `./scripts/database/migrate.sh current` | Applied revision |
| `./scripts/database/migrate.sh history` | Revision list |

**Schema change loop:**

1. Edit `src/todos_app/infrastructure/persistence/<feature>/orm.py`
2. `./scripts/database/migrate.sh revision -m "…"`
3. Review `alembic/versions/` (always inspect autogenerate)
4. `./scripts/database/migrate.sh`
5. `./scripts/quality/tests.sh`

Raw (`.venv` + `PYTHONPATH=src`):

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic current
```

Tests: `upgrade head` on PostgreSQL test DB (`ENV_PROFILE=test`, `postgres.test_url` in [`test.toml`](../config/profiles/test.toml), [`conftest.py`](../tests/conftest.py)).

## Seeding

Resets DB, migrates, inserts bundled SQL.

1. `local.toml` + `export ENV_PROFILE=local` (Podman for bundled Postgres)
2. `./scripts/database/seed.sh`

Order: `default_users.sql`, `default_todos.sql` under `src/todos_app/infrastructure/persistence/seeding/`.

Use seed for demo data; [wipe](#wiping-the-database) for empty DB.

**Safety:** refused when `APP_ENV` is `staging`/`production` or `POSTGRES_URL` is non-local. [Deployment — Security notes](deployment.md#security-notes-local-and-deployed).

## Wiping the database

```bash
./scripts/database/wipe.sh          # compose down -v
./scripts/database/wipe.sh --yes    # non-interactive
```

Then:

```bash
./scripts/database/migrate.sh       # required
./scripts/database/seed.sh          # optional demo data
```

**Wipe** removes containers/volumes. **Seed** resets DB + migrations + demo SQL.

← [Project README](../README.md)
