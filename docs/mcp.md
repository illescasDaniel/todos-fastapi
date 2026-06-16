# MCP server (Cursor agent tools)

**On this page:** [What it is](#what-it-is) · [Python environments](#python-environments) · [Install](#install) · [Test in Cursor](#test-in-cursor) · [Tools](#tools) · [Configuration](#configuration) · [Troubleshooting](#troubleshooting)

The [Todos Backend MCP](../mcp/todos-backend/) is a **stdio MCP server** that lets Cursor agents call the HTTP API and run local dev scripts (start stack, migrate, seed, etc.) through typed tools instead of raw `curl` and shell commands.

Package path: [`mcp/todos-backend/`](../mcp/todos-backend/).

## What it is

```text
Cursor agent  →  MCP tools (stdio)  →  httpx  →  FastAPI (`todos_api_base_url` from env profile)
                              ↘  subprocess  →  ./scripts/*.sh
```

- **API tools** mirror the HTTP routes (`auth_login`, `todos_create`, `users_signup`, …).
- **Lifecycle tools** wrap existing repo scripts (`stack_compose_up`, `db_migrate`, `db_seed`, …).
- After `auth_login`, protected tools reuse the stored Bearer token unless you pass `access_token` explicitly.

See the full tool catalog in [`mcp/todos-backend/README.md`](../mcp/todos-backend/README.md).

## Python environments

The MCP server uses **its own virtual environment**, separate from everything else:

| Environment | Path | Used for |
|-------------|------|----------|
| **MCP server** | `mcp/todos-backend/.venv` | Running the MCP process (`mcp`, `httpx`) |
| **FastAPI app** | repo root `.venv` | `./scripts/start.sh`, pytest, Ruff on `todos_app` |

Cursor starts the MCP server with the interpreter configured in [`.cursor/mcp.json`](../.cursor/mcp.json) at the **repo root**:

```json
"command": "${workspaceFolder}/mcp/todos-backend/.venv/bin/python"
```

`${workspaceFolder}` resolves to the workspace root when you open the repo in Cursor. If interpolation does not work in your Cursor version, replace it with the absolute path to `mcp/todos-backend/.venv/bin/python`.

That means:

- **Nothing is installed into your global/system Python** when you follow the install steps below.
- The MCP server does **not** use the main API `.venv` for its own process.
- Lifecycle tools such as `stack_start_host` may **invoke** repo scripts that activate the **API** `.venv` internally — that is expected; the MCP process itself still runs from `mcp/todos-backend/.venv`.

## Install

One-time setup (from repo root):

```bash
cd mcp/todos-backend
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Prerequisites for the **API** and lifecycle tools (unchanged from normal dev):

- [`src/env_config/profiles/local.py`](../src/env_config/profiles/local.py) with secrets (`ENV_PROFILE=local` in [`.cursor/mcp.json`](../.cursor/mcp.json) or shell)
- **Podman** (or Docker) for compose lifecycle tools
- API reachable at `http://127.0.0.1:${API_PORT}` (`api_port` in env profile) when using API tools

## Test in Cursor

This is the fastest path — it matches what works in practice:

1. **Install** the MCP venv (see [Install](#install)) if you have not already.

2. **Open** the repo root in Cursor  
   (File → Open Folder → `.../todo`).

3. **Enable the server** in the **Agents** view (MCP panel):
   - Find **todos-backend**
   - Toggle it **on**  
   Cursor reads [`.cursor/mcp.json`](../.cursor/mcp.json) from the workspace root automatically.

4. **Start the API** (from the main repo root, in a terminal):
   ```bash
   ./scripts/start.sh
   ```
   Or ask the agent to run `stack_compose_up` once the MCP is enabled.

5. **Smoke test** in Agent chat — ask the agent to:
   - run `health_check`
   - run `auth_login` with `username=jane`, `password=changeme`
   - run `todos_list` with `limit=5`

You should see **todos-backend** tools listed when the server is connected.

### Other ways to attach

| Method | When |
|--------|------|
| **Repo root workspace** | Recommended; [`.cursor/mcp.json`](../.cursor/mcp.json) is committed and ready to use |
| **All projects** | Copy the `todos-backend` block into `~/.cursor/mcp.json` |

If `${workspaceFolder}` is unsupported, set `command` to the absolute path of `mcp/todos-backend/.venv/bin/python`. `TODOS_REPO_ROOT` is optional — when omitted, the server auto-detects the repo root from `config.py` (`parents[4]` from the installed package path).

### CLI (without Cursor)

```bash
cd mcp/todos-backend
.venv/bin/python -m todos_mcp
```

Runs the stdio server on its own; useful with the MCP inspector or debugging.

## Tools

### API tools (HTTP mirror)

| Tool | HTTP |
|------|------|
| `health_check` | `GET /health` |
| `auth_login` | `POST /auth/login` |
| `auth_clear_session` | Clears stored token |
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

Responses are JSON strings: `{"ok": true, "status": 200, "data": ...}` on success, or `{"ok": false, "status": ..., "detail": ...}` on API errors.

### Lifecycle tools

#### Read-only / safe

| Tool | Action |
|------|--------|
| `stack_health` | `curl` API `/health` |
| `open_api_docs` | Open `TODOS_API_BASE_URL/docs` in the default browser |
| `stack_start_host` | Background `./scripts/start.sh` (Path A) |
| `stack_stop_host` | Stop MCP-spawned host process only |
| `stack_compose_up` | `./scripts/container/up.sh` (Path B) |
| `stack_compose_down` | `./scripts/container/down.sh` (without `remove=true`) |
| `db_migrate` | `./scripts/database/migrate.sh` |

#### Destructive (require `MCP_ALLOW_DESTRUCTIVE=true`)

> **Warning:** These tools modify or destroy local data and are disabled by default.
> Set `MCP_ALLOW_DESTRUCTIVE=true` in the MCP server env to enable them.

| Tool | Action |
|------|--------|
| `db_seed` | `./scripts/database/seed.sh` — inserts demo data (needs `APP_ENV=local`) |
| `db_wipe` | `./scripts/database/wipe.sh --yes` — **destroys all local DB volumes** |
| `stack_compose_down` with `remove=true` | Removes compose volumes |

### Example agent prompts

- “Log in as jane and list my todos.”
- “Sign up `bob@example.com` / `bob`, log in, and create a high-priority todo.”
- “Start the compose stack, seed the DB, and open the API docs.”

## Configuration

| Variable | Required | Purpose |
|----------|----------|---------|
| `todos_api_base_url` | From env profile | API base URL (no trailing slash) |
| `ENV_PROFILE` | Yes (`local` in `.cursor/mcp.json`) | Loads [`src/env_config/profiles/<name>.py`](../src/env_config/) — any valid profile module name |
| `TODOS_REPO_ROOT` | Yes (e.g. `${workspaceFolder}` in `.cursor/mcp.json`) | Working directory for lifecycle scripts |
| `mcp_allow_destructive` | From env profile | Set `true` in `local.py` to enable destructive lifecycle tools |
| `mcp_allow_remote_api` | From env profile | Set `true` to allow non-loopback API targets |

Set in `.cursor/mcp.json` under `env`, or in the shell when running manually.

### Security defaults

- **Destructive tools are off by default.** `db_wipe`, `db_seed`, and `stack_compose_down --remove` return an error unless `mcp_allow_destructive=true` in the active env profile. For local dev, set it in your local profile module (e.g. `local.py`). Do **not** enable in CI.
- **SSRF guard is on by default.** `todos_api_base_url` is validated at startup; only loopback addresses are allowed unless `mcp_allow_remote_api=true`.
- **Subprocesses inherit a minimal environment.** Only variables needed by shell scripts are forwarded; secrets are not passed to child processes. Scripts load config from env profiles on disk.
- **Bearer token lifetime.** The session token is stored in process memory and cleared on shutdown via `atexit`. When passing `access_token` explicitly in tool arguments, note that the value appears in agent call logs — prefer `auth_login` once and let the session store handle it.

## OpenAPI snapshot

[`.cursor/openapi.snapshot.json`](../.cursor/openapi.snapshot.json) is a **gitignored** local reference for the HTTP surface (agents can `@`-reference it). Generated from `todos_app.main:app` — no running server required.

- **Automatic:** local `./scripts/quality/checks.sh` regenerates it before MCP tests (skipped when `CI=true`).
- **Manual:** `./scripts/mcp/export_openapi.sh`

## Tests

From `mcp/todos-backend/`:

```bash
.venv/bin/pytest -m "not integration"
.venv/bin/pytest -m integration   # requires running API
```

These tests are independent of the main repo coverage gate on `todos_app`.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| MCP server not listed | Open repo root as workspace; confirm `mcp/todos-backend/.venv` exists and `pip install -e .` succeeded |
| Tools fail with connection errors | Start API (`./scripts/start.sh` or `stack_compose_up`); run `stack_health` |
| `401` on protected tools | Run `auth_login` first, or pass `access_token` |
| Lifecycle tools fail | Repo root auto-detect or `TODOS_REPO_ROOT` correct; Podman installed; `src/env_config/profiles/local.py` present |
| `db_seed` fails | `app_env=local` in env profile (`ENV_PROFILE=local`) |

## Limitations

- `stack_start_host` tracks one background process; prefer `stack_compose_up` for reliable daemonized starts.
- `db_wipe` destroys local volumes — use with care.
- `verify_stack.sh` is not exposed as an MCP tool (too heavy for routine agent use).
