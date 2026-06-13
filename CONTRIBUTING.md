# Contributing

Thanks for your interest in this demo/portfolio project.

## Getting started

1. Clone the repository and follow [Getting started](docs/getting-started.md) — Python 3.14+, virtualenv, `.env`, migrations, and running the API.
2. Read [Architecture](docs/architecture.md) before structural changes (layer boundaries, DI, testing layout).

## Development workflow

- **Lint and format:** [Development — Ruff](docs/development.md#code-quality-and-linting-ruff)
- **Tests and coverage:** [Development — Running tests](docs/development.md#running-tests) (90% line coverage gate on `todos_app`)
- **Schema changes:** [Database — Alembic](docs/database.md#database-migrations-alembic)

Run `./scripts/run_ruff.sh` and `./scripts/run_tests.sh --coverage` before opening a pull request. For the full local gate (Ruff, basedpyright, MCP tests, CI audit), use `./scripts/run_checks.sh`.

## Pull requests

- Keep changes focused; match existing conventions (tabs in Python, thin routers, ports in `domain/`).
- Add or update tests when behavior changes (see [Architecture — Testing](docs/architecture.md#testing)).
- Do not commit `.env`, keys, or other secrets.

## Security

See [SECURITY.md](SECURITY.md) for scope, reporting, and deployment checklist items.

## Agent / IDE tooling

This repo may include `.cursor/` skills and `AGENTS.md` for Cursor-assisted development. They are optional maintainer tooling — not required for contributors using a standard editor.
