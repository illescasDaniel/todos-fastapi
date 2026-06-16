# Deployment

**On this page:** [Environments](#environments) · [Image](#container-image) · [Local Compose](#local-podman-compose) · [Staging/production](#staging-and-production-path-c) · [Config reference](#configuration-reference)

Cloud-agnostic: one OCI image, same env vars everywhere. No cloud SDKs.

Local: **rootless Podman** — `./scripts/install_podman.sh`. [Install Podman](#install-podman).

See: [Getting started](getting-started.md) · [Database](database.md) · [Architecture](architecture.md)

## Environments

| Environment | Use | Database | Config |
|-------------|-----|----------|--------|
| **Local** | Dev machine | Postgres (Compose) | `ENV_PROFILE=local` + gitignored `local.toml`; Compose `.env` |
| **Staging** | Pre-prod | Managed Postgres | Platform secrets (same keys) |
| **Production** | Live | Managed Postgres | Platform secrets; unique `JWT_SECRET_KEY` |

`APP_ENV=local|staging|production` for logging/ops; behavior from `POSTGRES_URL`, `JWT_*`, etc.

## Container image

```bash
./scripts/container/build.sh
# podman build --format docker -t todos-api .
```

`--format docker` preserves Dockerfile `HEALTHCHECK`.

[Dockerfile](../Dockerfile): multi-stage — builder wheels app; runtime slim Python 3.14, non-root `app`, health on `/health`.

Standalone:

```bash
podman run --rm -p 8000:8000 \
  -e JWT_SECRET_KEY="your-secret" \
  -e POSTGRES_URL="postgresql+asyncpg://user:pass@db-host:5432/todos" \
  -e VALKEY_URL="valkey://valkey-host:6379/0" \
  todos-api
```

Migrations on start when `DEPLOY_RUN_MIGRATIONS=true` (default; `[deploy] run_migrations` in profile).

## Local Podman Compose

| Path | When | Compose files | App | DB / Valkey |
|------|------|---------------|-----|-------------|
| **A — Host** | Daily dev | `docker-compose.infra.yml` | Host `.venv` / `start.sh` | `127.0.0.1` |
| **B — Full stack** | Local smoke | infra + `app.base` + `app.with-infra` | Container | In-network `postgres`/`valkey` |
| **C — Production** | Staging/prod | `app.base` only | Container | External URLs |

Paths A/B: Valkey + Postgres on `COMPOSE_INFRA_BIND:*`. Path B rewrites loopback URLs inside app container.

**Prereqs A/B:** Podman, [`local.toml`](../config/profiles/local.toml) from [`example.toml`](../config/profiles/example.toml), strong `[jwt] secret_key` (≥32 chars), postgres/valkey URLs. `export ENV_PROFILE=local`.

### Path B commands

| Command | Action |
|---------|--------|
| `up.sh` | Full stack |
| `down.sh` | Stop (containers kept) |
| `down.sh --remove` | Remove containers; volumes kept |
| `wipe.sh` | Full volume reset |
| `seed.sh` | Demo data (local) |
| `migrate.sh` | Alembic |
| `logs.sh` | App logs |
| `build.sh` | App image |

Scripts need `postgres.url`. Path B overlay sets in-network URLs; loopback in `local.toml` correct for host.

### Install Podman

Arch/CachyOS:

```bash
./scripts/install_podman.sh
systemctl --user enable --now podman.socket
podman info --format '{{.Host.Security.Rootless}}'   # expect true
```

Rootless ports &lt;1024: may need `net.ipv4.ip_unprivileged_port_start=1024` in `/etc/sysctl.d/`.

### URLs (Paths A and B)

| Context | `POSTGRES_URL` | `VALKEY_URL` |
|---------|----------------|--------------|
| Host (A) | `@127.0.0.1:5432` | `@127.0.0.1:6379` |
| Container (B) | `@postgres:5432` | `@valkey:6379` |

Set in `local.toml`; Path B scripts rewrite for container.

API bind: `COMPOSE_APP_BIND:API_PORT`. Path A: `./scripts/start.sh`.

### Raw Compose

```bash
podman compose -f docker-compose.infra.yml up -d
podman compose -f docker-compose.infra.yml -f docker-compose.app.base.yml -f docker-compose.app.with-infra.yml up --build
```

## Staging and production (Path C)

### Migrations pre-deploy (recommended)

Default `DEPLOY_RUN_MIGRATIONS=true` runs Alembic on every start — OK single-replica; risky multi-replica rolling deploy.

Production: `run_migrations=false` in profile; migrate before rollout:

```bash
podman run --rm --env-file .env -e DEPLOY_RUN_MIGRATIONS=true todos-api true
./scripts/container/deploy.sh   # DEPLOY_RUN_MIGRATIONS=false
```

CI/CD:

```bash
podman run --rm \
  -e JWT_SECRET_KEY="$JWT_SECRET_KEY" \
  -e POSTGRES_URL="$POSTGRES_URL" \
  -e VALKEY_URL="$VALKEY_URL" \
  -e DEPLOY_RUN_MIGRATIONS=true \
  todos-api true
./scripts/container/deploy.sh
```

Same image; env differs:

1. **`JWT_SECRET_KEY`** — random ≥32 chars, unique per env; entrypoint rejects placeholders
2. **`POSTGRES_URL`** — managed Postgres (not loopback)
3. **`VALKEY_URL`** — managed Valkey (required)
4. **`APP_ENV`** — `staging` or `production`
5. **`DEPLOY_RUN_MIGRATIONS`** — `false` if separate migration job
6. **`JWT_EXPIRE_MINUTES`** — shorter in prod

### Path C — app-only Compose

[`production.example.toml`](../config/profiles/production.example.toml) → gitignored `production.toml` (not `example.toml`).

```bash
cp config/profiles/production.example.toml config/profiles/production.toml
export ENV_PROFILE=production
# Edit: app_env, jwt.secret_key, postgres.url, valkey.url (no loopback)
./scripts/container/build.sh
./scripts/container/deploy.sh
curl -sf http://localhost:8000/health
```

`deploy.sh` rejects `APP_ENV=local` and loopback URLs.

| Command | Action |
|---------|--------|
| `deploy.sh` | Start app (external URLs) |
| `down.sh --prod` | Stop |
| `down.sh --prod --remove` | Remove |
| `logs.sh --prod` | Logs |

### Standalone container

```bash
podman run -d --name todos-api -p 8000:8000 \
  -e APP_ENV=production \
  -e JWT_SECRET_KEY="$JWT_SECRET_KEY" \
  -e POSTGRES_URL="$POSTGRES_URL" \
  -e VALKEY_URL="$VALKEY_URL" \
  -e DEPLOY_RUN_MIGRATIONS=true \
  todos-api
```

Health: `GET /health` → `{"status":"ok"}`.

### Checklist

- [ ] Unique strong `JWT_SECRET_KEY` per env
- [ ] Managed Postgres (+ TLS if supported)
- [ ] Managed Valkey reachable
- [ ] Migrations applied
- [ ] First admin outside API — [Authentication — Admin users](authentication.md#admin-users)
- [ ] No `.env` baked in image
- [ ] DB not public unless required
- [ ] No `seed.sh` in staging/production

## Security notes

Internet-facing: TLS at reverse proxy; rate limiting + security headers — not in app container.

| Risk | Mitigation |
|------|------------|
| Weak DB passwords | Explicit `postgres_password`; Compose fails if missing |
| Prod seeding | `assert_seed_allowed()` blocks staging/prod + non-local hosts |
| Weak JWT | Entrypoint rejects placeholders, empty, &lt;32 chars |
| API on all interfaces | Default `COMPOSE_APP_BIND=127.0.0.1` |
| DB on LAN | Infra binds `127.0.0.1` only |

Never copy `local.toml` creds to staging/production. Start from `production.example.toml`.

## Configuration reference

| File | Use |
|------|-----|
| [`example.toml`](../config/profiles/example.toml) | Local template → any gitignored profile |
| [`production.example.toml`](../config/profiles/production.example.toml) | Staging/prod template → `production.toml` |
| [`test.toml`](../config/profiles/test.toml) | CI/pytest |

`ENV_PROFILE` merges stacked TOML; scripts export vars + root `.env` for Compose. [Configuration and secrets](architecture.md#configuration-and-secrets).

No cloud-specific variables.

← [Getting started](getting-started.md)
