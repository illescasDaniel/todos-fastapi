# API reference

Server at `http://localhost:${API_PORT}` (`api.port` in env profile).

`POST /auth/login` before protected routes — [Authentication](authentication.md).

`GET /todos`: cursor envelope (`items`, `next_last_id`, `limit`). Query `last_id` (omit first page; UUID v7 from prior page) and `limit` (default 20, max 100). Non-null `next_last_id` → pass as `last_id`. Regular users: own todos; admins: all.

IDs are **UUID v7** (`domain/ids.new_id()` on insert). After schema changes: `./scripts/database/migrate.sh` or `./scripts/database/seed.sh` for reset + demo data.

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **HTTP samples:** [api.http](api.http)

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
