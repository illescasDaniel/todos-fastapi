# Secrets management

**See also:** [Configuration and secrets](architecture.md#configuration-and-secrets) · [Deployment](deployment.md)

## Env profiles

Stacked TOML under [`config/`](../config/). Set `ENV_PROFILE` before scripts or app start:

```bash
export ENV_PROFILE=local       # merges config/profiles/local.toml
export ENV_PROFILE=local2      # custom local stack
export ENV_PROFILE=test        # CI / pytest (committed)
export ENV_PROFILE=production
```

Profile names: lowercase identifiers (`local`, `local2`, `my_staging`). Paths, dots, uppercase rejected. `example` is template only — copy it first.

Secret overlays are **gitignored**; committed: `example.toml`, `production.example.toml`, `test.toml`.

## Local development

Copy [`example.toml`](../config/profiles/example.toml) → gitignored `local.toml` (or `local2.toml` for a second stack). Set ports, URLs, secrets. Use `app_env = "local"` for OpenAPI UI and seed guards.

Shell scripts and Compose share a generated root [`.env`](../.env) from `python -m todos_app.core.config.export` (via [`load_env.sh`](../scripts/internal/load_env.sh)) — gitignored, do not hand-edit.

Production (Path C): gitignored [`production.toml`](../config/profiles/production.toml) from [`production.example.toml`](../config/profiles/production.example.toml). `export ENV_PROFILE=production` before `./scripts/container/deploy.sh`.

**Never pass secrets as `-e KEY=value`** on manual `podman run` — visible in `/proc/<pid>/cmdline`. Use:

- `--env-file .env` (generated from profile; do not commit)
- Compose `env_file:` (default in `docker-compose.app.base.yml`)
- Orchestrator injection (production)

## Production (Path C)

Prefer platform secrets over host `.env`:

- Podman secrets (`podman secret create`, `--secret` / Compose `secrets:`)
- Kubernetes Secrets
- Cloud stores (AWS/GCP/Azure)

If you must use host `.env`: `chmod 600`, deploy-user ownership, rotate on exposure.

## Secret variables

Do not log or print:

| Variable | Notes |
|----------|-------|
| `JWT_SECRET_KEY` | HMAC signing key — rotate per environment |
| `POSTGRES_URL` | Contains DB password |
| `VALKEY_URL` | Contains Valkey password |
| `POSTGRES_PASSWORD` | Bundled Postgres (local/Path B) |
| `VALKEY_PASSWORD` | Bundled Valkey (local/Path B) |

## Compose `env_file`

`docker-compose.app.base.yml` loads `.env` — fine for local dev. Production: inject only required vars via orchestrator; enumerate in `environment:`; never bake secrets into the image.

## Rotation

- Rotate `JWT_SECRET_KEY` on team churn or suspected breach — invalidates all sessions
- Unique random values per environment — never reuse local dev secrets in staging/production

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
