# Todos Backend MCP Server

stdio MCP server that exposes tools to call the FastAPI todos API and manage the local dev stack.

**Full guide:** [docs/mcp.md](../../docs/mcp.md)

## Quick start

### 1. Install (MCP-only venv)

Uses **`mcp/todos-backend/.venv`** — not the repo root `.venv`, not global Python.

```bash
cd mcp/todos-backend
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Test in Cursor

1. Open the **repo root** in Cursor (`.../todo`).
2. In the **Agents** view, find **todos-backend** and **enable** it.  
   Config: [`.cursor/mcp.json`](../../.cursor/mcp.json) (committed at repo root).
3. Start the API from repo root: `./scripts/start.sh` (or use `stack_compose_up` via the agent).
4. In Agent chat, try: `health_check` → `auth_login(username="jane", password="changeme")` → `todos_list(limit=5)`.

No manual JSON editing required when you open the repo root as the workspace.

### 3. Other attach options

- **All projects:** copy the `todos-backend` block from [`.cursor/mcp.json`](../../.cursor/mcp.json) into `~/.cursor/mcp.json`.

If `${workspaceFolder}` is unsupported, set `command` to the absolute path of `mcp/todos-backend/.venv/bin/python`. `TODOS_REPO_ROOT` is optional (auto-detected when omitted).

## Python environments

| Venv | Purpose |
|------|---------|
| `mcp/todos-backend/.venv` | MCP server (`mcp`, `httpx`) — what Cursor runs |
| repo root `.venv` | FastAPI app, pytest, `./scripts/start.sh` |

Cursor’s `command` points at `mcp/todos-backend/.venv/bin/python` (via `${workspaceFolder}` in the root [`.cursor/mcp.json`](../../.cursor/mcp.json)), so MCP dependencies stay isolated.

## Prerequisites

- Python **3.14+**
- Repo root [`.env`](../../.env) with `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL`
- **Podman** for compose lifecycle tools
- Running API at `http://127.0.0.1:8000` for API tools

## Tool catalog

### API (mirror HTTP routes)

| Tool | HTTP |
|------|------|
| `health_check` | `GET /health` |
| `auth_login` | `POST /auth/login` |
| `auth_clear_session` | (clears stored token) |
| `users_signup` | `POST /users` |
| `users_get_me` | `GET /users/me` |
| `users_replace_me` | `PUT /users/me` |
| `users_patch_me` | `PATCH /users/me` |
| `users_admin_replace` | `PUT /users/{user_id}` |
| `users_admin_patch` | `PATCH /users/{user_id}` |
| `users_admin_delete` | `DELETE /users/{user_id}` |
| `todos_list` | `GET /todos` |
| `todos_get` | `GET /todos/{todo_id}` |
| `todos_create` | `POST /todos` |
| `todos_replace` | `PUT /todos/{todo_id}` |
| `todos_patch` | `PATCH /todos/{todo_id}` |
| `todos_delete` | `DELETE /todos/{todo_id}` |

Protected tools accept optional `access_token`; otherwise they use the token from the last `auth_login`.

### Lifecycle / dev

| Tool | Action |
|------|--------|
| `stack_health` | `curl` API `/health` |
| `stack_start_host` | Background `./scripts/start.sh` (Path A) |
| `stack_stop_host` | Stop MCP-spawned host process |
| `stack_compose_up` | `./scripts/container/up.sh` (Path B) |
| `stack_compose_down` | `./scripts/container/down.sh` |
| `db_migrate` | `./scripts/migrate.sh` |
| `db_seed` | `./scripts/seed.sh` (needs `APP_ENV=local`) |
| `db_wipe` | `./scripts/wipe.sh --yes` (**destructive**) |

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `TODOS_API_BASE_URL` | `http://127.0.0.1:${API_PORT}` | API base URL (built from `API_HOST` + `API_PORT` when unset) |
| `API_PORT` | `8000` | Host API port |
| `TODOS_REPO_ROOT` | auto-detected repo root | Path for lifecycle scripts |

## Tests

```bash
.venv/bin/pytest -m "not integration"
.venv/bin/pytest -m integration   # requires running API
```

## OpenAPI snapshot

[`openapi.snapshot.json`](openapi.snapshot.json) — refresh per [docs/mcp.md](../../docs/mcp.md#openapi-snapshot).
