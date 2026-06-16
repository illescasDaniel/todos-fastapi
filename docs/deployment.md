# Deployment

**On this page:** [Environments](#environments) · [Container image](#container-image) · [Local Podman Compose](#local-podman-compose) · [Staging and production](#staging-and-production) · [Configuration reference](#configuration-reference)

This project stays **cloud-agnostic**: one portable OCI image and the same environment variables everywhere. No AWS, GCP, or Azure SDKs — pick a host later and inject config from that platform's secret store.

Local development uses **rootless Podman** (same Compose file format as Docker Compose). Install with `./scripts/install_podman.sh` — see [Install Podman](#install-podman) below.

See also: [Getting started](getting-started.md) · [Database](database.md) · [Architecture](architecture.md)

## Environments

| Environment | Typical use | Database | How config is supplied |
|-------------|-------------|----------|------------------------|
| **Local** | Developer machine | PostgreSQL (Compose) | `ENV_PROFILE=local` + gitignored `src/env_config/profiles/local.py`; Compose uses generated `.env` |
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
| **C — Production** | Staging / production | `docker-compose.app.base.yml` only | App container | External managed URLs from production profile |

Paths A and B use local infra ([`docker-compose.infra.yml`](../docker-compose.infra.yml)): **Valkey** on `COMPOSE_INFRA_BIND:VALKEY_PORT` and **PostgreSQL** on `COMPOSE_INFRA_BIND:POSTGRES_PORT` (from env profile). Path B rewrites loopback `DATABASE_URL` / `VALKEY_URL` to in-network service names inside the app container.

**Prerequisites (Paths A and B):** rootless Podman (`./scripts/install_podman.sh`), [`src/env_config/profiles/local.py`](../src/env_config/profiles/local.py) (copy from [`example.py`](../src/env_config/profiles/example.py)) with a strong `jwt_secret_key` (at least 32 characters), postgres/valkey credentials, and explicit URLs. `export ENV_PROFILE=local`.

### Path B — local full stack commands

| Command | Action |
|---------|--------|
| `./scripts/container/up.sh` | Start full stack (infra + app) |
| `./scripts/container/down.sh` | Stop stack (fast; containers kept) |
| `./scripts/container/down.sh --remove` | Remove containers; named volumes kept |
| `./scripts/database/wipe.sh` | Remove local infra containers and all named volumes (full reset) |
| `./scripts/database/seed.sh` | Load demo users/todos (local only; via app container) |
| `./scripts/database/migrate.sh` | Apply Alembic migrations (via app container) |
| `./scripts/container/logs.sh` | Follow app logs |
| `./scripts/container/build.sh` | Build app image only |

The scripts require a PostgreSQL connection (`database_url` in env profile). For Path B, the app overlay sets in-network URLs; loopback values in `local.py` are correct for the host.

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
| Host app (Path A) | `postgresql+asyncpg://todos:PASSWORD@127.0.0.1:5432/todos` | `valkey://:PASSWORD@127.0.0.1:6379/0` |
| App container (Path B) | `postgresql+asyncpg://todos:PASSWORD@postgres:5432/todos` | `valkey://:PASSWORD@valkey:6379/0` |

Set URLs in [`src/env_config/profiles/local.py`](../src/env_config/profiles/local.py). Path B scripts rewrite loopback hosts for the app container.

The API binds to `COMPOSE_APP_BIND:API_PORT` from the env profile; override `compose_app_bind` only if you need LAN access.

**Path A — infra-only + host app:** use `./scripts/start.sh` with `ENV_PROFILE=local`.

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

For production, set `run_migrations=false` in your production profile and run migrations as a separate
one-shot step before rolling out the new image. Scripts export a generated `.env` for Compose; the same vars can be injected via orchestrator secrets instead:

```bash
# Run migrations before starting/updating the app container
podman run --rm \
  --env-file .env \
  -e RUN_MIGRATIONS=true \
  todos-api true   # exits after migrations; 'true' is a no-op CMD

# Then deploy the app without re-running migrations
./scripts/container/deploy.sh  # uses RUN_MIGRATIONS=false from exported profile
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

1. **`JWT_SECRET_KEY`** — cryptographically random (at least 32 characters), unique per environment; never reuse local dev secrets or template placeholders from [`production.example.py`](../src/env_config/profiles/production.example.py). The container entrypoint rejects empty, placeholder, and migration-only values.
2. **`DATABASE_URL`** — connection string to your managed PostgreSQL instance (not `127.0.0.1`).
3. **`VALKEY_URL`** — connection string to your managed Valkey/Redis instance (auth cache is required at runtime; not `127.0.0.1`).
4. **`APP_ENV`** — `staging` or `production`.
5. **`RUN_MIGRATIONS`** — `true` on deploy if this container should apply Alembic revisions (default); set `false` if migrations run in a separate job.
6. **`JWT_EXPIRE_MINUTES`** — consider shorter values in production.

### Path C — app-only Compose (primary)

Deploy the app container only — no bundled PostgreSQL or Valkey. Use [`production.example.py`](../src/env_config/profiles/production.example.py) as the template (copy to gitignored `production.py`, not [`example.py`](../src/env_config/profiles/example.py), which is for local development only).

#### Example: deploy from scratch

```bash
# 1. Copy the production env template
cp src/env_config/profiles/production.example.py src/env_config/profiles/production.py
export ENV_PROFILE=production

# 2. Edit production.py — set at minimum:
#    app_env=staging|production
#    jwt_secret_key   (generate: python -c "import secrets; print(secrets.token_urlsafe(64))")
#    database_url     (managed PostgreSQL — not 127.0.0.1)
#    valkey_url       (managed Valkey/Redis — not 127.0.0.1)

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

- [ ] Strong, unique `JWT_SECRET_KEY` per environment (not the template placeholder in [`production.example.py`](../src/env_config/profiles/production.example.py))
- [ ] Managed PostgreSQL with TLS if your provider supports it in the URL
- [ ] Managed Valkey/Redis reachable from the app (auth cache required)
- [ ] Migrations applied (`RUN_MIGRATIONS=true` or separate migration step)
- [ ] First admin provisioned outside the API (DB insert or signup + `role='admin'` update); further admins via `PATCH /users/{user_id}` — see [Authentication — Admin users](authentication.md#admin-users)
- [ ] No `.env` file baked into the image — inject secrets at runtime
- [ ] Restrict network access to the database (not public unless required)
- [ ] Do **not** run `./scripts/database/seed.sh` in staging or production (`APP_ENV` must be `local`)

## Security notes (local and deployed)

For internet-facing deployments, terminate **TLS** at a reverse proxy (nginx, Caddy, Traefik, or your cloud load balancer) and add **rate limiting** plus standard security headers. The app container does not provide these on its own.

| Risk | Mitigation |
|------|------------|
| Weak or shared database passwords | Env profile must set explicit `postgres_password`; Compose fails fast when missing |
| Seeding production data | `assert_seed_allowed()` blocks `APP_ENV=staging|production` and non-local `DATABASE_URL` hosts |
| Weak JWT at container start | `scripts/container/internal/entrypoint.sh` rejects placeholders, empty values, and keys shorter than 32 characters |
| API exposed on all interfaces | Default `COMPOSE_APP_BIND=127.0.0.1` limits the dev API to loopback |
| DB ports on LAN | `docker-compose.infra.yml` binds PostgreSQL and Valkey to `127.0.0.1` only |

**Never copy local [`local.py`](../src/env_config/profiles/local.py) credentials into staging or production.** Start from [`production.example.py`](../src/env_config/profiles/production.example.py) and generate fresh secrets per environment.

## Configuration reference

Environment templates:

| File | Use |
|------|-----|
| [`profiles/example.py`](../src/env_config/profiles/example.py) | Local development template → copy to any gitignored profile name (e.g. `local.py`, `local2.py`) |
| [`profiles/production.example.py`](../src/env_config/profiles/production.example.py) | Staging/production template → copy to gitignored `production.py` |
| [`profiles/test.py`](../src/env_config/profiles/test.py) | CI and pytest (`ENV_PROFILE=test`) |

All runtime config comes from env profiles loaded by `ENV_PROFILE` (any valid module name under `profiles/`). Shell scripts export vars and generate a root `.env` for Compose. See [Configuration and secrets](architecture.md#configuration-and-secrets) for profile naming rules and the full field list.

No cloud-provider-specific variables are used or required.

← [Getting started](getting-started.md)
