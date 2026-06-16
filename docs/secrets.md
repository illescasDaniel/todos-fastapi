# Secrets management

This document describes the recommended approach for managing secrets in this project.

## Env profiles

Configuration lives in Python modules under [`src/env_config/profiles/`](../src/env_config/profiles/). Set `ENV_PROFILE` to the module name (without `.py`) before running scripts or starting the app:

```bash
export ENV_PROFILE=local    # loads profiles/local.py
export ENV_PROFILE=local2   # loads profiles/local2.py (custom local stack)
export ENV_PROFILE=test     # CI / pytest (committed)
export ENV_PROFILE=production
```

Profile names must be lowercase identifiers (`local`, `local2`, `my_staging`). Invalid names (paths, dots, uppercase) are rejected. The template module `example` cannot be used as `ENV_PROFILE` — copy it to a new file first.

Secret-bearing profile files are **gitignored** automatically; only `example.py`, `production.example.py`, and `test.py` are committed. See [Configuration and secrets](architecture.md#configuration-and-secrets).

## Local development

For local development (Path A and B), create a gitignored profile from [`example.py`](../src/env_config/profiles/example.py) (commonly `local.py`). Ports, bind addresses, and connection URLs are set in the same module. Use `app_env="local"` for local behavior (OpenAPI UI, seed allowed).

For a **second local stack** (different ports/DB), copy the template to another name (e.g. `local2.py`) and `export ENV_PROFILE=local2`.

Shell scripts load the active profile and export uppercase env vars. For Compose, they also write a generated root [`.env`](../.env) via `env_config.export --dotenv` — gitignored, not hand-edited.

For production (Path C), secrets live in gitignored [`profiles/production.py`](../src/env_config/profiles/production.py) (copy from [`production.example.py`](../src/env_config/profiles/production.example.py)). Set `export ENV_PROFILE=production` before `./scripts/container/deploy.sh`.

**Never pass raw secret values as `-e KEY=value` CLI arguments** when running containers manually.
These values are visible to any process that can read `/proc/<pid>/cmdline` on the host.

Instead, use one of:

- `--env-file .env` (podman/docker) — generated from env profile; do not commit
- The `env_file:` key in Compose files (already the default in `docker-compose.app.base.yml`)
- Orchestrator-level injection (see Production below)

## Production (Path C)

For production deployments, **do not** rely on a `.env` file on the host if your platform
supports a secrets manager. Prefer:

- **Podman secrets** (`podman secret create`, `--secret` flag or `secrets:` in Compose)
- **Kubernetes Secrets** (mounted as env vars or volume files)
- **Cloud provider secret stores** (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, etc.)

If you must use a `.env` file on the host:

1. Set restrictive permissions: `chmod 600 .env`
2. Own it by the deploy user, not root
3. Rotate secrets after any suspected exposure

## Variables that are secrets

The following variables contain sensitive values and must not be logged, printed, or exposed:

| Variable | Notes |
|----------|-------|
| `JWT_SECRET_KEY` | HMAC signing key for access tokens — rotate per environment |
| `DATABASE_URL` | Contains database password |
| `VALKEY_URL` | Contains Valkey/Redis password |
| `POSTGRES_PASSWORD` | Bundled PostgreSQL password (local/Path B only) |
| `VALKEY_PASSWORD` | Bundled Valkey password (local/Path B only) |

## Compose env_file note

`docker-compose.app.base.yml` uses `env_file: - .env` to load the generated environment file.
This is convenient for local development but loads all variables including secrets into the
container environment. For production deployments:

- Prefer injecting only the required variables listed above via your orchestrator's secrets mechanism
- Use `environment:` in the Compose file to enumerate only the variables the app actually needs
- Never bake secrets into the image at build time

## Rotation

- Rotate `JWT_SECRET_KEY` whenever a team member leaves or a breach is suspected
- Rotating `JWT_SECRET_KEY` immediately invalidates all active sessions (users must log in again)
- Use unique, randomly generated values per environment — never reuse local dev secrets in staging or production

Generate a new secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
