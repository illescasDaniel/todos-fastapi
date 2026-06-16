# Getting started

**On this page:** [Setup](#setup-and-installation) · [Run server](#running-the-server) · [Path B compose](#podman-compose--path-b-local-full-stack)

**Default dev:** infra Compose ([`docker-compose.infra.yml`](../docker-compose.infra.yml)) + host app (`./scripts/start.sh`). [Deployment — Local Podman Compose](deployment.md#local-podman-compose).

Podman Compose for Valkey + Postgres on `127.0.0.1`. Same `migrate.sh` / `seed.sh` / `wipe.sh` for host-app and full-stack.

Use `.venv` — do not install globally.

## Setup and installation

**Python 3.14+** (stdlib `uuid.uuid7()`; matches [Dockerfile](../Dockerfile)).

### 1. Virtual environment

```bash
python3.14 -m venv .venv
```

No `python3.14`? Any 3.14 interpreter (`python3 --version`).

### 2. Activate

- **Linux / macOS:** `source .venv/bin/activate`
- **Windows CMD:** `.venv\Scripts\activate.bat`
- **Windows PowerShell:** `.venv\Scripts\Activate.ps1`

Prompt shows `(.venv)`.

### 3. Install

```bash
pip install -e .           # runtime
pip install -e ".[dev]"    # + Ruff, pytest
```

`-e` = editable; code changes without reinstall.

### 4. Reinstall after dep changes

```bash
chmod +x scripts/reinstall.sh   # once
./scripts/reinstall.sh          # pip install -e .
./scripts/reinstall.sh dev      # pip install -e ".[dev]"
```

Runtime deps:

| Package | Role |
|---------|------|
| `sqlalchemy` | Async ORM |
| `asyncpg` | Postgres driver |
| `greenlet` | SQLAlchemy sync bridges |
| `argon2-cffi` | Password hashing |
| `PyJWT` | JWT issue/verify |
| `valkey` | Auth cache (required; infra via compose) |

### 5. Working environment

Configure **before** API start — server does not create tables. Schema via Alembic ([Database](database.md#database-migrations-alembic)).

**Profile**

Copy [`example.toml`](../config/profiles/example.toml) → `local.toml`. Set:

- `[jwt] secret_key` — `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- `[postgres] password`, `user`, `db`, `url`
- `[valkey] password`, `url`
- Ports: `[api] port`, `[postgres] port`, `[valkey] port`, `[compose] infra_bind`, `app_bind`

```bash
export ENV_PROFILE=local
```

Tests/CI: `ENV_PROFILE=test` ([`test.toml`](../config/profiles/test.toml)). Extra profiles (`local2.toml`): [Configuration](architecture.md#profile-selection-env_profile).

**Migrate**

```bash
chmod +x scripts/database/migrate.sh   # once
./scripts/database/migrate.sh
```

Ensures infra, runs Alembic in app container → `users`, `todos`, `alembic_version`.

> Fresh DB: migrate before `./scripts/start.sh`. Full reset: `./scripts/database/wipe.sh` → migrate (optional seed).

**Seed (optional)**

```bash
./scripts/database/seed.sh
```

Demo: `jane`/`changeme`, `admin`/`changeme`. Seed runs migrate — can replace step 2. [Seeding](database.md#seeding). Admin account: [Authentication — Admin users](authentication.md#admin-users).

Empty DB: `wipe.sh` → `migrate.sh`. [Wipe](database.md#wiping-the-database).

**Start API** — [Running the server](#running-the-server).

| Step | Command |
|------|---------|
| Profile | `example.toml` → `local.toml`; secrets + URLs |
| Tables | `./scripts/database/migrate.sh` |
| Demo (opt) | `./scripts/database/seed.sh` |
| API | `./scripts/start.sh` |

## Running the server

`.venv` active; [environment](#5-working-environment) done (migrate on fresh DB).

### Option A: start script (recommended)

```bash
chmod +x scripts/start.sh   # once
./scripts/start.sh          # dev, hot reload
./scripts/start.sh pro      # production mode
```

| Script | Role |
|--------|------|
| `migrate.sh` | Infra + Alembic (autogenerate on host `.venv`) |
| `wipe.sh` | Remove containers + volumes |
| `seed.sh` | Reset + demo data |
| `start.sh` | Infra + host API |

Shared: `scripts/database/internal/setup.sh`, `ensure.sh`.

### Option B: FastAPI CLI

`ENV_PROFILE=local` + `PYTHONPATH=src`:

```bash
export ENV_PROFILE=local PYTHONPATH=src
fastapi dev --entrypoint todos_app.main:app --port "$API_PORT"   # reload
fastapi run --entrypoint todos_app.main:app --port "$API_PORT"   # prod
```

Unset `API_PORT`? `set -a && source .env && set +a` after `./scripts/database/migrate.sh` or any script that loads `ENV_PROFILE` via [`load_env.sh`](../scripts/internal/load_env.sh).

### Option C: main.py

```bash
python src/todos_app/main.py
```

No schema on startup — run [`migrate.sh`](database.md#database-migrations-alembic) first.

## Podman Compose — Path B (local full stack)

Infra + app container. Rootless Podman: `./scripts/install_podman.sh`. Paths A/B/C: [Deployment](deployment.md).

1. `example.toml` → `local.toml` (secrets)
2. `./scripts/container/up.sh`
3. Optional: `./scripts/database/seed.sh`

Path C: [`production.example.toml`](../config/profiles/production.example.toml) → `production.toml`, `ENV_PROFILE=production`, `./scripts/container/deploy.sh` — [Path C](deployment.md#path-c--app-only-compose-primary).

| Script | Action |
|--------|--------|
| `up.sh` | Start stack |
| `down.sh` | Stop (containers kept) |
| `down.sh --remove` | Remove containers/network; volumes kept |
| `wipe.sh` | Full volume reset |
| `seed.sh` | Demo data |
| `logs.sh` | Follow app logs |

Migrations on container start (`DEPLOY_RUN_MIGRATIONS=true`). Docs: `http://localhost:${API_PORT}/docs`.

Infra-only + host app: `./scripts/start.sh` — [Deployment](deployment.md#local-podman-compose).

## Architecture diagrams (optional)

Pre-committed SVGs in [`docs/images/`](images/). Regenerate: [Architecture — diagrams](architecture.md#architecture-diagrams). Needs Java 17+ and PlantUML (`pacman -S plantuml graphviz`, etc.) or `tools/plantuml.jar`.

← [Project README](../README.md)
