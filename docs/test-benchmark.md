# Pytest benchmark snapshot

Recorded timings for the **serial** pytest suite (`./scripts/quality/tests.sh`) after [integration test speed optimizations](architecture.md#testing). Use this doc to compare future changes; re-run the benchmark script to refresh numbers locally.

## Latest snapshot (2026-06-14)

Environment: local Path A, Podman PostgreSQL, Python 3.14, pytest 9.0.3, **32 CPU cores** (parallelism not used — serial pytest only).

| Suite | Elapsed | Exit |
|-------|---------|------|
| Full (194 tests) | **2.821s** | 0 |
| Unit only (128 tests) | **1.779s** | 0 |
| Integration only (66 tests) | **2.296s** | 0 |
| Full + coverage | **3.501s** | 0 |

### Before optimizations (same machine, pre-change)

| Suite | Elapsed (approx.) |
|-------|-------------------|
| Integration only | ~10–11s |
| Full suite | ~9–12s |
| Full + coverage | ~14s |

Integration suite improved by roughly **4–5×** (repo-based user setup, fast test Argon2, lighter DB reset, module-scoped HTTP client, slimmer rate-limit tests, local Postgres commit tuning).

## pytest-xdist

Evaluated and **not adopted**. On this repo and hardware, `-n auto` and `-n 2` were **slower** than serial for unit tests and **flaky** for integration (shared `todos_test` database). With a sub-4s full+coverage gate, worker spawn overhead dominates.

## Re-run locally

From the repo root (`.venv` active, dev deps installed):

```bash
./scripts/quality/benchmark_pytest.sh
# optional log path:
./scripts/quality/benchmark_pytest.sh /tmp/my-benchmark.log
```

The script:

1. Resets the local PostgreSQL container with `ENV_PROFILE=test` credentials (see [`profiles/test.py`](../src/env_config/profiles/test.py))
2. Warms up pytest + `todos_test`
3. Times four runs: full, unit, integration, full+coverage
4. Writes a log and `.tsv` summary (default under `/tmp/`)

Implementation: [`scripts/quality/internal/benchmark_pytest.sh`](../scripts/quality/internal/benchmark_pytest.sh).

← [Development](development.md#running-tests) · [Testing architecture](architecture.md#testing)
