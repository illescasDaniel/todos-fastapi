# Pytest benchmark snapshot

Serial suite timings (`./scripts/quality/tests.sh`) after [integration speed optimizations](architecture.md#testing). Re-run `./scripts/quality/benchmark_pytest.sh` to refresh.

## Latest snapshot (2026-06-14)

Path A, Podman PostgreSQL, Python 3.14, pytest 9.0.3, **32 cores** (serial only).

| Suite | Elapsed | Exit |
|-------|---------|------|
| Full (194 tests) | **2.821s** | 0 |
| Unit (128) | **1.779s** | 0 |
| Integration (66) | **2.296s** | 0 |
| Full + coverage | **3.501s** | 0 |

### Pre-optimization (same machine)

| Suite | Elapsed (approx.) |
|-------|-------------------|
| Integration | ~10–11s |
| Full | ~9–12s |
| Full + coverage | ~14s |

Integration ~**4–5×** faster (repo user setup, fast Argon2, lighter DB reset, module-scoped HTTP client, slimmer rate-limit tests, Postgres commit tuning).

## pytest-xdist

**Not adopted.** `-n auto` / `-n 2` slower than serial for unit; flaky integration (shared `todos_test`). Sub-4s full+coverage gate — worker spawn overhead wins.

## Re-run

```bash
./scripts/quality/benchmark_pytest.sh
./scripts/quality/benchmark_pytest.sh /tmp/my-benchmark.log
```

Script: reset Postgres with `ENV_PROFILE=test`, warm `todos_test`, time four runs, write log + `.tsv` (default `/tmp/`). Implementation: [`scripts/quality/internal/benchmark_pytest.sh`](../scripts/quality/internal/benchmark_pytest.sh).

← [Development](development.md#running-tests) · [Testing](architecture.md#testing)
