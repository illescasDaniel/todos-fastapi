# Secrets management

This document describes the recommended approach for managing secrets in this project.

## Local development

For local development (Path A and B), secrets are stored in `.env` (copied from `.env.example`).
Ports and bind addresses live in committed [`config/ports.env`](../config/ports.env) (override locally via gitignored `config/ports.local.env`).
`.env` is listed in `.gitignore` and must never be committed.

**Never pass raw secret values as `-e KEY=value` CLI arguments** when running containers manually.
These values are visible to any process that can read `/proc/<pid>/cmdline` on the host.

Instead, use one of:

- `--env-file .env` (podman/docker) — loads the file without exposing values in the process list
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

`docker-compose.app.base.yml` uses `env_file: - .env` to load the entire environment file.
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
