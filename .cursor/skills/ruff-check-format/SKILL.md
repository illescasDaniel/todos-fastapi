---
name: ruff-check-format
description: Run the project's Ruff check-and-format workflow and iteratively resolve Ruff-reported warnings and errors in Python files. Use when linting, formatting, or fixing Ruff findings.
disable-model-invocation: true
---

# Ruff Check Format

## When to use

Use this skill when the user asks to lint, format, or fix Ruff diagnostics in this repository.

## Workflow

1. Ensure the project virtual environment is active (`.venv`).
2. Run:
   - `./.cursor/skills/ruff-check-format/scripts/run.sh`
3. Review Ruff output.
4. If Ruff reports warnings or errors that can be safely fixed, edit the relevant files to address them and rerun `./.cursor/skills/ruff-check-format/scripts/run.sh`.
5. If Ruff reports findings that cannot be auto-fixed (for example "No fixes available"), summarize the remaining diagnostics and notify the user so they can decide whether to proceed with manual fixes.
6. Repeat until Ruff reports no remaining errors, or stop and wait for user decision when required.

## Constraints

- Do not install packages globally.
- Use `./.cursor/skills/ruff-check-format/scripts/run.sh` as the canonical check-and-format script for this skill.
- Preserve project style conventions while fixing diagnostics.
