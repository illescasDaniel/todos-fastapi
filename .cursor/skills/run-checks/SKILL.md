---
name: run-checks
description: Run the full quality gate via scripts/quality/checks.sh. Local workflow is --fix first, then confirm without --fix. Use after substantive code changes before considering work done.
disable-model-invocation: true
---

# Run Checks

## When to use

Use this skill after substantive code changes to run the full quality gate — the same steps as GitHub Actions, plus optional local stack verification.

## Workflow

1. Ensure the project virtual environment is active (`.venv`) with dev dependencies installed (`pip install -e ".[dev]"`).
2. **First run (required locally):**
   - `./.cursor/skills/run-checks/scripts/run.sh --fix`
   - Ruff autofix + format, then audit, basedpyright, MCP tests, pytest with coverage.
3. **Confirm pass (required locally):**
   - `./.cursor/skills/run-checks/scripts/run.sh`
   - Check-only Ruff (same as CI). Must exit 0 before the task is done.
4. If the confirm pass fails, fix reported errors and repeat from step 2.
5. Optional: add `--full` on the **first** run only for stack verification after the gate (`scripts/verify/verify_stack.sh`; local only, not CI). Still run step 3 afterward.

## Constraints

- Do not install packages globally.
- **Do not** use a check-only run as the only local gate pass — always run `--fix` first, then confirm without `--fix`.
- All steps run in order each time; failures do not skip later steps.
- Exit 1 only on errors; warnings appear in the report and as GHA `::warning::` annotations.
- Individual step scripts: `scripts/quality/{checks,tests,ruff,pyright}.sh`; gate internals in `scripts/quality/internal/`.
