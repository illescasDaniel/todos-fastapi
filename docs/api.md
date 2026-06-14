# API reference

Once the server is running (`http://localhost:${API_PORT}` — `API_PORT` from [`config/ports.env`](../config/ports.env)), you can access the following resources.

Obtain a JWT access token via `POST /auth/login` before calling protected routes — see [Authentication](authentication.md).

`GET /todos` returns a cursor-paginated envelope (`items`, `next_last_id`, `limit`). Use query parameters `last_id` (omit for the first page; UUID v7 from the previous page) and `limit` (default `20`, maximum `100`). When `next_last_id` is non-null, pass it as `last_id` to fetch the next page. Regular users see only their own todos; admins see all.

User and todo primary keys are **UUID v7** (time-ordered, generated in repository `add()` via `domain/ids.new_id()`). After schema changes, run `./scripts/database/migrate.sh` (or `./scripts/database/seed.sh` for a full reset with demo data).

- **Interactive API Docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative API Docs (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **HTTP Request Samples:** [api.http](api.http) (VS Code REST Client, IntelliJ HTTP Client, etc.)

Current routes (prefix `/auth`):

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/login` | Exchange username/password for a JWT access token |

Current routes (prefix `/todos`):

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/todos` | List todos (authenticated; cursor pagination: `last_id`, `limit`; default limit 20, max 100; regular users see own todos only) |
| `GET` | `/todos/{todo_id}` | Get one todo by UUID (authenticated; owner or admin; `404` if missing or not in your scope) |
| `POST` | `/todos` | Create a todo (`201 Created`; authenticated; regular users create for self, admins may set `owner_id`) |
| `PUT` | `/todos/{todo_id}` | Replace a todo (owner or admin; `404` if missing or not in scope; non-admins get `403` when changing `owner_id`) |
| `PATCH` | `/todos/{todo_id}` | Partially update a todo (same rules as `PUT`) |
| `DELETE` | `/todos/{todo_id}` | Delete a todo (`204 No Content`; owner or admin; `404` if missing or not in scope) |

Current routes (prefix `/users`):

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users` | Create a user (`201 Created`; public; always `role=user`) |
| `GET` | `/users/me` | Get the authenticated user's profile (`404` if missing) |
| `PUT` | `/users/me` | Replace your profile (`404` if missing; password optional) |
| `PATCH` | `/users/me` | Partially update your profile |
| `PUT` | `/users/{user_id}` | Replace any user (admin only; `404` if missing; password optional) |
| `PATCH` | `/users/{user_id}` | Partially update any user (admin only) |
| `DELETE` | `/users/{user_id}` | Deactivate a user (admin only; `204`; soft by default, `?hard=true` to purge with their todos) |

← [Project README](../README.md)
