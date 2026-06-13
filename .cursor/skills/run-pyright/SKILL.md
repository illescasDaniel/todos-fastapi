---
name: run-pyright
description: Run basedpyright type checking via run_pyright.sh for src, tests, and MCP. Use when fixing type errors or verifying typed API changes.
disable-model-invocation: true
---

# Run Pyright

## When to use

Use this skill when the user asks to type-check Python code, fix basedpyright/pyright diagnostics, or verify typed API changes.

## Workflow

1. Ensure the project virtual environment is active (`.venv`) with dev dependencies installed.
2. Run:
   - `./.cursor/skills/run-pyright/scripts/run.sh`
3. Review basedpyright output.
4. Fix reported type errors in source files; test and MCP files may use targeted `# pyright: ignore` where pytest fixtures or third-party stubs require it.
5. Repeat until basedpyright reports no errors, or report remaining diagnostics to the user.

## Constraints

- Do not install packages globally.
- Use `./.cursor/skills/run-pyright/scripts/run.sh` as the canonical type-check script for this skill.
- Scope is configured in root `pyproject.toml` → `[tool.basedpyright]` (`src/`, `tests/`, `mcp/todos-backend/`).
- The script auto-installs `mcp/todos-backend/` editable when `todos_mcp` is not importable.
