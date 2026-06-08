# Getting started

**On this page:** [Setup and installation](#setup-and-installation) · [Running the server](#running-the-server) · [Podman Compose full stack](#podman-compose-local-full-stack)

**Primary dev path:** infra-only Compose ([`docker-compose.infra.yml`](../docker-compose.infra.yml) — Valkey + PostgreSQL) + host app via `./scripts/start.sh`. See [Deployment — Local Podman Compose](deployment.md#local-podman-compose).

Local development uses Podman Compose for Valkey and PostgreSQL. The host app connects to both on `127.0.0.1`. The same `./scripts/migrate.sh`, `./scripts/seed.sh`, and `./scripts/wipe.sh` commands apply to host-app and full-stack workflows.

To keep your global Python environment clean, install all dependencies inside a virtual environment (`.venv`).

## Setup and installation

**Requires Python 3.14+** (stdlib `uuid.uuid7()` for primary keys; matches the [Dockerfile](../Dockerfile) used by Podman Compose).

### 1. Create a virtual environment

Navigate to the project root directory and run the following command to create a virtual environment named `.venv` (Python **3.14+**):

```bash
python3.14 -m venv .venv
```

If `python3.14` is not on your `PATH`, use any 3.14 interpreter (for example `python3 -m venv .venv` after confirming `python3 --version`).

### 2. Activate the virtual environment

Before installing dependencies or running the server, activate the virtual environment:

- **Linux / macOS:**
  ```bash
  source .venv/bin/activate
  ```
- **Windows (Command Prompt):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

_(You will see `(.venv)` prepended to your command line prompt, indicating the virtual environment is active)._

### 3. Install dependencies

With the virtual environment active, install the dependencies listed in `pyproject.toml` in editable mode:

- **For standard usage (FastAPI, asyncpg, and server dependencies):**
  ```bash
  pip install -e .
  ```
- **For development (includes Ruff, pytest, and pytest-asyncio):**
  ```bash
  pip install -e ".[dev]"
  ```

_Note: The `-e` (editable) flag allows you to make changes to the source code without needing to reinstall the package._

### 4. Reinstall the package

After you change dependencies in `pyproject.toml`, uninstall and reinstall the project in `.venv` with:

```bash
chmod +x scripts/reinstall.sh   # once, if needed
./scripts/reinstall.sh                    # pip install -e .
./scripts/reinstall.sh dev                # pip install -e ".[dev]"
```

The script activates `.venv`, removes `fastapi-todos`, then installs again in editable mode. Run it from the project root (same as the other `scripts/` utilities).

Runtime dependencies (from `pyproject.toml`):

| Package | Role |
|---------|------|
| `sqlalchemy` | Async ORM and query API (`AsyncSession`, `create_async_engine`) |
| `asyncpg` | Async PostgreSQL driver (`postgresql+asyncpg://…`) |
| `greenlet` | Required by SQLAlchemy for sync bridges (e.g. `run_sync` during schema creation) |
| `argon2-cffi` | Password hashing for user registration and login |
| `PyJWT` | Issue and verify JWT access tokens |
| `valkey` | Auth user cache (required at runtime; infra via `docker-compose.infra.yml`) |

### 5. Set up your working environment

After dependencies are installed, configure the app and prepare the database **before** starting the API. The server does not create tables on startup — schema is applied with Alembic (see [Database migrations (Alembic)](database.md#database-migrations-alembic)).

**1. Environment file**

Copy [`.env.example`](../.env.example) to `.env` in the project root and set at least:

- `JWT_SECRET_KEY` — required; generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- `POSTGRES_PASSWORD` — required for the Compose PostgreSQL service
- `DATABASE_URL` — `postgresql+asyncpg://todos:YOUR_POSTGRES_PASSWORD@127.0.0.1:5432/todos` (use the same password as `POSTGRES_PASSWORD`)
- `VALKEY_URL` — optional; defaults to `valkey://127.0.0.1:6379/0` (`./scripts/start.sh` ensures Valkey infra is running)
- `APP_ENV` — optional; `local` (default), `staging`, or `production`

**2. Create database tables**

Tables come from Alembic migrations, not from starting the server.

```bash
chmod +x scripts/migrate.sh   # once, if needed
./scripts/migrate.sh
```

`./scripts/migrate.sh` ensures Valkey and PostgreSQL are up, then runs Alembic inside the app container.

This runs `alembic upgrade head` and creates `users` and `todos` (and the `alembic_version` table).

> **Run order:** apply schema with `./scripts/migrate.sh` before `./scripts/start.sh` on a fresh database. Use `./scripts/wipe.sh` for a full volume reset (`compose down -v`), then migrate (and optionally seed) again.

**3. Optional: load demo data**

To reset the DB and insert sample users and todos (`jane` / `changeme`, `admin` / `changeme`):

```bash
./scripts/seed.sh
```

Seeding runs migrations after reset, so you can use it instead of step 2 when you want a fresh DB with demo records. See [Seeding](database.md#seeding) for details. Public `POST /users` signup always creates `role=user`; the seeded **`admin` / `changeme`** account is the local admin — see [Authentication — Admin users](authentication.md#admin-users).

To wipe schema and data without re-seeding (empty database), run `./scripts/wipe.sh` and then `./scripts/migrate.sh`. See [Wiping the database](database.md#wiping-the-database).

**4. Start the API**

```bash
chmod +x scripts/start.sh   # once, if needed
./scripts/start.sh
```

**Quick reference — fresh environment from zero:**

| Step | Command |
|------|---------|
| Configure `.env` | Copy `.env.example`, set `JWT_SECRET_KEY` and `POSTGRES_PASSWORD`, align `DATABASE_URL` |
| Create tables | `./scripts/migrate.sh` |
| Demo data (optional) | `./scripts/seed.sh` |
| Run API | `./scripts/start.sh` |

## Running the server

Make sure your virtual environment is active before starting the server.

### Option A: Using the start script

We provide a `scripts/start.sh` utility script. First, ensure it has execution permissions:

```bash
chmod +x scripts/start.sh
```

- **Development Mode** (Runs with hot-reloading enabled):
  ```bash
  ./scripts/start.sh
  ```
- **Production Mode**:
  ```bash
  ./scripts/start.sh pro
  ```

| Script | Role |
|--------|------|
| `scripts/migrate.sh` | Ensure Valkey + PostgreSQL infra; apply or inspect Alembic revisions via app container (`revision` autogenerate uses host `.venv`) |
| `scripts/wipe.sh` | Remove all Compose containers and named volumes (full reset) |
| `scripts/seed.sh` | Reset DB, migrate, load demo data (via app container) |
| `scripts/start.sh` | Ensure infra, run host API with hot reload |

All share `scripts/database/setup.sh` and `ensure.sh`. For a new machine or empty database, follow [Set up your working environment](#5-set-up-your-working-environment) first.

### Option B: Running the FastAPI CLI directly

You can also bypass the script and call the `fastapi` command line tool directly:

- **Development Mode** (auto-reload):
  ```bash
  fastapi dev src/todos_app/main.py --port 8000
  ```
- **Production Mode**:
  ```bash
  fastapi run src/todos_app/main.py --port 8000
  ```

### Option C: Running `main.py` directly

Since `main.py` is in the `src/` directory, you can launch it using python:

```bash
python src/todos_app/main.py
```

The API does **not** create or migrate schema on startup. Run [`./scripts/migrate.sh`](database.md#database-migrations-alembic) before `./scripts/start.sh` (see [PostgreSQL](database.md#postgresql)).

## Podman Compose — Path B (local full stack)

Prod-like local development: same infra as Path A plus an app container. Requires rootless Podman — run `./scripts/install_podman.sh`. See [Deployment](deployment.md) for all three paths (A/B/C) and production deploy.

**1. Configure `.env`**

Copy [`.env.example`](../.env.example) to `.env` and set `JWT_SECRET_KEY` and `POSTGRES_PASSWORD`. Set `DATABASE_URL` to PostgreSQL on `127.0.0.1`:

```
DATABASE_URL=postgresql+asyncpg://todos:YOUR_POSTGRES_PASSWORD@127.0.0.1:5432/todos
```

Path B rewrites the host to `postgres` inside the app container.

**2. Start the stack**

```bash
chmod +x scripts/container/*.sh   # once
./scripts/container/up.sh
```

**3. Optional: demo data**

```bash
./scripts/seed.sh
```

For **production deploy** (Path C), copy [`.env.production.example`](../.env.production.example) to `.env`, then use `./scripts/container/deploy.sh` — see [Deployment — Path C example](deployment.md#path-c--app-only-compose-primary).

### Container scripts (Path B)

| Script | Action |
|--------|--------|
| `./scripts/container/up.sh` | Start stack (`compose start` if stopped, else `up -d --build`) |
| `./scripts/container/down.sh` | Stop stack (containers kept) |
| `./scripts/container/down.sh --remove` | Remove containers and network; volumes kept |
| `./scripts/wipe.sh` | Remove local infra containers and named volumes (full reset) |
| `./scripts/seed.sh` | Reset DB and load demo users/todos (via app container) |
| `./scripts/container/logs.sh` | Follow app logs |

Migrations run automatically on container start (`RUN_MIGRATIONS=true`). Open [http://localhost:8000/docs](http://localhost:8000/docs).

**Infra-only + host app:** use `./scripts/start.sh` with the same `DATABASE_URL` — see [Deployment](deployment.md#local-podman-compose).

## Architecture diagrams (optional)

Rendered SVG diagrams are **pre-committed** under [`docs/images/`](images/) — you do not need PlantUML to run the API. To regenerate from sources, see [Architecture — Architecture diagrams](architecture.md#architecture-diagrams). Prerequisites: Java 17+ and PlantUML via your package manager (`pacman -S plantuml graphviz`, `apt install plantuml graphviz`, or `brew install plantuml graphviz`) or a local JAR at `tools/plantuml.jar`.

← [Project README](../README.md)
