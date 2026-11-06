# Runtime schema regression
Restore the Docker application against existing PostgreSQL volumes and pin the affected vehicle and entry flows with automated proof.

## Specs
1. S1 — "hace un momento levantamos la aplicacion pero no esta funcionando varios modulos [Image#1]  Y [Image#2]"
2. S2 — "realiza pruebas unitarias y de integracion"
3. S3 — "para que garanticemos que la aplicacion va funcionar correctamente"

## Tasks
- T1 [S1-S3] Diagnose the shared runtime failure and define regression coverage. Route: parent inline. Commit: this feature commit.
- T2 [S1-S3] Add an idempotent legacy-schema upgrade with unit/integration tests for vehicle registration and entry lookup. Route: delegated writer. Commit: this feature commit.
- T3 [S2-S3] Run focused, full backend, build, and live Docker HTTP verification; document any remaining limits. Route: independent verifier. Commit: this feature commit.

## Log
- L1 — hace un momento levantamos la aplicacion pero no esta funcionando varios modulos [Image#1]  Y [Image#2] realiza pruebas unitarias y de integracion para que garanticemos que la aplicacion va funcionar correctamente
- L2 — Runtime evidence: both screenshots share a backend PostgreSQL failure because the persistent `vehicles` table lacks the newer `active` column; the same legacy database also lacks `vehicle_audits`.
- L3 — T2 migration slice [S1-S3]: added `app.db.migrations.upgrade_schema(engine)` and an explicit Docker pre-uvicorn command. The additive upgrade preserves legacy vehicle rows, backfills `active=true`, and creates missing model tables including `vehicle_audits`; repeated runs preserve retired vehicles and audit rows. PostgreSQL starts serialize with a transaction-scoped advisory lock. FastAPI/TestClient startup is unchanged.
- L4 — Focused validation: `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_schema_migrations.py -v` — 3 passed. SQLite tests cover populated legacy upgrade twice, audit insertion with existing vehicle/account references, invalid references, retention of inactive vehicles/audits, unchanged current-schema DDL, and empty-database initialization. Strict TDD was not activated.
- L5 — Parent verification: focused vehicle/entry/migration set — 32 passed; complete backend suite — 126 passed, 3 skipped; Angular development build — passed. The existing PostgreSQL volume was upgraded in place: `vehicles.active` is `NOT NULL DEFAULT true`, `vehicle_audits` exists, and an authenticated live flow returned registration 201, new-vehicle lookup 200, seeded entry lookup 200, and `/entrada` 200. The probe row and audit were deleted afterward.
- L6 — PostgreSQL idempotency: restarting the backend ran the migration a second time and preserved availability; authenticated `GET /api/vehiculos/ABC123` returned 200 with `authorized=true` after restart.
- L7 — Repeatable integration proof [S1-S3]: `RUN_SCHEMA_MIGRATION_DOCKER=1 PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_schema_migration_runtime.py -v` — 1 passed in 15.46 s. The isolated test creates PostgreSQL 16 from the repository schema/seed, deliberately removes `vehicles.active` and `vehicle_audits`, starts the candidate backend, verifies health/auth/registration/audit/existing-vehicle lookup/schema restoration, restarts the backend, verifies lookup again, and removes only uniquely named test resources.
- L8 — Final regression: complete backend suite — 126 passed, 4 skipped; Angular development build — passed. Independent Risk item 1 verification returned S1 pass scoped, S2 pass, S3 pass with the explicit limit that this proves the reported legacy-schema regression rather than every possible application flow.
