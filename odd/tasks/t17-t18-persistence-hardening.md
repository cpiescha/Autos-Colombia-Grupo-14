# T17–T18 Persistence Hardening

Finish and publish the Iteration 2 persistence foundation on `camilo-backend`. Keep `main` unchanged until the final iteration merge.

## Specs

1. **S1** — “si vamos a subir todo a camilo backend y al final hacemos merge al main”
2. **S2** — “vamos a seguir con t17 y 18”
3. **S3** — “al final lo subes al repo”
4. **S4** — “me das un resumen de lo que hicitse”

## Tasks

- [x] **T1** · S2 · Route: parent inline · Audited the existing T17/T18 persistence changes and preserved a reproducible RED baseline. Evidence: clean `9e44dc7` collection failed with circular `app.models` ↔ `app.db.operations` import, exit 2. Commit: `2c6681f`.
- [x] **T2** · S2 · Route: parent inline · Completed model/import compatibility, migration workflow, and focused persistence tests. Evidence: 4 focused tests, 60-test backend suite, and two-pass PostgreSQL migration verification passed. Commit: `2c6681f`.
- [ ] **T3** · S1, S3 · Route: parent inline · Packaged the synchronized Iteration 2 documentation and branch integration into reviewable commits; final verification and push remain. Commits: `9e44dc7`, `2f808ae`.
- [ ] **T4** · S1, S4 · Route: parent inline · Confirm the remote branch state, record deferred work, and provide the implementation summary. Commit: pending.

## Log

- **L1** — User request (original): "si vamos a subir todo a camilo backend y al final hacemos merge al main, vamos a seguir con t17 y 18 y al final lo subes al repo y me das un resumen de lo que hicitse"
- **L2** — `main` remains unchanged by explicit instruction; only `camilo-backend` will be published in this work.
- **L3** — Starting state: local `camilo-backend` is six commits ahead of `origin/camilo-backend`; Paul and Mafe are integrated locally. The clean committed T17/T18 state fails test collection through a circular `app.models` ↔ `app.db.operations` import, while three local source/doc corrections make the full backend suite pass 58 tests.
- **L4** — Delivery strategy: separate work-unit commits for persistence hardening, Iteration 2 source documentation, and final tracking evidence; push only after all applicable checks.
- **L5** — RED reproduced from the clean merge commit: `.venv/Scripts/python.exe -m pytest -q tests/test_iteration2_persistence_model.py` exited 2 during collection because `app.db.__init__` eagerly imported operations while models were only partially initialized. Docker Engine 29.2.1 is available for PostgreSQL migration verification.
- **L6** — GREEN: database operations now load lazily from `app.db`, PostgreSQL-only regex constraints no longer break SQLite metadata creation, and focused tests pin both behaviors. `pytest -q tests/test_iteration2_persistence_model.py` passed 4 tests; the complete backend suite passed 60 tests with one dependency deprecation warning.
- **L7** — PostgreSQL 16 migration proof started from `origin/main` schema, applied T17 + T18 + seed twice in single transactions, and produced 3 accounts, 80 active spots, and all 4 triggers. Plaintext passwords, occupied-spot deactivation, and deletion of a historical spot were all rejected.
- **L8** — Work-unit boundary: `2c6681f` contains the complete T17/T18 persistence hardening with tests and migration instructions. The three linked architecture/PRD source documents form one documentation work unit in `2f808ae`; together they exceed the nominal 400-line review budget because they are pre-existing complete academic source documents required by the tracked links, not a code behavior slice.
- **L9** — Independent high-risk verification approved S2 with one medium reservation: after renaming a demo account, rerunning `seed.sql` could violate `UNIQUE(operator_id)` because conflict handling covered only username. Added a RED/GREEN regression assertion and guarded account insertion by existing `operator_id`. PostgreSQL reproduction after renaming `admin` to `admin.renamed` passed: 3 total accounts, one account for the administrator operator, and the renamed username preserved.
- **L10** — Native review was due for the committed range, but two fresh START attempts failed before lineage creation in the provider candidate-view `git worktree` step. No native review authority or verdict was created; functional verification remains authoritative for this delivery.
