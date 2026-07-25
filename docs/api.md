# API reference

Server at `http://localhost:${API_PORT}` (`api.port` in env profile).

`POST /auth/login` before protected routes — [Authentication](authentication.md).

`GET /todos`: cursor envelope (`items`, `next_last_id`, `limit`). Query `last_id` (omit first page; UUID v7 from prior page) and `limit` (default 20, max 100). Non-null `next_last_id` → pass as `last_id`. Regular users: own todos; admins: all.

IDs are **UUID v7** (`domain/ids.new_id()` on insert). After schema changes: `./scripts/database/migrate.sh` or `./scripts/database/seed.sh` for reset + demo data.

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs) — interactive OpenAPI explorer (try requests in the browser)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) (local only; hidden in staging/production)
- **HTTP samples:** [api.http](api.http)
- **JSON Schema export:** [json-schemas.md](json-schemas.md) — standalone model schemas for mobile/web clients (`./scripts/export_json_schemas.sh`)

## Idempotency

Optional `Idempotency-Key` header on `POST`, `PUT`, `PATCH`, and `DELETE` (except `POST /auth/login`). Omit the header for current behavior.

### Client rules

1. **One logical operation → one key.** Generate a fresh **UUID v7** when starting a create, update, or delete you may need to retry (network timeout, mobile backgrounding, etc.).
2. **Retries reuse the same key.** Send the identical header value with the same method, path, query string, and body as the original attempt.
3. **Never reuse a key for a different operation.** Same key + different body/path/method → `422`.
4. **`POST /users` (signup):** no JWT yet — scope is global (`anon`). Use a new UUID v7 per signup attempt; do not recycle keys across signups.

Generate a key (Python 3.14+):

```python
from uuid import uuid7

idempotency_key = str(uuid7())
```

Example — create todo with retry-safe key:

```http
POST /todos
Authorization: Bearer <access_token>
Idempotency-Key: 019e7000-0000-7000-8000-0000000000aa
Content-Type: application/json

{"title": "Buy milk", "completed": false}
```

If the first request times out after the server processed it, repeat the **same** request (same key, same JSON). The API returns the cached `201` and body instead of creating a second todo.

| Situation | Status | Meaning |
|-----------|--------|---------|
| First request with a key | normal | Handler runs; response cached (default TTL 24h) |
| Retry with same key + same body/path/method | replay | Stored status and body returned |
| Same key, different request fingerprint | `422` | Key reused for a different operation |
| Concurrent duplicate while first in flight | `409` | Wait and retry later |

**Scope:** authenticated routes key by JWT `sub` + header value; `POST /users` uses `anon` scope.

**Config:** `[idempotency]` in env profile (`enabled`, `ttl_seconds`, `max_key_length`). See [Architecture — cache](architecture.md#cache-here).

### `/auth`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Username/password → JWT |

### `/todos`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/todos` | List (auth; `last_id`, `limit`; users: own only) |
| `GET` | `/todos/{todo_id}` | One todo (owner or admin; `404` out of scope) |
| `POST` | `/todos` | Create (`201`; users: self; admins: optional `owner_id`) |
| `PUT` | `/todos/{todo_id}` | Replace (owner/admin; `403` if non-admin changes `owner_id`) |
| `PATCH` | `/todos/{todo_id}` | Partial update (same rules as `PUT`) |
| `DELETE` | `/todos/{todo_id}` | Delete (`204`; owner/admin) |

### `/users`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users` | Signup (`201`; always `role=user`) |
| `GET` | `/users/me` | Profile (`404` if missing) |
| `PUT` | `/users/me` | Replace profile (password optional) |
| `PATCH` | `/users/me` | Partial profile update |
| `PUT` | `/users/{user_id}` | Admin replace |
| `PATCH` | `/users/{user_id}` | Admin partial update |
| `DELETE` | `/users/{user_id}` | Admin deactivate (`204`; `?hard=true` purges todos) |

← [Project README](../README.md)
