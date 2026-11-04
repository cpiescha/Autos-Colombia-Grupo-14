# T22 Operational Authorization and Audit

Protect Iteration 1 operations with the T19 identity boundary, add role-aware vehicle management, and derive every responsible operator from the authenticated account. Vehicle registration uses an existing client selected by `cliente_id`; no client CRUD is added.

## Specs

1. **S1** — “sigue con t 22”
2. **S2** — “Adaptar vehículos, entradas y salidas para permisos y auditoría”
3. **S3** — “Ambos perfiles operan; solo administrador edita/elimina vehículos; queda responsable registrado”
4. **S4** — “Tanto administrador como operador pueden registrar un vehículo nuevo cuando la placa todavía no existe.”
5. **S5** — “Después de guardar, solo el administrador puede editar o eliminar el registro del vehículo.”
6. **S6** — “Cada movimiento debe conservar qué usuario autenticado lo realizó”
7. **S7** — “Usar cliente existente (recomendado)”

## Tasks

- [x] **T1** · S1-S7 · Route: parent inline · Establish RED contract tests, reconcile the two writer units, and preserve exact 401/403/no-mutation behavior. Commit: 325a38f.
- [x] **T2** · S4-S5, S7 · Route: parallel writer A · Implement authenticated vehicle registration for both roles, administrator-only update/retirement, existing-client validation, logical retirement/history preservation, and vehicle audit evidence. Commit: 325a38f.
- [x] **T3** · S2-S3, S6 · Route: parallel writer B · Protect lookup, entry, exit, active movements, occupancy reports, and correction; remove caller-controlled operator IDs and derive the responsible operator from the session. Commit: 325a38f.
- [x] **T4** · S1-S7 · Route: parent integration · Resolve shared router/error/docs integration, run focused and full regression checks, and verify the real PostgreSQL HTTP stack. Commit: 325a38f.
- [x] **T5** · S1-S7 · Route: independent verifier for items 1-3 · Verify permission boundaries, audit attribution, logical retirement, rejected-request immutability, and Iteration 1 regression. Commit: 325a38f.
- [x] **T6** · S1-S7 · Route: parent inline · Record evidence, publish directly to `camilo-backend`, and confirm the remote revision. Commit: 325a38f.

## Allowed edit surfaces

- **Writer A — vehicles:** `backend/app/api/vehicles.py`, `backend/app/schemas/vehicle.py`, `backend/app/services/vehicle*.py`, `backend/app/models/vehicle.py`, new vehicle-audit model files, `backend/app/models/__init__.py`, `backend/scripts/schema.sql`, new T22 migration scripts, `backend/scripts/seed.sql` only if required, and `backend/tests/test_vehicle*.py`.
- **Writer B — operational identity:** `backend/app/api/entries.py`, `backend/app/api/exits.py`, `backend/app/api/corrections.py`, `backend/app/api/occupancy.py`, `backend/app/schemas/entry.py`, `backend/app/schemas/exit.py`, `backend/app/schemas/correction.py`, `backend/tests/test_entry.py`, `backend/tests/test_exit.py`, `backend/tests/test_correction.py`, `backend/tests/test_occupancy.py`, and new operational authorization test files.
- **Parent-only integration:** `backend/app/main.py`, `backend/app/api/dependencies.py`, `README.md`, `docs/`, and this task document.

## Log

- **L1** — User request (original): "sigue con t 22"
- **L2** — Product decision: "Usar cliente existente (recomendado)". `POST /api/vehiculos` receives `cliente_id`; invalid clients are rejected without adding vehicle or audit rows.
- **L3** — Exploration found every Iteration 1 operational endpoint except `/api/celdas` remains unauthenticated, and entry/exit/correction accept caller-controlled `operario_id`. Existing services already persist operator IDs, so routes can pass `current_account.operator_id` without changing transaction boundaries.
- **L4** — Exploration also found vehicle lookup exists but registration/update/retirement do not. `Vehicle.client_id` is mandatory and there is no client API; S7 resolves this without expanding scope. Vehicle retirement must be logical when history exists and administrative changes need durable actor evidence.
- **L5** — Integration gap: writer B had added local `get_entry_repository(db, use_cache=False)` in `backend/app/api/entries.py` to escape the shared auth-session transaction, which bypassed the shared dependency override and broke every pre-existing entry/exit/correction/occupancy test. Resolved by moving `use_cache=False` to the shared `get_entry_repository` in `backend/app/api/dependencies.py` and to `get_current_account`, so auth and write paths always open distinct sessions. The four Iteration-1 suites were updated to inject the authenticated account via `app.dependency_overrides[get_current_account]`, drop the removed `operario_id` request field, and derive the expected operator from the session.
- **L6** — Verification evidence: 116/116 backend tests passing on SQLite (`backend\.venv\Scripts\python.exe -m pytest`, 11s). PostgreSQL 16 end-to-end on an isolated Docker project (`autos_t22`, port 55432, tmpfs volume) seeded from `scripts/schema.sql` + `scripts/seed.sql`; booted the API on port 18080 and ran 16 HTTP probes — all green: 401 without token for `/api/vehiculos`, `/api/entradas`, `/api/movimientos/activos`, `/api/reportes/ocupacion`; both roles register vehicles; operator gets 403 on PUT/DELETE; duplicate plate normalized to uppercase → 409; admin DELETE marks `active=false` and a second DELETE → 409; GET of the retired plate still returns 200 with `authorized=false`; invalid `cliente_id=9999` → 422; `vehicle_audits` rows show `CREATE` (account_id=3 operario1), `UPDATE` and `RETIRE` (account_id=1 admin) with the correct before/after JSON snapshots.
- **Risk:** item 1 (vehicle retirement and audit persistence), item 2 (authorization and authenticated identity), and item 3 (public request contracts and every existing operational route). Rejected 401/403/409/422 requests must preserve all business and audit state.
