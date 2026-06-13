# Deployment

**On this page:** [Environments](#environments) · [Container image](#container-image) · [Local Podman Compose](#local-podman-compose) · [Staging and production](#staging-and-production) · [Configuration reference](#configuration-reference)

This project stays **cloud-agnostic**: one portable OCI image and the same environment variables everywhere. No AWS, GCP, or Azure SDKs — pick a host later and inject config from that platform's secret store.

Local development uses **rootless Podman** (same Compose file format as Docker Compose). Install with `./scripts/install_podman.sh` — see [Install Podman](#install-podman) below.

See also: [Getting started](getting-started.md) · [Database](database.md) · [Architecture](architecture.md)

## Environments

| Environment | Typical use | Database | How config is supplied |
|-------------|-------------|----------|------------------------|
| **Local** | Developer machine | PostgreSQL (Compose) | `.env` file, Podman Compose `env_file`, or shell exports |
| **Staging** | Pre-production testing | Managed PostgreSQL | Platform env vars / secrets (same keys as local) |
| **Production** | Live traffic | Managed PostgreSQL | Platform env vars / secrets; rotate `JWT_SECRET_KEY` per environment |

Set `APP_ENV=local|staging|production` as a label for logging and ops; behavior is driven by the other variables (`DATABASE_URL`, `JWT_*`, etc.).

## Container image

Build a production image from the project root with Podman:

```bash
./scripts/container/build.sh
# or: podman build --format docker -t todos-api .
```

Use `--format docker` so Podman preserves the Dockerfile `HEALTHCHECK` instruction (ignored in default OCI format).

The [Dockerfile](../Dockerfile) (OCI-compatible; built with `podman build`) uses a multi-stage build:

- **Builder** — wheels the app with core deps (`asyncpg`, `valkey`, etc.).
- **Runtime** — slim Python 3.14 image (stdlib `uuid7`), non-root `app` user, `HEALTHCHECK` on `/health`.

Run standalone (no Compose):

```bash
podman run --rm -p 8000:8000 \
  -e JWT_SECRET_KEY="your-secret" \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@db-host:5432/todos" \
  -e VALKEY_URL="valkey://valkey-host:6379/0" \
  todos-api
```

Point `DATABASE_URL` at your PostgreSQL host and ensure the network can reach it. Migrations run on container start when `RUN_MIGRATIONS=true` (default).

## Local Podman Compose

Three deployment paths share the same environment variables but use different Compose file sets:

| Path | When | Compose files | App runs | DB / Valkey |
|------|------|---------------|----------|-------------|
| **A — Host app** | Daily dev (hot reload) | [`docker-compose.infra.yml`](../docker-compose.infra.yml) only | Host `.venv` via `./scripts/start.sh` | Bundled on `127.0.0.1` |
| **B — Local full stack** | Prod-like local smoke | `docker-compose.infra.yml` + [`docker-compose.app.base.yml`](../docker-compose.app.base.yml) + [`docker-compose.app.with-infra.yml`](../docker-compose.app.with-infra.yml) | App container | Bundled; URLs rewritten to `postgres`/`valkey` |
| **C — Production** | Staging / production | `docker-compose.app.base.yml` only | App container | External managed URLs from `.env` |

Paths A and B use local infra ([`docker-compose.infra.yml`](../docker-compose.infra.yml)): **Valkey** on `COMPOSE_INFRA_BIND:VALKEY_PORT` (defaults `127.0.0.1:6379`) and **PostgreSQL** on `COMPOSE_INFRA_BIND:POSTGRES_PORT` (defaults `127.0.0.1:5432`). Host `.env` uses `127.0.0.1` for `DATABASE_URL` and `VALKEY_URL`; Path B rewrites `@127.0.0.1` / `valkey://127.0.0.1:…` to in-network service names inside the app container.

**Prerequisites (Paths A and B):** rootless Podman (`./scripts/install_podman.sh`), `.env` copied from [`.env.example`](../.env.example) with a strong `JWT_SECRET_KEY` (at least 32 characters, not the template placeholder) and `POSTGRES_PASSWORD` set.

### Path B — local full stack commands

| Command | Action |
|---------|--------|
| `./scripts/container/up.sh` | Start full stack (infra + app) |
| `./scripts/container/down.sh` | Stop stack (fast; containers kept) |
| `./scripts/container/down.sh --remove` | Remove containers; named volumes kept |
| `./scripts/wipe.sh` | Remove local infra containers and all named volumes (full reset) |
| `./scripts/seed.sh` | Load demo users/todos (local only; via app container) |
| `./scripts/migrate.sh` | Apply Alembic migrations (via app container) |
| `./scripts/container/logs.sh` | Follow app logs |
| `./scripts/container/build.sh` | Build app image only |

The scripts require a PostgreSQL `DATABASE_URL` (`postgresql+asyncpg://…`). For Path B, the app overlay sets in-network URLs; `127.0.0.1` in `.env` is correct.

### Install Podman

On Arch/CachyOS (rootless):

```bash
./scripts/install_podman.sh
# or: sudo pacman -S --needed podman podman-compose
systemctl --user enable --now podman.socket   # recommended
podman info --format '{{.Host.Security.Rootless}}'   # expect true
```

If binding to ports below 1024 fails as rootless, you may need `net.ipv4.ip_unprivileged_port_start=1024` via `/etc/sysctl.d/` (requires sudo).

### `DATABASE_URL`, `VALKEY_URL`, and host alignment (Paths A and B)

| Context | `DATABASE_URL` | `VALKEY_URL` |
|---------|----------------|--------------|
| Host app / `.env` (Path A) | `postgresql+asyncpg://todos:PASSWORD@127.0.0.1:${POSTGRES_PORT}/todos` | `valkey://127.0.0.1:${VALKEY_PORT}/0` |
| App container (Path B) | `postgresql+asyncpg://todos:PASSWORD@postgres:5432/todos` | `valkey://valkey:6379/0` |

Set `POSTGRES_PASSWORD` in `.env` before starting bundled PostgreSQL — Compose requires it and does not ship weak inline defaults. **Never reuse local dev database passwords in staging or production.**

The API binds to `COMPOSE_APP_BIND:API_PORT` by default (`127.0.0.1:8000`); override `COMPOSE_APP_BIND` only if you need LAN access.

**Path A — infra-only + host app:** use `./scripts/start.sh` with `DATABASE_URL` in `.env` — see [Getting started](getting-started.md).

### Compose (without the wrapper)

`./scripts/container/up.sh` uses Path B. To run Compose directly:

```bash
# Path A infra only — Valkey + PostgreSQL
podman compose -f docker-compose.infra.yml up -d

# Path B — infra + app
podman compose -f docker-compose.infra.yml -f docker-compose.app.base.yml -f docker-compose.app.with-infra.yml up --build
```

## Staging and production (Path C)

### Running migrations as a pre-deploy step (recommended for production)

By default, `RUN_MIGRATIONS=true` runs Alembic on every container start. This is safe for
single-replica deployments but can cause issues under multi-replica or zero-downtime rolling
deployments (concurrent migration attempts, table locks).

For production, set `RUN_MIGRATIONS=false` in `.env` and run migrations as a separate
one-shot step before rolling out the new image:

```bash
# Run migrations before starting/updating the app container
podman run --rm \
  --env-file .env \
  -e RUN_MIGRATIONS=true \
  todos-api true   # exits after migrations; 'true' is a no-op CMD

# Then deploy the app without re-running migrations
./scripts/container/deploy.sh  # uses RUN_MIGRATIONS=false from .env
```

Or in a CI/CD pipeline (e.g. GitHub Actions):

```bash
# Pre-deploy migration step
podman run --rm \
  -e JWT_SECRET_KEY="$JWT_SECRET_KEY" \
  -e DATABASE_URL="$DATABASE_URL" \
  -e VALKEY_URL="$VALKEY_URL" \
  -e RUN_MIGRATIONS=true \
  todos-api true

# Deploy step
./scripts/container/deploy.sh
```

Use the **same image** built from this repository. Differences are only env vars:

1. **`JWT_SECRET_KEY`** — cryptographically random (at least 32 characters), unique per environment; never reuse local dev secrets or template placeholders from [`.env.production.example`](../.env.production.example). The container entrypoint rejects empty, placeholder, and migration-only values.
2. **`DATABASE_URL`** — connection string to your managed PostgreSQL instance (not `127.0.0.1`).
3. **`VALKEY_URL`** — connection string to your managed Valkey/Redis instance (auth cache is required at runtime; not `127.0.0.1`).
4. **`APP_ENV`** — `staging` or `production`.
5. **`RUN_MIGRATIONS`** — `true` on deploy if this container should apply Alembic revisions (default); set `false` if migrations run in a separate job.
6. **`JWT_EXPIRE_MINUTES`** — consider shorter values in production.

### Path C — app-only Compose (primary)

Deploy the app container only — no bundled PostgreSQL or Valkey. Use [`.env.production.example`](../.env.production.example) as the template (not [`.env.example`](../.env.example), which is for local development only).

#### Example: deploy from scratch

```bash
# 1. Copy the production env template
cp .env.production.example .env

# 2. Edit .env — set at minimum:
#    APP_ENV=staging|production
#    JWT_SECRET_KEY   (generate: python -c "import secrets; print(secrets.token_urlsafe(64))")
#    DATABASE_URL     (managed PostgreSQL — not 127.0.0.1)
#    VALKEY_URL       (managed Valkey/Redis — not 127.0.0.1)

# 3. Build the image and start the app container
./scripts/container/build.sh
./scripts/container/deploy.sh

# 4. Verify health
curl -sf http://localhost:8000/health

# 5. Day-two operations
./scripts/container/logs.sh --prod          # follow logs
./scripts/container/down.sh --prod          # stop (container kept)
./scripts/container/down.sh --prod --remove # remove container
```

`deploy.sh` rejects `APP_ENV=local` and loopback `DATABASE_URL` / `VALKEY_URL` to prevent accidental local config in production.

| Command | Action |
|---------|--------|
| `./scripts/container/deploy.sh` | Start app container (external URLs required) |
| `./scripts/container/down.sh --prod` | Stop app container |
| `./scripts/container/down.sh --prod --remove` | Remove app container |
| `./scripts/container/logs.sh --prod` | Follow app logs |

`deploy.sh` preflight checks are listed above; see [Security notes](#security-notes-local-and-deployed) for the full production checklist.

### Alternative: standalone container (no Compose)

For orchestrators that inject env vars directly (Kubernetes, systemd, etc.):

```bash
podman run -d --name todos-api \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e JWT_SECRET_KEY="$JWT_SECRET_KEY" \
  -e DATABASE_URL="$DATABASE_URL" \
  -e VALKEY_URL="$VALKEY_URL" \
  -e RUN_MIGRATIONS=true \
  todos-api
```

Health check: `GET /health` returns `{"status":"ok"}` for load balancers and container orchestrators.

### Checklist

- [ ] Strong, unique `JWT_SECRET_KEY` per environment (not the template placeholder in `.env.production.example`)
- [ ] Managed PostgreSQL with TLS if your provider supports it in the URL
- [ ] Managed Valkey/Redis reachable from the app (auth cache required)
- [ ] Migrations applied (`RUN_MIGRATIONS=true` or separate migration step)
- [ ] First admin provisioned outside the API (DB insert or signup + `role='admin'` update); further admins via `PATCH /users/{user_id}` — see [Authentication — Admin users](authentication.md#admin-users)
- [ ] No `.env` file baked into the image — inject secrets at runtime
- [ ] Restrict network access to the database (not public unless required)
- [ ] Do **not** run `./scripts/seed.sh` in staging or production (`APP_ENV` must be `local`)

## Security notes (local and deployed)

For internet-facing deployments, terminate **TLS** at a reverse proxy (nginx, Caddy, Traefik, or your cloud load balancer) and add **rate limiting** plus standard security headers. The app container does not provide these on its own.

| Risk | Mitigation |
|------|------------|
| Weak or shared database passwords | `docker-compose.infra.yml` requires explicit `POSTGRES_PASSWORD` in `.env`; no weak fallbacks |
| Seeding production data | `assert_seed_allowed()` blocks `APP_ENV=staging|production` and non-local `DATABASE_URL` hosts |
| Weak JWT at container start | `scripts/container/entrypoint.sh` rejects placeholders, empty values, and keys shorter than 32 characters |
| API exposed on all interfaces | Default `COMPOSE_APP_BIND=127.0.0.1` limits the dev API to loopback |
| DB ports on LAN | `docker-compose.infra.yml` binds PostgreSQL and Valkey to `127.0.0.1` only |

**Never copy local `.env` or [`.env.example`](../.env.example) credentials into staging or production.** Start from [`.env.production.example`](../.env.production.example) and generate fresh secrets per environment.

## Configuration reference

Environment templates:

| File | Use |
|------|-----|
| [`.env.example`](../.env.example) | Local development (Paths A and B) |
| [`.env.production.example`](../.env.production.example) | Staging and production (Path C) |

All runtime config comes from environment variables (same keys in both templates):

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `JWT_SECRET_KEY` | Yes | — | HMAC key for access tokens (HS256 only; not configurable) |
| `DATABASE_URL` | No | Local PostgreSQL URL | `postgresql+asyncpg://…` |
| `APP_ENV` | No | `local` | Informational environment label |
| `JWT_EXPIRE_MINUTES` | No | `60` | |
| `VALKEY_URL` | No | `valkey://127.0.0.1:6379/0` | Valkey URL for auth user cache (required at runtime) |
| `AUTH_USER_CACHE_TTL_SECONDS` | No | `120` | Cached auth identity TTL |
| `RUN_MIGRATIONS` | No | `true` | Container entrypoint runs `alembic upgrade head` when true |
| `ENV_FILE` | No | `.env` | Optional path for pydantic-settings; omit when vars are injected directly |

No cloud-provider-specific variables are used or required.

← [Getting started](getting-started.md)
