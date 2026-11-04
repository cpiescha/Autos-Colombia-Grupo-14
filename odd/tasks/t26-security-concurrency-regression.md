# T26 Security, Concurrency, Audit, and Regression

Add reproducible PostgreSQL/Docker verification for the integrated Iteration 2 system on `test/i2-t26-security-concurrency-regression`. Keep ordinary fast backend tests independent from Docker; runtime scenarios must use isolated data and prove final database integrity.

## Specs

1. **S1** — “+si sigamos con t26”
2. **S2** — “Pruebas de permisos, concurrencia, auditoría y regresión de Iteración 1”
3. **S3** — “Dos operadores trabajan simultáneamente; no comparten celda; flujos anteriores siguen funcionando”
4. **S4** — “Dos sesiones registran entradas simultáneas con celdas suficientes”
5. **S5** — “Dos solicitudes simultáneas intentan ocupar una única celda compatible”

## Tasks

- [x] **T1** · S1-S5 · Route: parent inline · Added an opt-in PostgreSQL/Docker pytest harness with isolated project/volume lifecycle, deterministic data preparation, HTTP helpers, SQL integrity queries, and automatic cleanup. Commit: `cf4df91`.
- [x] **T2** · S2-S4 · Route: parent inline · Verified `operario1` and `operario2` enter simultaneously, receive different cells/receipts, and persist their own responsible accounts. Commit: `cf4df91`.
- [x] **T3** · S2-S3, S5 · Route: parent inline · Verified two entries competing for the only active compatible cell produce one `201`, one `409 NO_COMPATIBLE_SPACE`, exactly one stay/receipt, and no partial state. Commit: `cf4df91`.
- [x] **T4** · S2-S3 · Route: parent inline · Verified operator `403` with unchanged data, vehicle audit attribution, session invalidation after account annulment, and authenticated entry/correction/report/preview/exit regression with entry/correction/exit actors preserved. Commit: `cf4df91`.
- [x] **T5** · S1-S5 · Route: parent integration · Documented commands/results in `docs/VERIFICACION_T26.md`; PostgreSQL/Docker scenarios, Python compilation, default opt-in skip behavior, and structural checks passed. The complete ordinary suite attempt timed out after 75 tests and was not retried; the prior T25 baseline was 120/120. Commit: `cf4df91` plus closing metadata commit.

## Allowed edit surfaces

- `backend/tests/test_t26_runtime.py`
- `backend/tests/t26_runtime_support.py`
- `backend/tests/README.md`
- `docs/VERIFICACION_T26.md`
- `README.md`
- this task document

## Log

- **L1** — User request (original): “+si sigamos con t26”
- **L2** — Starting state: `camilo-backend` at `e82169a`; the ordinary SQLite-backed backend suite passes 120 tests, but no automated PostgreSQL concurrency test exists. T13 concurrency remained explicitly deferred in `docs/VERIFICACION_MANUAL_ITERACION_1.md`.
- **L3** — T26 runtime proof must use PostgreSQL 16 because `FOR UPDATE SKIP LOCKED`, partial unique indexes, transaction isolation, and concurrent HTTP sessions are not proven by SQLite.
- **L4** — Added `RUN_T26_DOCKER=1` opt-in tests so the ordinary suite does not require Docker. `test_t26_runtime.py` starts a clean Compose project, waits for backend/frontend health, executes three PostgreSQL scenarios, and verifies cleanup from the fixture `finally`.
- **L5** — Runtime verification passed 3/3 in 44.75 seconds. It proved two distinct cells and actors under simultaneous entry, the one-cell race without partial state, operator permission denial immutability, vehicle audit ownership, account invalidation of a pre-issued token, and the Iteration 1 entry→correction→report→preview→exit flow with audit attribution. Python compilation and `git diff --check` passed. A parent attempt to rerun the entire ordinary suite exceeded the 30-second synchronous limit after 75 tests; it was not retried or migrated. The previous T25 baseline remains 120/120 before these opt-in skipped-by-default tests.
- **L6** — Independent verification requested corrections: startup cleanup was outside `finally`, project/ports were shared, transaction overlap was not proven, actor assertions allowed swaps, and immutability checks were too narrow.
- **L7** — Corrections use unique Compose projects/ports, explicit PostgreSQL settings, checked cleanup, a PostgreSQL insert delay to prove transaction overlap and lock-time rejection, exact plate→operator→response attribution, and whole-database fingerprints around rejected requests. Corrected Docker run passed 3/3 in 38.24 seconds.
- **Risk:** item 1 (runtime tests mutate isolated PostgreSQL data), item 2 (permissions/session invalidation), item 3 (shared operational contracts), and item 4 (concurrency). Verification asserts HTTP results, responsible accounts, receipts/stays, exact overlap, and unchanged data after rejection.
