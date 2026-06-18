# JSON Schema export

Public HTTP request and response bodies are defined as **Pydantic models** under `src/todos_app/api/<feature>/schemas.py`. FastAPI already embeds those shapes in the live **OpenAPI** document (`/openapi.json` in local dev), but mobile apps, web frontends, and codegen tools often want **standalone JSON Schema** files they can vendor or feed into generators without pulling the full API spec.

This repo exports those models with `./scripts/export_json_schemas.sh`.

## What you get

Default output directory: [`schemas/json/`](../schemas/json/).

| File | Purpose |
|------|---------|
| `<ModelName>.schema.json` | One JSON Schema per public API model (e.g. `TodoCreate.schema.json`) |
| `index.json` | Manifest listing every model, its feature group, and filename |
| `bundle.schema.json` | Single document with all models under `$defs` (handy for all-in-one codegen) |

Schemas are generated from the same Pydantic types the API uses at runtime, so they stay aligned with validation rules (min/max length, required fields, `extra="forbid"`, examples, and so on).

### Covered models

| Group | Models |
|-------|--------|
| **auth** | `LoginRequest`, `TokenResponse` |
| **todos** | `TodoCreate`, `TodoUpdate`, `TodoPatch`, `TodoResponse`, `TodoListResponse` |
| **users** | `UserSignup`, `UserSelfReplace`, `UserSelfPatch`, `UserAdminReplace`, `UserAdminPatch`, `UserResponse` |

The canonical list lives in [`src/todos_app/api/schema_export/registry.py`](../src/todos_app/api/schema_export/registry.py). Add new public request/response models there when you introduce routes.

## Export

From the repo root with `.venv` active (see [Getting started](getting-started.md)):

```bash
./scripts/export_json_schemas.sh
```

Custom output path:

```bash
./scripts/export_json_schemas.sh /path/to/output
```

Serialization mode (output shapes instead of input validation):

```bash
PYTHONPATH=src .venv/bin/python -m todos_app.api.schema_export.export schemas/json --mode serialization
```

Re-run the export after changing any `api/*/schemas.py` model and commit the updated files under `schemas/json/` if you vendor them for clients.

## OpenAPI vs JSON Schema

| | OpenAPI (`/openapi.json`) | JSON Schema export |
|---|---------------------------|-------------------|
| **Scope** | Full HTTP API: paths, methods, status codes, security | Data shapes only |
| **Best for** | Interactive docs, API clients, integration tests | Mobile/web model codegen, shared validation libraries |
| **Local access** | Swagger UI at `/docs`, ReDoc at `/redoc` when `APP_ENV=local` | Static files in `schemas/json/` |
| **CI / agents** | `./scripts/mcp/export_openapi.sh` → `.cursor/openapi.snapshot.json` | `./scripts/export_json_schemas.sh` → `schemas/json/` |

Use **OpenAPI** when you need routes, auth, and try-it-out docs. Use **JSON Schema export** when another codebase only needs the request/response payloads.

See also [API reference](api.md) for route tables and live doc URLs.

## Client examples

**TypeScript (quicktype):**

```bash
npx quicktype --src schemas/json/TodoResponse.schema.json --lang ts --top-level TodoResponse -o TodoResponse.ts
```

**Dart / Flutter (json_serializable):** point your build_runner or a schema-to-Dart tool at individual `.schema.json` files or at `bundle.schema.json`.

**JSON Schema validators:** use the per-model files directly in Ajv, `@cfworker/json-schema`, or native mobile validators.

← [API reference](api.md) · [Project README](../README.md)
