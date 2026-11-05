# T20 Operator Administration

Implement administrator-only operator account management on `feat/i2-t20-operator-admin`, then merge and publish the verified result directly to `camilo-backend`.

## Specs

1. **S1** — “listo sigamos con t20”
2. **S2** — “continua con t20”
3. **S3** — “API administrativa de operadores y guards por rol”
4. **S4** — “Operador recibe `403` al intentar administrar usuarios”
5. **S5** — “permitir al administrador crear cuentas de operadores con credenciales individuales.”
6. **S6** — “permitir al administrador consultar, anular y reactivar operadores sin borrar su historial.”
7. **S7** — “`GET /api/operadores`”, “`POST /api/operadores`” y “`PATCH /api/operadores/{id}/estado`”

## Tasks

- [x] **T1** · S3-S7 · Route: parent inline · Added public-interface tests for listing, creation, duplicate rejection, state changes, and operator `403`; observed RED. Evidence: five tests failed against missing `/api/operadores` routes with `404`. Commit: `ac9dfd4`.
- [x] **T2** · S3-S7 · Route: parent inline · Implemented administrator guard, operator administration schemas/service/router, bcrypt hashing, atomic duplicate rejection, stable errors, blank-name validation (`422 INVALID_OPERATOR_DATA`), and account state preservation. Evidence: eight focused tests pass. Commit: `ac9dfd4`.
- [x] **T3** · S3-S7 · Route: parent inline · Documented T20 payloads, responses, authorization errors, duplicate rollback, bcrypt bounds, and historical preservation in `README.md`; preserved T19 token revalidation. Commit: `ac9dfd4`.
- [x] **T4** · S1-S7 · Route: parent inline · Focused suite `tests/test_operator_admin.py` 8/8 passed; full backend suite 77/77 passed; no state leakage between tests. Commit: `ac9dfd4`.
- [x] **T5** · S1-S7 · Route: parent inline · Fast-forward merge of `ac9dfd4` into `camilo-backend` and push; `origin/camilo-backend` HEAD confirmed at `ac9dfd4`. Commit: `ac9dfd4`.

## Log

- **L1** — User request (original): "listo sigamos con t20"
- **L2** — User continuation: "continua con t20"
- **L3** — Referenced T20 source: `docs/PLAN_DESARROLLO_GITHUB.md`, `docs/PRD_Autos_Colombia_Iteracion_2.md`, and the REST contract in `docs/ARQUITECTURA_TECNICA_AUTOS_COLOMBIA.md`.
- **L4** — Scope boundary: T20 manages operator accounts only. T21 cell administration, T22 operational permissions/auditing, and T25 frontend HTTP integration remain deferred.
- **L5** — Delivery strategy: one cohesive security work-unit commit with endpoint behavior, role guard, tests, and docs; after verification it is merged and pushed directly to `camilo-backend` per the standing project instruction.
- **L6** — RED: `.venv/Scripts/python.exe -m pytest -q tests/test_operator_admin.py` produced five failures. All three `/api/operadores` routes returned `404`; no administration or role guard existed.
- **L7** — GREEN: the focused suite now has six passing tests covering unauthenticated `401`, operator `403` with unchanged rows/state, safe listing, bcrypt creation, duplicate rollback, and reversible account state without historical deletion.
- **L8** — Documentation: `README.md` now records the three administrator-only endpoints, accepted payloads, password bounds, stable `401`/`403`/`409` errors, and non-destructive state changes.
- **L9** — Bugfix (2026-11-02): `OperatorCreateRequest.normalize_name` previously accepted `"   "` because `min_length=3` runs before the normalizer; the normalizer now rejects any post-collapse value shorter than 3 characters so blank names fail with `422 INVALID_OPERATOR_DATA` and no partial rows are inserted. New regression test: `test_blank_operator_name_is_rejected_without_partial_rows`.
- **L10** — Verification (T4): `.venv/Scripts/python.exe -m pytest -q tests/test_operator_admin.py` → `8 passed`; `.venv/Scripts/python.exe -m pytest -q` (full backend suite) → `77 passed`. Risk: item 2 (security — administrator guard, bcrypt) and item 3 (public API contract) satisfied by the focused and regression suites.
- **L11** — Delivery (T5): commit `ac9dfd4` on `feat/i2-t20-operator-admin`, fast-forward into `camilo-backend`, push successful; `git ls-remote origin camilo-backend` returned `ac9dfd49559eeba1d20893ed0adfb33e2c7cc8c8`.
