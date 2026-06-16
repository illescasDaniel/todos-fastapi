# Authentication

Protected routes need `Authorization: Bearer <access_token>`. Get a token via `POST /auth/login`.

**Local setup:** copy [`example.toml`](../config/profiles/example.toml) → `local.toml`, set `[jwt] secret_key` (`python -c "import secrets; print(secrets.token_urlsafe(64))"`), `export ENV_PROFILE=local`. See [Configuration and secrets](architecture.md#configuration-and-secrets).

After [seeding](database.md#seeding): `jane` / `changeme` (user), `admin` / `changeme` (admin). Samples in [api.http](api.http).

Layer layout, protected endpoints, rules: [Authentication (JWT login)](architecture.md#authentication-jwt-login).

## Admin users

`POST /users` always creates `role=user`. `role` in signup body → **422**.

### Local

[`./scripts/database/seed.sh`](database.md#seeding) → log in as **`admin` / `changeme`** (`default_users.sql`).

Promote without re-seed: log in as admin → `PATCH /users/{user_id}` with `"role": "admin"`.

Tests: `register_admin_and_login` in `tests/integration/api/helpers.py` inserts admin via repository.

### Staging and production

Seeding blocked when `APP_ENV` is `staging` or `production` ([Deployment — Security notes](deployment.md#security-notes-local-and-deployed)). No public admin signup.

First admin outside API:

1. Insert `users` row: `role='admin'`, `is_active=true`, Argon2 hash (see `default_users.sql`), or
2. `POST /users`, then `UPDATE` row to `role='admin'`

Then `PATCH /users/{user_id}` for more admins. Do **not** run `./scripts/database/seed.sh` in deployed envs.

← [Project README](../README.md)
