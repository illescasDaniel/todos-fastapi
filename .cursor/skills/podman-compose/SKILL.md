---
name: podman-compose
description: Manage the local full-stack Podman Compose dev environment (Path B — up, down, wipe, seed, logs, build). Use when the user prefers containerized local development. For production deploy use deploy.sh (Path C).
disable-model-invocation: true
---

# Podman Compose (Path B — local full stack)

## When to use

Use this skill when the user wants **local full-stack** container development (bundled infra + app container) or a deployment-like local environment.

For **daily dev** (Path A — infra-only Compose + host app with hot reload), use `./scripts/start.sh` — see [docs/deployment.md](../../../docs/deployment.md#local-podman-compose).

For **production deploy** (Path C), use `./scripts/container/deploy.sh` with [`.env.production.example`](../../../.env.production.example) — see [docs/deployment.md](../../../docs/deployment.md#path-c--app-only-compose-primary).

## When NOT to use

- **pytest** — use the `run-tests` skill (tests use a PostgreSQL test database and `FakeUserAuthCache`, not Compose).
- **Alembic-only bare-metal workflow** — use the `alembic-migrate` skill (`./scripts/database/migrate.sh`).
- **Day-to-day unit test coding** — Path A (venv + `./scripts/start.sh`) is faster.
- **Production staging/production deploy** — use `./scripts/container/deploy.sh`, not this skill.

For bare-metal API dev (venv, `./scripts/database/migrate.sh`, `./scripts/start.sh`), see Path A in AGENTS.md **Local development paths**.

## Prerequisites

1. **Podman** installed (rootless). On Arch/CachyOS: `./scripts/install_podman.sh` or `sudo pacman -S --needed podman podman-compose`. See [docs/deployment.md](../../../docs/deployment.md#install-podman).
2. **`.env`** at the repo root with secrets only (`JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, `VALKEY_PASSWORD`). Ports in [`config/ports.env`](../../../config/ports.env); app derives `DATABASE_URL` / `VALKEY_URL` unless overridden in `.env`.
3. For **seed**: Podman and `.env` with `APP_ENV=local` (seed runs via app container).

## Compose layout (Path B)

| File | Purpose |
|------|---------|
| `docker-compose.infra.yml` | Infra: Valkey + PostgreSQL; ports on `127.0.0.1` |
| `docker-compose.app.base.yml` | App service base |
| `docker-compose.app.with-infra.yml` | Local overlay: `depends_on` bundled infra, URL rewrites via scripts |

Full-stack scripts use: `-f docker-compose.infra.yml -f docker-compose.app.base.yml -f docker-compose.app.with-infra.yml`.

## DATABASE_URL / VALKEY_URL (Path B)

Host `.env` uses `127.0.0.1`; app overlay rewrites to `postgres` / `valkey` inside the container. Do not put compose service hostnames in `.env` for Path B.

Set `POSTGRES_PASSWORD` in `.env` before starting — Compose requires it.

## Commands

Use `./.cursor/skills/podman-compose/scripts/run.sh` as the canonical wrapper:

| Subcommand | Delegates to | Notes |
|------------|--------------|-------|
| `up` | `./scripts/container/up.sh` | Start Path B stack; uses `compose start` if stopped containers exist, else `up -d --build`. Waits for `/health`. |
| `down` | `./scripts/container/down.sh` | Default: `compose stop` (containers kept). Pass `--remove` for `compose down` (containers and network removed; **named volumes kept**). |
| `wipe` | `./scripts/database/wipe.sh` | `down -v` across local infra + app. Requires confirmation unless `--yes` is passed. |
| `seed` | `./scripts/database/seed.sh` | Reset + migrate + SQL seed via app container (demo users `jane` / `admin`, password `changeme`). |
| `logs` | `./scripts/container/logs.sh` | `compose logs -f app`. |
| `build` | `./scripts/container/build.sh` | `podman build --format docker -t todos-api` (optional image name as second arg). |

Examples:

```bash
./.cursor/skills/podman-compose/scripts/run.sh up
./.cursor/skills/podman-compose/scripts/run.sh down
./.cursor/skills/podman-compose/scripts/run.sh down --remove
./.cursor/skills/podman-compose/scripts/run.sh wipe --yes
./.cursor/skills/podman-compose/scripts/run.sh seed
./.cursor/skills/podman-compose/scripts/run.sh logs
./.cursor/skills/podman-compose/scripts/run.sh build
```

Migrations run on container start when `RUN_MIGRATIONS=true` (default). After `wipe`, run `./scripts/database/migrate.sh` (and optionally `./scripts/database/seed.sh` or `up`).

## Constraints

- Use `./.cursor/skills/podman-compose/scripts/run.sh` as the canonical wrapper.
- Do not run Compose seed/wipe against staging or production (`APP_ENV` guards apply).
- Do not mix Compose service hostnames with bare-metal `127.0.0.1` workflows in the same session without understanding the overlay rewrite behavior.
- See [docs/deployment.md](../../../docs/deployment.md) for Path C production deploy.
