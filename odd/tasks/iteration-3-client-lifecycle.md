# Iteration 3 — Client Lifecycle (T36)
Feature branch: `feat/i3-t36-client-lifecycle`, stacked on completed T35 at `bbdbb35`.
Scope: authenticated client deactivation, operational visibility, entry blocking, and payment-driven reactivation; T37 remains separate.

## Specs

1. **S1 — User direction:** “sigamos con t36”.
2. **S2 — Deactivation route:** “Usar `/baja`”. Implement `PATCH /api/clientes/{id}/baja` with a required Spanish `motivo` and a public lifecycle DTO.
3. **S3 — Roles:** “Administrador y operador”. Both authenticated roles may deactivate a client; unauthenticated requests return `401`.
4. **S4 — Open-stay guard:** Deactivation returns `409` when any vehicle owned by the client has a `ParkingStay` with `exited_at IS NULL`; rejection leaves client state and audits unchanged.
5. **S5 — Idempotency:** “200 idempotente”. Repeated deactivation returns the existing inactive state without changing timestamps, reason, responsible account, or creating another audit.
6. **S6 — Reactivation:** “Solo mediante pago nuevo”. No standalone reactivation endpoint is added; successful `POST /api/pagos` reactivates the client atomically and records one status audit.
7. **S7 — Visibility:** “Admin ve todos; operador solo activos”. `GET /api/clientes` filters inactive clients for operators while administrators can audit all clients.
8. **S8 — Operational enforcement:** An inactive client cannot start a new parking entry even if a prior membership cutoff remains current; payment reactivation enables later entry.
9. **S9 — Atomic audit:** Deactivation updates client lifecycle fields and creates exactly one `ClientStatusAudit(INACTIVATE)` in one transaction; persistence failure rolls back everything and leaves the session reusable.
10. **S10 — Public contract:** Spanish DTOs and stable errors: `CLIENT_NOT_FOUND`, `CLIENT_HAS_OPEN_STAY`, `CLIENT_INACTIVE`, and `INVALID_CLIENT_DATA`, with `{code,message,details}` and no private account data.

## Allowed edit surfaces

- `backend/app/services/client_lifecycle.py`
- `backend/app/services/entry.py`
- `backend/app/api/clients.py`
- `backend/app/schemas/client.py`
- `backend/app/main.py`
- `backend/tests/test_client_lifecycle.py`
- `backend/tests/test_clients.py`
- `backend/tests/test_entry.py`
- `backend/tests/test_payment_registration.py`
- `backend/tests/test_payment_api.py`
- `odd/tasks/iteration-3-client-lifecycle.md`

## Tasks

- [x] **T1** (`S2-S5`, `S9-S10`, inline, commit pending): Add RED service/API tests for authenticated deactivation, missing clients, open stays, idempotency, exact DTO/errors, audit, and rollback.
- [x] **T2** (`S2-S5`, `S9-S10`, inline, commit pending): Implement transactional client deactivation while locking the client and owned vehicles before checking open stays.
- [x] **T3** (`S6-S8`, `S10`, inline, commit pending): Enforce role-based client-list visibility and inactive-client entry rejection while preserving payment-driven atomic reactivation.
- [ ] **T4** (`S2-S10`, independent verification, commit pending): Run client, payment, membership, entry, persistence, authorization, and lifecycle regressions; record independent verdicts.

Risk: item 1 — deactivation and reactivation change persisted eligibility and audit state.
Risk: item 2 — role authorization and operational entry eligibility are security boundaries.
Risk: item 3 — T36 adds and changes public HTTP contracts consumed by the frontend.
Risk: item 4 — deactivation races with concurrent entry unless client-owned vehicles are locked consistently.

## Log

- **L1:** “sigamos con t36”
- **L2:** Exploration found lifecycle persistence fields and payment-driven reactivation already present, but no deactivation route/service/DTO/error handler or lifecycle tests. Entry did not check client status, and the client list exposed inactive clients to every authenticated role.
- **L3:** The user selected: `PATCH /api/clientes/{id}/baja`; both administrator and operator may deactivate; repeated deactivation returns `200` idempotently; reactivation occurs only through a new payment; administrators list all clients while operators list only active clients.
- **L4:** Human-approved DTO B: exactly `id`, `nombre`, `estado` (`ACTIVO`/`INACTIVO`), `fecha_baja` (ISO 8601 or null), `motivo`, `responsable_id` (numeric account identifier only). Idempotent replies preserve original persisted data.
- **L5:** Strict test-first: initial run exposed a fixture exit-pair constraint error, corrected before production edits. Re-run observed 16 failures and 1 pass: missing route/service, operator visibility, and missing inactive-entry enforcement. Implemented transactional deactivation with client/all-owned-vehicle locks and identity-map refresh, service role check, atomic INACTIVATE audit/rollback, exact DTO/errors, filtered list, and entry status check after the vehicle lock. S2, S3, S4, S5, S6, S7, S8, S9, S10 covered by T1–T3; payment implementation remains unchanged.
- **L6:** Final focused command (from repository root): `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_client_lifecycle.py -q --tb=short` — 19 passed. Includes induced audit/commit failures, session reuse, persisted snapshots, stale identity-map reload, PostgreSQL lock SQL compilation, payment replay and a second new payment producing only one REACTIVATE audit, followed by successful entry.
- **L7:** Proportional regression: `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_client_lifecycle.py tests/test_clients.py tests/test_entry.py tests/test_payment_registration.py tests/test_payment_api.py tests/test_membership_api.py tests/test_membership_cycle.py tests/test_payment_persistence.py tests/test_iteration2_persistence_model.py -q --tb=short` — 111 passed; one existing Starlette/AnyIO deprecation warning. SQLite fixture uses a second vehicle without history for post-payment entry because create_all does not reproduce PostgreSQL partial stay indexes.
- **L8:** T4 remains pending; no independent verdict, commit, or push. Real PostgreSQL concurrent execution was not tested. Review concurrent payment/deactivation lock ordering: payment currently locks vehicle then client, whereas deactivation locks client then vehicles, so PostgreSQL may abort one transaction on deadlock (rollback protects atomicity). Payment service is outside this task's allowed edit surfaces.
