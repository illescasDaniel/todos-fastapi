# Architecture

This document describes the layered architecture used by the ToDo API. Read it before making structural or feature changes.

**See also:** [Getting started](getting-started.md) · [Database](database.md) · [Authentication](authentication.md) · [API reference](api.md) · [Development](development.md)

## Overview

The application follows a **ports-and-adapters** (hexagonal / clean architecture) style:

- **Domain** holds business meaning — no FastAPI, no SQLAlchemy.
- **Application** orchestrates use cases — coordinates domain rules and ports; no FastAPI or Pydantic.
- **Infrastructure** implements domain ports against external systems (databases, APIs, queues, and similar).
- **API** exposes HTTP endpoints and Pydantic schemas at the outer edge.
- **Core** holds cross-cutting wiring (logging, FastAPI `Depends` providers, exception translation).

Dependencies point **inward**: outer layers depend on inner abstractions, never the reverse.

### Architecture diagrams

Layer and module diagrams are **PlantUML + C4** sources under [`docs/diagram/`](diagram/). Rendered SVGs live in [`docs/images/`](images/).

**Prerequisites:** Java 17+ and either the `plantuml` CLI (`pacman -S plantuml graphviz`, `apt install plantuml graphviz`, or `brew install plantuml graphviz`) or a local JAR at [`tools/plantuml.jar`](../tools/plantuml.jar) (download from [PlantUML releases](https://github.com/plantuml/plantuml/releases)). Graphviz improves layout when installed; without it the render script uses PlantUML’s built-in Smetana engine. Rendered SVGs are pre-committed — regeneration is optional.

**Regenerate:**

```bash
chmod +x scripts/render_diagrams.sh   # once
./scripts/render_diagrams.sh
```

Commit both updated `.puml` sources and generated `.svg` files when diagrams change.

### Layer flow

The center is **domain + ports** (hexagon); use cases orchestrate from **application**; **HTTP / api** is the primary (driving) adapter on top. The **domain & outbound adapters** band groups the hexagon with its driven-side adapters — persistence and auth / JWT implement domain ports; they are not the next step after domain in the call chain. **Core** is cross-cutting composition: FastAPI `Depends`, auth extraction, and exception-to-HTTP mapping.

![Layer containers](images/layer_containers.svg)

Source: [`docs/diagram/layer_containers.puml`](diagram/layer_containers.puml)

![Todo stack module dependencies](images/todo_stack_components.svg)

Source: [`docs/diagram/todo_stack_components.puml`](diagram/todo_stack_components.puml)

## Three kinds of model

Do not merge these into a single `models.py`:

| Kind | Location | Purpose | Example |
|------|----------|---------|---------|
| **API schema** | `api/<feature>/schemas.py` | HTTP request/response contract | `TodoCreate`, `TodoResponse` |
| **Domain entity** | `domain/<feature>/entity.py` | Business data, framework-free | `Todo` dataclass |
| **ORM model** | `infrastructure/persistence/<feature>/orm.py` | Database table mapping | `TodoModel` |

Mapping happens at boundaries:

- **ORM ↔ domain:** `infrastructure/persistence/<feature>/mapper.py`
- **Domain ↔ API:** router (or a small `api/<feature>/mappers.py` when routes grow)

### Identifiers (UUID v7)

User and todo primary keys are **`uuid.UUID`** values generated with **`uuid.uuid7()`** (Python 3.14+). Shared helpers and stable seed constants live in [`domain/ids.py`](../src/todos_app/domain/ids.py):

- `new_id()` — call from repository `add()` when `entity.id is None`
- `JANE_USER_ID`, `ADMIN_USER_ID`, `SEED_TODO_IDS` — fixed literals for seed SQL, `docs/api.http`, and docs

Keyset pagination uses `ORDER BY id` and `WHERE id > last_id`; v7 ordering keeps cursors efficient. JWT `sub` stores `str(user_id)`; the verifier parses it back to `UUID`.

## Repository ports and adapters

Domain defines **ports** as `typing.Protocol` — structural interfaces with no implementation:

```python
# domain/todos/repository.py
class TodoRepository(Protocol):
    async def list_page(
        self, last_id: UUID | None, limit: int, *, owner_id: UUID | None = None
    ) -> TodoPage: ...
    async def get_by_id(self, todo_id: UUID, *, owner_id: UUID | None = None) -> Todo | None: ...
    async def update(self, todo: Todo, *, owner_id: UUID | None = None) -> Todo | None: ...
    async def delete(self, todo_id: UUID, *, owner_id: UUID | None = None) -> bool: ...
    # ...
```

**Actor scope (`owner_id`):** Several todo port methods accept an optional `owner_id`. When set (regular users: the actor’s user id from `list_owner_filter`), adapters restrict SQL to rows owned by that user. When `None` (admins), no owner predicate is applied. Routes pass `list_owner_filter(actor_id=..., actor_role=...)` from `domain/auth/authorization.py`—the repository does not read JWTs or roles. Apply the same filter on **reads and writes** (`get_by_id`, `list_page`, `update`, `delete`) so authorization is enforced at query time, not only on an earlier `SELECT`.

Infrastructure provides **adapters** that satisfy the port:

```python
# infrastructure/persistence/todos/repository.py
class SqlAlchemyTodoRepository:
    def __init__(self, db: AsyncSession) -> None: ...
    async def list_page(
        self, last_id: UUID | None, limit: int, *, owner_id: UUID | None = None
    ) -> TodoPage: ...
    # ...
```

Routes and use cases depend on `TodoRepository` (the port), not on `SqlAlchemyTodoRepository`.

## The application layer

`application/` sits between `api/` and `domain/`. It holds **framework-free use cases** — functions that orchestrate domain rules and repository ports, return domain entities, and raise application or domain exceptions on failure.

| Piece | Responsibility |
|-------|----------------|
| **`application/auth.py`** | Login orchestration: credential lookup, password verify, token issuance |
| **`application/errors.py`** | `UserNotFoundError`, `TodoNotFoundError`, `TodoOwnerChangeForbiddenError`, `InvalidCredentialsError` |
| **`application/users.py`** | Create, load, update, deactivate, and hard-delete users |
| **`application/todos.py`** | Actor-scoped get, update, and delete todos |

Use cases receive ports as function arguments (for example `repo: UserRepository`). They do **not** import FastAPI, Pydantic schemas, or `api/*`. HTTP status codes and error detail strings live in `core/http_errors.py`; [`core/exceptions.py`](../src/todos_app/core/exceptions.py) maps application and domain exceptions to HTTP responses.

Routers stay thin: parse the request with Pydantic, build merge callables or entities via `api/<feature>/mappers.py`, call the use case, map the returned entity to a response schema.

## The infrastructure layer

`infrastructure/` holds **adapters** — code that talks to the outside world on behalf of the domain. The domain defines *what* it needs (`Protocol` ports); infrastructure provides *how*.

Organize by **kind of external system**, not by feature. Feature-specific code still gets its own subfolder inside each kind (mirroring `domain/<feature>/`).

### What belongs under `infrastructure/`

| Subpackage | When to add it | Examples |
|------------|----------------|----------|
| **`persistence/`** | Database, file, or other durable storage | SQLAlchemy async ORM (asyncpg), repository adapters, `get_db`, local seeding |
| **`messaging/`** | Publish or consume events/messages | RabbitMQ publisher, SQS consumer, outbox relay |
| **`integrations/`** | Call or verify third-party HTTP APIs | Payment provider client, webhook signature checker |
| **`notifications/`** | Send outbound alerts | SMTP email, Slack webhook adapter |
| **`cache/`** | Fast ephemeral lookups | Redis get/set adapter behind a domain port |
| **`auth/`** | Validate identity from an external source | Argon2 password hashing, JWT access-token issuance |

Only create a subpackage when you have real adapters for that system. Do not add empty placeholder folders.

### What does **not** belong here

| Location | Holds |
|----------|-------|
| **`domain/`** | Entities and port `Protocol`s — no framework imports |
| **`application/`** | Use-case orchestration across ports — no FastAPI or Pydantic |
| **`api/`** | HTTP routes and Pydantic request/response schemas |
| **`core/`** | Cross-cutting app wiring: logging, FastAPI `Depends` factories, exception handlers |

### `persistence/` in this project

`persistence/` is the infrastructure subpackage for **durable storage**. The backend is **PostgreSQL** via asyncpg, selected with **`DATABASE_URL`**.

| Piece | Responsibility |
|-------|----------------|
| **Driver URL** | `postgresql+asyncpg://…` — set in env profile (`database_url`), or explicit for Path C — see [Database](database.md#postgresql) |
| **`database.py`** | `require_async_db_driver`, `create_async_engine`, URL helpers (`database_url_is_postgresql`), `async_sessionmaker`, async `get_db`, `import_all_orm_models` |
| **`migrations.py`** | `run_migrations_async()` — canonical programmatic `alembic upgrade` (tests, seeding) |
| **`<feature>/`** | Per-aggregate adapters: `orm.py`, `mapper.py`, `repository.py` (dialect-agnostic SQLAlchemy) |
| **`seeding/`** | Dev/bootstrap: resets the configured DB (`TRUNCATE`), `run_migrations_async()`, then applies bundled `.sql` via async `text()` |
| **`alembic/`** (repo root) | Alembic `env.py` (async, reads `DATABASE_URL` from settings) and `versions/` revision scripts — owns DDL in dev/prod |
| **`docker-compose.infra.yml`** | Path A/B local infra: Valkey + PostgreSQL on `127.0.0.1` |
| **`docker-compose.app.base.yml`** | App container (Path B base, Path C production) |
| **`docker-compose.app.with-infra.yml`** | Path B overlay: `depends_on` bundled infra |

**Dependencies:** `sqlalchemy`, `asyncpg`, and `greenlet` in core (`pyproject.toml`). `require_async_db_driver` checks the asyncpg module before `create_async_engine`. Request-scoped code must not use synchronous `Session` for queries; keep async in repositories and routes.

**Tests** use a PostgreSQL test database ([`tests/conftest.py`](../../tests/conftest.py), `ENV_PROFILE=test`); they do not require Compose volumes but need PostgreSQL reachable on `127.0.0.1` at the port in [`profiles/test.py`](../src/env_config/profiles/test.py).

**Transactions:** `get_db` owns the unit of work for HTTP requests—it commits after the handler returns successfully and rolls back on exceptions. Repository adapters stage changes (`execute`, `add`, `flush`) but do not call `commit()`, so multiple adapter calls in one request share a single transaction.

If storage grows beyond a single database (e.g. S3 for attachments), add sibling adapters under `persistence/` (e.g. `persistence/files/`) or a dedicated subpackage if the mechanism is fundamentally different.

### `cache/` in this project

`cache/` holds **ephemeral storage** behind domain ports. Valkey is **required at runtime** for authenticated request identity caching.

| Piece | Responsibility |
|-------|----------------|
| **`VALKEY_URL`** | Valkey connection URL — set in env profile, or explicit for Path C — see [Deployment](../docs/deployment.md#local-podman-compose) |
| **`user_auth_cache_codec.py`** | JSON encode/decode for `AuthenticatedUser` cache entries |
| **`valkey_client.py`** | `require_valkey_driver`, `create_valkey_client` |
| **`valkey_user_auth_cache.py`** | Valkey adapter for `UserAuthCache` port |

**Domain port:** [`domain/auth/user_auth_cache.py`](../src/todos_app/domain/auth/user_auth_cache.py) — `UserAuthCache` Protocol (`get_active_user`, `set_active_user`, `invalidate_user`).

**Wiring:** `UserAuthCacheDep` in [`core/dependencies.py`](../src/todos_app/core/dependencies.py) always constructs `ValkeyUserAuthCache`. [`get_current_user`](../src/todos_app/core/auth.py) uses cache-aside after JWT decode; user update/deactivate/delete use cases invalidate entries via the same port.

**Dependencies:** `valkey` is a core runtime dependency in `pyproject.toml`. **Tests** override `get_user_auth_cache` with **`FakeUserAuthCache`** from [`tests/fakes/user_auth_cache.py`](../tests/fakes/user_auth_cache.py) (session autouse in [`tests/conftest.py`](../tests/conftest.py)) — no live Valkey in CI.

**Import style:** `valkey_client.py` lazy-loads the driver and constructs the client; `valkey_user_auth_cache.py` types its constructor with `Valkey` via `TYPE_CHECKING` only (no runtime `valkey` import). See [Development — Type-only imports](development.md#type-only-imports-and-lazy-driver-loading).

### Wiring adapters

Concrete classes from `infrastructure/` are constructed in **`core/dependencies.py`**, not imported directly by route handlers. That keeps the API layer depending on domain ports, not on `AsyncSession` or HTTP client libraries.

## Dependency injection

All FastAPI dependency providers live in [`src/todos_app/core/dependencies.py`](../src/todos_app/core/dependencies.py).

Pattern:

1. Define `DbSessionDep` as `Annotated[AsyncSession, Depends(get_db)]`.
2. Define a factory that receives `DbSessionDep` and returns a port implementation.
3. Expose an `Annotated` alias (e.g. `TodoRepositoryDep`) for route signatures.

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from todos_app.infrastructure.persistence.database import get_db

DbSessionDep = Annotated[AsyncSession, Depends(get_db)]

def get_todo_repository(db: DbSessionDep) -> TodoRepository:
    return SqlAlchemyTodoRepository(db)

TodoRepositoryDep = Annotated[TodoRepository, Depends(get_todo_repository)]
```

### Route example (async repository + actor scope)

Inject the port via `TodoRepositoryDep`, resolve owner scope from the authenticated actor, and `await` repository methods:

```python
from fastapi import Query

from todos_app.core.settings import get_settings

settings = get_settings()

@router.get("", response_model=TodoListResponse)
async def list_todos(
    repo: TodoRepositoryDep,
    current_user: CurrentUserDep,
    last_id: UUID | None = Query(None),
    limit: int = Query(
        settings.api.pagination_default_limit,
        ge=1,
        le=settings.api.pagination_max_limit,
    ),
) -> TodoListResponse:
    owner_filter = list_owner_filter(
        actor_id=current_user.user_id, actor_role=current_user.role
    )
    page = await repo.list_page(last_id, limit, owner_id=owner_filter)
    return TodoListResponse(
        items=[...],  # map page.items to TodoResponse
        next_last_id=page.next_last_id,
        limit=limit,
    )
```

Add new `get_*_repository` factories and `*Dep` aliases in `core/dependencies.py` as features are added.

## Configuration and secrets

Runtime configuration uses **profile-based Python modules** under [`src/env_config/`](../src/env_config/):

| Piece | Role |
|-------|------|
| [`schema.py`](../src/env_config/schema.py) | `EnvSettings` root + nested groups (`ApiSettings`, `JwtSettings`, `PostgresSettings`, …); all fields required; validation only |
| [`profiles/example.py`](../src/env_config/profiles/example.py) | Committed local template — copy to a gitignored profile (e.g. `local.py`, `local2.py`) |
| [`profiles/test.py`](../src/env_config/profiles/test.py) | Committed CI/pytest values (`ENV_PROFILE=test`) |
| [`profiles/production.example.py`](../src/env_config/profiles/production.example.py) | Production template — copy to gitignored `production.py` on deploy host |
| [`loader.py`](../src/env_config/loader.py) | `ENV_PROFILE=<name>` → load `profiles/<name>.py` → `get_env_settings()` |
| [`export.py`](../src/env_config/export.py) | Emit shell exports / generated `.env` for Compose |

[`core/settings.py`](../src/todos_app/core/settings.py) re-exports `get_settings()` / `Settings` for existing imports.

### Profile selection (`ENV_PROFILE`)

`ENV_PROFILE` must be set explicitly before scripts or the app load configuration — there is no silent default.

The value is the **module name** (not a path): `export ENV_PROFILE=local` loads [`profiles/local.py`](../src/env_config/profiles/local.py). Any valid identifier works — for example `local2` for a second local stack with different ports:

```bash
cp src/env_config/profiles/example.py src/env_config/profiles/local2.py
# edit ports, database_url, secrets in local2.py
export ENV_PROFILE=local2
```

**Rules:**

- Name must match `^[a-z][a-z0-9_]*$` (lowercase identifier; blocks `../other` and dotted paths).
- `example` is reserved (template only — copy it, do not load it directly).
- `production.example` is not a valid name (dots rejected); use `production` after copying the template.
- Secret-bearing profile files are **gitignored** (see `.gitignore`); only `example.py`, `production.example.py`, and `test.py` stay committed.

**`app_env` vs profile name:** the filename (`local`, `local2`, `production`, …) only selects which module loads. Runtime behavior (OpenAPI visibility, seed guards, production URL validation) comes from the `app_env` field inside that module (`local`, `staging`, or `production`).

**Local setup (default profile name `local`):**

```bash
cp src/env_config/profiles/example.py src/env_config/profiles/local.py
# edit secrets and URLs in local.py
export ENV_PROFILE=local   # required — set before running scripts
```

Shell scripts and Compose load vars via `python -m env_config.export --shell` (see [`scripts/internal/load_env.sh`](../scripts/internal/load_env.sh)). Compose still uses a generated gitignored `.env` from `env_write_dotenv`.

**Container listen port:** The app container always listens on internal port **8000** (Dockerfile `CMD`, healthcheck). Host binding uses `api_port` from the profile: `${COMPOSE_APP_BIND}:${API_PORT}:8000`.

**Package layout:** `env_config` lives alongside `todos_app` under `src/` (same wheel, `PYTHONPATH=src`). MCP imports it by adding `repo_root/src` to `sys.path` — not a separate distribution.

**Runtime overrides:** after loading the profile module, `get_env_settings()` merges any already-set process env vars (Compose `environment`, orchestrator injection) over profile values — so Path B can inject `@postgres` / `@valkey` URLs without editing `local.py` in the image.

`get_settings()` is cached with `@lru_cache` and exposed to routes via `SettingsDep` in `core/dependencies.py`.

## Authentication (JWT login)

Login is implemented as a thin API flow over existing user persistence and password hashing. Protected routes validate the `Authorization: Bearer` header and enforce **owner-or-admin** authorization where noted below.

![Protected route JWT authentication](images/auth_sequence.svg)

Source: [`docs/diagram/auth_sequence.puml`](diagram/auth_sequence.puml)

| Layer | Piece | Role |
|-------|-------|------|
| **API** | `api/auth/router.py`, `schemas.py` | `POST /auth/login` — delegates to `application/auth.py` |
| **API** | protected handlers in `api/todos/router.py`, `api/users/router.py` | Require `CurrentUserDep`; admin routes call domain `require_admin` in `api/users/router.py`; delegate orchestration to `application/` |
| **Application** | `application/auth.py` | `authenticate` — username lookup, password verify, access token issuance |
| **Application** | `application/users.py` | Create, load, update, deactivate, hard delete |
| **Application** | `application/todos.py` | Actor-scoped get, update, delete; owner-change forbidden check |
| **Application** | `application/errors.py` | Framework-free not-found, forbidden, and invalid-credentials exceptions |
| **Domain** | `domain/auth/authenticated_user.py` | Framework-free actor identity from a valid token |
| **Domain** | `domain/auth/authorization.py` | `is_admin`, `require_admin`, `list_owner_filter`, `resolve_create_owner_id`, `resolve_update_owner_id`, `is_update_owner_change_forbidden` |
| **Core** | `core/exceptions.py` | Maps `UserNotFoundError`, `TodoNotFoundError`, `AdminRequiredError`, `TodoOwnerChangeForbiddenError` to HTTP |
| **Domain** | `domain/auth/password_hasher.py` | `PasswordHasher` port — hash on register, verify on login |
| **Domain** | `domain/auth/access_token_issuer.py` | `AccessTokenIssuer` port — issue signed access tokens |
| **Domain** | `domain/auth/access_token_verifier.py` | `AccessTokenVerifier` port — decode and validate access tokens |
| **Infrastructure** | `infrastructure/auth/argon2_password_hasher.py` | Argon2 adapter for `PasswordHasher` |
| **Infrastructure** | `infrastructure/auth/jwt_access_token_issuer.py` | PyJWT adapter; reads signing settings from `Settings` |
| **Infrastructure** | `infrastructure/auth/jwt_access_token_verifier.py` | PyJWT decode adapter |
| **Core** | `core/auth.py` | `HTTPBearer` extraction, `get_current_user`, `CurrentUserDep` |
| **Core** | `core/settings.py` | JWT secret, algorithm, expiry |
| **Core** | `core/dependencies.py` | `PasswordHasherDep`, `AccessTokenIssuerDep`, `AccessTokenVerifierDep`, `SettingsDep` |

**Protected endpoints today**

| Method | Path | Rule |
|--------|------|------|
| `GET` | `/todos` | Authenticated; regular users see own todos only, admins see all |
| `GET` | `/todos/{todo_id}` | Authenticated; todo owner or admin; `404` when missing or not in actor scope |
| `POST` | `/todos` | Authenticated; regular users create for self (`owner_id` ignored), admins may set `owner_id` |
| `PUT` | `/todos/{todo_id}` | Todo owner or admin; scoped read + scoped `UPDATE`; `404` when not in scope; non-admins get `403` when changing `owner_id` |
| `PATCH` | `/todos/{todo_id}` | Same as `PUT` but partial body |
| `DELETE` | `/todos/{todo_id}` | Todo owner or admin; scoped read + scoped `DELETE`; `404` when not in scope |
| `GET` | `/users/me` | Authenticated caller's profile; `404` when missing |
| `PUT` | `/users/me` | Self-service full profile replace; password optional |
| `PATCH` | `/users/me` | Self-service partial profile update |
| `PUT` | `/users/{user_id}` | Admin only; full replace including `role` and `is_active` |
| `PATCH` | `/users/{user_id}` | Admin only; partial update |
| `DELETE` | `/users/{user_id}` | Admin only; soft delete (`is_active=false`) by default; `?hard=true` cascades todos then removes user |

Invalid or missing bearer tokens return **401** (`Could not validate credentials`). Todo routes return **404** when a todo is missing or outside the actor's scope (regular users: `You don't have a todo with this id`; admins: `Todo not found`). **403** is reserved for disallowed actions (for example a non-admin changing `owner_id` on a todo update, or a non-admin calling admin-only user routes).

Dependency: **PyJWT** (see `pyproject.toml`). **EnvSettings** uses Pydantic validation in `src/env_config/schema.py` (not pydantic-settings dotenv loading).

## Package layout

```text
src/
├── env_config/                      # profile-based runtime config (bundled with app wheel)
│   ├── schema.py                    # EnvSettings (Pydantic validation)
│   ├── loader.py                    # ENV_PROFILE → load profile → get_env_settings()
│   ├── export.py                    # shell / dotenv export for scripts and Compose
│   └── profiles/
│       ├── example.py               # local template → copy to gitignored local.py
│       ├── test.py                  # CI / pytest (ENV_PROFILE=test)
│       └── production.example.py    # production template → copy to production.py
└── todos_app/
    ├── main.py                          # FastAPI app, router includes, uvicorn entry
    ├── core/                            # cross-cutting wiring (no business rules)
    │   ├── logging.py                   # configure_logger
    │   ├── auth.py                      # HTTPBearer, get_current_user, CurrentUserDep
    │   ├── settings.py                  # shim → env_config.get_env_settings()
    │   ├── dependencies.py              # Depends factories and *Dep Annotated aliases
    │   ├── http_errors.py               # shared error detail strings for handlers
    │   ├── error_responses.py           # OpenAPI-oriented DB error examples
    │   └── exceptions.py                # register_exception_handlers (app/domain/DB errors → HTTP)
    ├── application/                     # use-case orchestration; no FastAPI or Pydantic
    │   ├── auth.py                      # authenticate (login orchestration)
    │   ├── errors.py                    # UserNotFoundError, TodoNotFoundError, …
    │   ├── users.py                     # create, load, update, deactivate, hard delete
    │   └── todos.py                     # actor-scoped get, update, delete
    ├── domain/                          # business meaning; no FastAPI or SQLAlchemy
    │   ├── auth/
    │   │   ├── access_token_issuer.py   # AccessTokenIssuer Protocol
    │   │   ├── access_token_verifier.py # AccessTokenVerifier Protocol
    │   │   ├── authenticated_user.py    # AuthenticatedUser dataclass
    │   │   ├── authorization.py         # is_admin, list_owner_filter, owner resolution
    │   │   ├── password_hasher.py       # PasswordHasher Protocol
    │   │   └── user_auth_cache.py       # UserAuthCache Protocol
    │   ├── todos/
    │   │   ├── entity.py                # Todo dataclass
    │   │   ├── page.py                  # TodoPage (cursor list result)
    │   │   ├── field_limits.py          # max lengths for validation alignment
    │   │   └── repository.py            # TodoRepository Protocol
    │   └── users/
    │       ├── entity.py                # User dataclass
    │       ├── field_limits.py
    │       └── repository.py            # UserRepository Protocol (incl. delete)
    ├── infrastructure/                  # adapters to external systems
    │   ├── auth/
    │   │   ├── argon2_password_hasher.py
    │   │   ├── jwt_access_token_issuer.py
    │   │   └── jwt_access_token_verifier.py
    │   ├── cache/
    │   │   ├── user_auth_cache_codec.py
    │   │   ├── valkey_client.py
    │   │   └── valkey_user_auth_cache.py
    │   └── persistence/
    │       ├── database.py              # async engine, AsyncSession, get_db, import_all_orm_models
    │       ├── migrations.py            # run_migrations_async() — Alembic upgrade/downgrade
    │       ├── seeding/
    │       │   ├── __main__.py          # python -m todos_app.infrastructure.persistence.seeding
    │       │   ├── runner.py            # reset_and_seed_defaults
    │       │   ├── default_users.sql
    │       │   └── default_todos.sql
    │       ├── todos/
    │       │   ├── orm.py               # TodoModel
    │       │   ├── mapper.py            # ORM ↔ Todo entity
    │       │   └── repository.py        # SqlAlchemyTodoRepository
    │       └── users/
    │           ├── orm.py               # UserModel
    │           ├── mapper.py            # ORM ↔ User entity
    │           └── repository.py        # SqlAlchemyUserRepository (update, hard delete + cascade)
    └── api/                             # HTTP boundary: routers, Pydantic schemas, schema/entity mappers
        ├── openapi_responses.py         # OpenAPIResponse enum and merge_* helpers
        ├── auth/
        │   ├── router.py                # POST /auth/login
        │   └── schemas.py
        ├── health/
        │   └── router.py                # GET /health
        ├── todos/
        │   ├── router.py                # CRUD + PATCH; delegates writes to application/todos
        │   ├── schemas.py               # TodoCreate, TodoUpdate, TodoPatch, TodoResponse, …
        │   ├── mappers.py               # schema/entity mapping and patch merge
        └── users/
            ├── router.py                # POST /users; GET/PUT/PATCH /me; admin /{user_id}; require_admin on admin routes
            ├── schemas.py               # UserSignup, UserSelf*, UserAdmin*, UserResponse
            └── mappers.py               # signup/replace/patch merge
```

Use-case orchestration lives in `application/`. The `api/` layer maps request/response schemas and calls use cases; list/create routes that are a single repo call may stay inline in the router until shared logic appears.

## Adding a new feature (e.g. users)

1. **Domain:** `domain/users/entity.py`, `domain/users/repository.py` (Protocol).
2. **Infrastructure:** `infrastructure/persistence/users/orm.py`, `mapper.py`, `repository.py`.
3. **Dependencies:** `get_user_repository` + `UserRepositoryDep` in `core/dependencies.py`.
4. **Application:** `application/<feature>.py` for shared orchestration; add exceptions to `application/errors.py` when needed and register HTTP handlers in `core/exceptions.py`.
5. **API:** `api/<feature>/router.py`, `schemas.py`, `mappers.py`; include router in `main.py`.
6. **Do not** import SQLAlchemy models or infrastructure types from domain, application, or route handlers directly.

## Layer rules (checklist)

- [ ] `domain/` imports nothing from `api/`, `application/`, or `infrastructure/`.
- [ ] `application/` imports nothing from `api/` or `infrastructure/`; no FastAPI imports.
- [ ] Application and domain exceptions are translated to HTTP in `core/exceptions.py`.
- [ ] Route handlers use `*RepositoryDep` aliases, not `AsyncSession` or ORM models directly.
- [ ] Repository ports and adapters use `async def`; persistence I/O is awaited in routes and use cases.
- [ ] New repository ports use `Protocol`; adapters live under the matching `infrastructure/<kind>/` subpackage.
- [ ] When a port enforces actor scope, use an explicit `owner_id` (or equivalent) parameter from `list_owner_filter` on both reads and mutating calls—not only on the entity payload.
- [ ] API schemas stay in `api/`; domain entities stay framework-free.
- [ ] DI factories are centralized in `core/dependencies.py`.

## Testing

The pytest suite lives at the repo root in **`tests/`** (outside `src/`). Each test module sets `pytestmark = pytest.mark.unit` or `pytest.mark.integration` (see `pyproject.toml` markers).

### Layout

```text
tests/
├── conftest.py                      # env vars, session DB, FakeUserAuthCache override, httpx client
├── factories.py                     # user_signup_payload, todo_create_payload
├── fakes/
│   ├── todo_repository.py           # in-memory TodoRepository for application unit tests
│   ├── user_repository.py           # in-memory UserRepository for application unit tests
│   └── user_auth_cache.py           # FakeUserAuthCache (no live Valkey in tests)
├── unit/
│   ├── domain/
│   │   └── test_authorization.py    # list_owner_filter, owner resolution, require_admin
│   ├── application/
│   │   ├── test_auth_use_cases.py   # authenticate; invalid credentials
│   │   ├── test_todo_use_cases.py   # get/update/delete for actor; owner-change rules
│   │   └── test_user_use_cases.py   # create, load, update, deactivate, hard delete
│   ├── api/
│   │   ├── test_todo_mappers.py     # create/update/patch/response mapping
│   │   ├── test_todo_schemas.py     # Pydantic schema validation (limits, required fields)
│   │   └── test_user_mappers.py     # signup/replace/patch mapping; password hashing stubs
│   ├── core/
│   │   ├── test_auth_cache.py       # get_current_user cache-aside behavior
│   │   ├── test_error_responses.py  # OpenAPI-oriented DB error examples
│   │   └── test_settings.py         # settings loading, API docs exposure by APP_ENV
│   └── infrastructure/
│       ├── test_jwt_access_token_verifier.py  # PyJWT decode edge cases
│       ├── cache/
│       │   ├── test_user_auth_cache_codec.py  # AuthenticatedUser JSON codec
│       │   └── test_valkey_client.py          # driver guard and client factory
│       └── persistence/
│           ├── test_database.py     # URL helpers, driver checks, local-host guards
│           ├── test_seeding.py      # seed safety guards and reset behavior
│           └── test_todo_mapper.py  # ORM ↔ Todo entity mapping
└── integration/
    ├── conftest.py                  # autouse: truncate users/todos before each test
    ├── persistence/
    │   ├── test_migrations.py       # run_migrations_async upgrade/downgrade round-trip
    │   ├── test_todo_repository.py  # SqlAlchemyTodoRepository CRUD + owner_id scope
    │   └── test_user_repository.py  # add/get/update/delete + cascade on hard delete
    └── api/
        ├── helpers.py               # register_and_login, auth_headers
        ├── test_auth.py             # login success/failure, 401 without token, deactivated user
        ├── test_health.py           # GET /health
        ├── test_todo_routes.py      # CRUD, pagination, owner scope, forbidden owner change
        └── test_user_routes.py      # /me, admin user CRUD, soft/hard delete, 409 duplicate email
```

| Path | Marker | Purpose |
|------|--------|---------|
| `tests/unit/` | `unit` | Fast tests without I/O: domain rules, application use cases with fakes, API mappers/schemas, core settings, JWT verifier, persistence helpers |
| `tests/integration/` | `integration` | SQLAlchemy repository adapters and HTTP routes via `httpx.AsyncClient` |

### What each layer tests

| Layer / kind | Module | Covers |
|--------------|--------|--------|
| **Domain** | `unit/domain/test_authorization.py` | `list_owner_filter`, `resolve_create_owner_id`, `is_update_owner_change_forbidden`, `require_admin` |
| **Application** | `unit/application/test_todo_use_cases.py` | `get_todo_for_actor`, `update_todo_for_actor`, `delete_todo_for_actor`; scope, owner-change forbidden, admin reassignment |
| **Application** | `unit/application/test_auth_use_cases.py` | `authenticate`; valid credentials issue token; invalid username/password/inactive user → `InvalidCredentialsError` |
| **Application** | `unit/application/test_user_use_cases.py` | `create_user`, `get_user_by_id`, `update_user`, `deactivate_user`, `hard_delete_user` |
| **API mappers** | `unit/api/test_todo_mappers.py` | Schema ↔ entity mapping for create, replace, patch, and list responses |
| **API schemas** | `unit/api/test_todo_schemas.py` | Pydantic validation for todo request/response schemas |
| **API mappers** | `unit/api/test_user_mappers.py` | Self/admin replace and patch; optional password; patch field exclusion |
| **Core** | `unit/core/test_settings.py` | Settings defaults, JWT config, API docs gated by `APP_ENV=local` |
| **Core** | `unit/core/test_auth_cache.py` | `get_current_user` cache hit/miss and invalidation paths |
| **Core** | `unit/core/test_error_responses.py` | Shared OpenAPI error response examples |
| **Infrastructure** | `unit/infrastructure/cache/test_user_auth_cache_codec.py` | JSON encode/decode for cached `AuthenticatedUser` |
| **Infrastructure** | `unit/infrastructure/cache/test_valkey_client.py` | `require_valkey_driver`, `create_valkey_client` |
| **Infrastructure** | `unit/infrastructure/test_jwt_access_token_verifier.py` | Valid tokens; invalid signature, claim types, and malformed payloads return `None` |
| **Persistence helpers** | `unit/infrastructure/persistence/test_database.py` | `DATABASE_URL` scheme detection and local-only guards |
| **Persistence helpers** | `unit/infrastructure/persistence/test_seeding.py` | Seed/wipe safety checks for non-local environments |
| **Persistence helpers** | `unit/infrastructure/persistence/test_todo_mapper.py` | ORM model ↔ domain entity mapping |
| **Persistence** | `integration/persistence/test_migrations.py` | `run_migrations_async` applies schema; downgrade/upgrade round-trip |
| **Persistence** | `integration/persistence/test_todo_repository.py` | Add, cursor pagination, `owner_id` filter on get/update/delete |
| **Persistence** | `integration/persistence/test_user_repository.py` | Add, get by id/username, update, hard delete with todo cascade |
| **HTTP** | `integration/api/test_auth.py` | `POST /auth/login`; protected route without bearer → 401; inactive user cannot log in |
| **HTTP** | `integration/api/test_health.py` | `GET /health` returns ok status for load balancers |
| **HTTP** | `integration/api/test_todo_routes.py` | End-to-end todo CRUD, pagination, cross-user 404, non-admin owner change → 403 |
| **HTTP** | `integration/api/test_user_routes.py` | `/users/me`, admin replace/patch/delete, soft vs hard delete, 404/409 error paths |

Application unit tests inject **`FakeTodoRepository`**, **`FakeUserRepository`**, and **`FakeUserAuthCache`** from `tests/fakes/` so use cases run without a database or Valkey. Integration API tests use **`register_and_login`** in `integration/api/helpers.py` and JSON builders in **`tests/factories.py`** to avoid duplicated request payloads.

### Fixtures and test database

Shared fixtures are in [`tests/conftest.py`](../tests/conftest.py):

- **`initialized_db`** (session) — at session **start**, drops and recreates the `public` schema, then runs `run_migrations_async("head")`
- **`override_password_hasher`** (session autouse) — `FastPasswordHasher` for faster integration setup
- **`db_session`** — per-test `AsyncSession` with rollback after the test (persistence tests)
- **`client`** — `httpx.AsyncClient` against the FastAPI app via `ASGITransport` (function-scoped in root conftest; **module-scoped** under `integration/api/`)

Integration tests use an autouse fixture in [`tests/integration/conftest.py`](../tests/integration/conftest.py) that **deletes** rows from `users` and `todos` before each test so cases stay isolated (with `synchronous_commit=off` on the reset connection for speed).

API integration setup uses **repo-based user factories** in [`tests/integration/api/helpers.py`](../tests/integration/api/helpers.py) (`create_user_in_db`, `register_and_login`) so tests hit the route under test without repeating `POST /users` signup; dedicated tests still cover signup/login HTTP. Tests override `get_password_hasher` with [`FastPasswordHasher`](../tests/fakes/fast_password_hasher.py) (low-cost Argon2). The HTTP client fixture in [`tests/integration/api/conftest.py`](../tests/integration/api/conftest.py) is **module-scoped** to reuse `AsyncClient` per API test module.

**Environment for tests:** set before importing `todos_app` (see root conftest):

- `ENV_PROFILE=test` — loads [`src/env_config/profiles/test.py`](../src/env_config/profiles/test.py) (`DATABASE_URL`, `JWT_SECRET_KEY`, Valkey URL, etc.)

**Test PostgreSQL bootstrap:** [`scripts/quality/tests.sh`](../scripts/quality/tests.sh) sets `ENV_PROFILE=test`, recreates the infra container when credentials do not match the test profile, creates `todos_test`, and stops the container afterward only when the script started it.

Tests do **not** use Compose volumes or a host dev database.

### Running tests

From the project root with dev dependencies installed:

```bash
pip install -e ".[dev]"
./scripts/quality/tests.sh
./scripts/quality/tests.sh -m unit
./scripts/quality/tests.sh -m integration
./scripts/quality/tests.sh --coverage
```

Coverage (optional) uses `pytest-cov`; HTML report under `htmlcov/`. The project enforces **90%** line coverage on `todos_app` (`fail_under` in `pyproject.toml`; seeding modules omitted).

Prefer **unit tests** for application orchestration and domain rules; **integration tests** for SQLAlchemy adapters and HTTP contracts. Keep routers thin and avoid asserting the same behavior in both layers unless the boundary differs (for example mapper unit tests plus one happy-path route test).

### GWT naming

Unit and integration tests under `tests/` use **Given–When–Then** naming and body structure:

- **Function name:** `test_given_{precondition}_when_{action}_then_{expected_outcome}` (snake_case, all three clauses).
- **Body sections:** `# given` (arrange), `# when` (single action under test), `# then` (assertions). Every test includes all three comment blocks.
- **One behavior per test** — split multi-step flows (for example separate create, list, and get route tests) instead of one long CRUD test.
- **Parametrized tests:** one GWT function name; `@pytest.mark.parametrize` varies the scenario; optional `ids=` for readable node IDs.
- **Exception tests:** the failing call lives in `# when` inside `pytest.raises(...)`; `# then` holds any follow-up asserts.

Serial pytest benchmark snapshot (post-optimization timings, xdist evaluation): [test-benchmark.md](test-benchmark.md).

### Local database reset

**Primary path:** [`scripts/database/wipe.sh`](../scripts/database/wipe.sh) removes Compose containers and named volumes (`compose down -v`), then re-run `./scripts/database/migrate.sh` (and optionally `./scripts/database/seed.sh`).
