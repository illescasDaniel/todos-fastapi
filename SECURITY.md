# Security

This repository is a **demo / portfolio** FastAPI backend. It is not hardened for direct internet exposure without additional infrastructure.

## Scope

- Intended for local development, learning, and portfolio review.
- Demo seed users (`jane` / `changeme`, `admin` / `changeme`) are for **local use only** — never deploy seeded credentials to staging or production.
- OpenAPI UI (`/docs`, `/redoc`) is exposed only when `APP_ENV=local` (see `core/settings.py`).

## Reporting a vulnerability

If you discover a security issue in this project, please **do not** open a public GitHub issue with exploit details.

1. Contact the maintainer privately (replace with your preferred channel: email, GitHub security advisory, etc.).
2. Include steps to reproduce, affected versions, and impact if known.
3. Allow reasonable time for a fix before public disclosure.

## Pre-public / pre-deploy checklist

Before publishing the repo or deploying beyond localhost:

- [ ] **No production secrets in git** — secret profile modules under `src/env_config/profiles/` are gitignored (whitelist keeps only `example.py`, `production.example.py`, `test.py`); see `.gitignore`.
- [ ] **Fresh secrets per environment** — generate a strong `JWT_SECRET_KEY` (32+ characters); never reuse template placeholders from env profile examples.
- [ ] **Seed scripts local-only** — `./scripts/database/seed.sh` is blocked when `APP_ENV` is `staging` or `production` and for non-local database hosts.
- [ ] **Database not public** — managed PostgreSQL should not be reachable from the open internet unless your threat model requires it.
- [ ] **Internet-facing deployments** — place the API behind a **reverse proxy** with **TLS termination**, **rate limiting**, and security headers (HSTS, `X-Content-Type-Options`, etc.). The app container alone does not provide these.
- [ ] **Restrict bind address** — default Compose binds the API to `127.0.0.1`; widen only when intentional.
- [ ] **Rotate credentials** — database passwords and JWT signing keys are unique per environment.

See also [Deployment — Security notes](docs/deployment.md#security-notes-local-and-deployed) and [Authentication](docs/authentication.md).
