# Authentication

Protected routes require an `Authorization: Bearer <access_token>` header. Obtain a token with `POST /auth/login` (username and password in the JSON body).

**Local setup:** copy [`src/env_config/profiles/example.py`](../src/env_config/profiles/example.py) to `src/env_config/profiles/local.py`, set `jwt_secret_key` to a long random string (for example `python -c "import secrets; print(secrets.token_urlsafe(64))"`), and `export ENV_PROFILE=local`. See [Configuration and secrets](architecture.md#configuration-and-secrets).

After [seeding](database.md#seeding), sample credentials are `jane` / `changeme` (regular user) and `admin` / `changeme` (admin). [api.http](api.http) shows login requests and authenticated calls.

For auth layer layout, protected endpoints, and authorization rules, see [Authentication (JWT login)](architecture.md#authentication-jwt-login).

## Admin users

Public signup (`POST /users`) always creates accounts with `role=user`. The signup schema does not include `role`; sending it returns **422**.

### Local development

Run [`./scripts/database/seed.sh`](database.md#seeding), then log in as **`admin` / `changeme`**. Seed SQL inserts that user directly (`default_users.sql`).

To promote another account without re-seeding:

1. Log in as the seeded admin.
2. `PATCH /users/{user_id}` with `"role": "admin"` (admin-only).

Integration tests use the same direct-insert pattern: `register_admin_and_login` in `tests/integration/api/helpers.py` adds a user with `role="admin"` via the repository, then logs in.

### Staging and production

Seeding is refused when `APP_ENV` is `staging` or `production` (see [Deployment — Security notes](deployment.md#security-notes-local-and-deployed)). There is no public admin signup endpoint.

Provision the **first** admin outside the API:

1. Insert a row into `users` with `role='admin'`, `is_active=true`, and an Argon2 password hash (same columns as `default_users.sql`).
2. Or register with `POST /users`, then set `role='admin'` on that row in the database.

After the first admin exists, log in and use `PATCH /users/{user_id}` with `"role": "admin"` to grant admin to other users. Do **not** run `./scripts/database/seed.sh` in deployed environments.

← [Project README](../README.md)
