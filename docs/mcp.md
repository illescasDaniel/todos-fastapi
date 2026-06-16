# MCP server (Cursor agent tools)

**On this page:** [What it is](#what-it-is) · [Python envs](#python-environments) · [Install](#install) · [Test in Cursor](#test-in-cursor) · [Tools](#tools) · [Config](#configuration) · [Troubleshooting](#troubleshooting)

[Todos Backend MCP](../mcp/todos-backend/) — stdio MCP server for typed API + lifecycle tools instead of raw `curl`/shell.

Package: [`mcp/todos-backend/`](../mcp/todos-backend/).

## What it is

```text
Cursor agent  →  MCP tools (stdio)  →  httpx  →  FastAPI (MCP_API_BASE_URL)
                              ↘  subprocess  →  ./scripts/*.sh
```

- **API tools** mirror HTTP (`auth_login`, `todos_create`, …)
- **Lifecycle tools** wrap scripts (`stack_compose_up`, `db_migrate`, …)
- After `auth_login`, protected tools reuse Bearer token unless `access_token` passed

Catalog: [`mcp/todos-backend/README.md`](../mcp/todos-backend/README.md).

## Python environments

Separate venvs:

| Env | Path | For |
|-----|------|-----|
| MCP | `mcp/todos-backend/.venv` | MCP process |
| API | repo `.venv` | `start.sh`, pytest, Ruff |

Cursor starts MCP via [`.cursor/mcp.json`](../.cursor/mcp.json):

```json
"command": "${workspaceFolder}/mcp/todos-backend/.venv/bin/python"
```

Replace with absolute path if `${workspaceFolder}` fails.

- No global Python install
- MCP process uses MCP venv, not API venv
- Lifecycle tools may invoke scripts that activate API `.venv` — expected

## Install

```bash
cd mcp/todos-backend
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

API prerequisites: [`local.toml`](../config/profiles/local.toml), `ENV_PROFILE=local`, Podman, API at `http://127.0.0.1:${API_PORT}`.

## Test in Cursor

1. Install MCP venv
2. Open repo root in Cursor
3. Agents → **todos-backend** → on
4. Start API: `./scripts/start.sh` or agent runs `stack_compose_up`
5. Smoke: `health_check` → `auth_login` (jane/changeme) → `todos_list` limit=5

| Method | When |
|--------|------|
| Repo workspace | Recommended — committed `.cursor/mcp.json` |
| All projects | Copy block to `~/.cursor/mcp.json` |

No `${workspaceFolder}`: absolute python path + `TODOS_REPO_ROOT` ([Config](#configuration)).

### CLI (no Cursor)

```bash
cd mcp/todos-backend
.venv/bin/python -m todos_mcp
```

## Tools

### API (HTTP mirror)

| Tool | HTTP |
|------|------|
| `health_check` | `GET /health` |
| `auth_login` | `POST /auth/login` |
| `auth_clear_session` | Clear token |
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

JSON: `{"ok": true, "status": 200, "data": ...}` or `{"ok": false, "status": ..., "detail": ...}`.

### Lifecycle

**Safe**

| Tool | Action |
|------|--------|
| `stack_health` | curl `/health` |
| `open_api_docs` | Open docs in browser |
| `stack_start_host` | Background `start.sh` (Path A) |
| `stack_stop_host` | Stop MCP-spawned host only |
| `stack_compose_up` | `up.sh` (Path B) |
| `stack_compose_down` | `down.sh` (no `remove`) |
| `db_migrate` | `migrate.sh` |

**Destructive** (`MCP_ALLOW_DESTRUCTIVE=true`)

> **Warning:** Modifies/destroys local data. Disabled by default.

| Tool | Action |
|------|--------|
| `db_seed` | `seed.sh` (needs `APP_ENV=local`) |
| `db_wipe` | `wipe.sh --yes` — destroys DB volumes |
| `stack_compose_down` `remove=true` | Removes compose volumes |

### Example prompts

- “Log in as jane and list my todos.”
- “Sign up bob, log in, create high-priority todo.”
- “Compose up, seed, open API docs.”

## Configuration

| Variable | Required | Purpose |
|----------|----------|---------|
| `MCP_API_BASE_URL` | From profile | API base (no trailing slash) |
| `ENV_PROFILE` | Yes | Merges `profiles/<name>.toml` |
| `TODOS_REPO_ROOT` | Yes | CWD for lifecycle scripts |
| `MCP_ALLOW_DESTRUCTIVE` | Profile | `true` in `local.toml` for wipe/seed |
| `MCP_ALLOW_REMOTE_API` | Profile | `true` for non-loopback API |

Set in `.cursor/mcp.json` `env` or shell.

### Security defaults

- Destructive off unless `mcp.allow_destructive = true` in local profile. Not in CI.
- SSRF guard: loopback only unless `MCP_ALLOW_REMOTE_API=true`.
- Subprocesses get minimal env; scripts load profile from disk.
- Bearer token in memory; cleared on shutdown. Prefer `auth_login` over passing `access_token` in logs.

## OpenAPI snapshot

[`.cursor/openapi.snapshot.json`](../.cursor/openapi.snapshot.json) — gitignored local HTTP reference. From `todos_app.main:app`, no running server.

- Auto: `checks.sh` before MCP tests (skip `CI=true`)
- Manual: `./scripts/mcp/export_openapi.sh`

## Tests

```bash
cd mcp/todos-backend
.venv/bin/pytest -m "not integration"
.venv/bin/pytest -m integration   # needs running API
```

Outside main `todos_app` coverage gate.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Server not listed | Repo root workspace; MCP venv + `pip install -e .` |
| Connection errors | Start API; `stack_health` |
| `401` | `auth_login` or `access_token` |
| Lifecycle fails | `TODOS_REPO_ROOT`; Podman; `local.toml` |
| `db_seed` fails | `app_env=local` |

## Limitations

- `stack_start_host`: one background process — prefer `stack_compose_up`
- `db_wipe` destroys volumes
- `verify_stack.sh` not exposed (too heavy)
