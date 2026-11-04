# T25 Frontend API Integration

Integrate the existing Angular T23–T24 screens and Iteration 1 flows with the authenticated FastAPI APIs already delivered through T22. Work proceeds in reviewable units on `feat/i2-t25-frontend-api-integration`; publishing and merging remain separate decisions.

## Specs

1. **S1** — “sigamos con t25 pero ve mostrandome que cambios vas haciendo”
2. **S2** — “Integración completa del frontend con autenticación y APIs”
3. **S3** — “Recargar conserva o invalida correctamente la sesión; errores `401/403` se muestran sin romper la aplicación”
4. **S4** — “Agregar selector de clientes”

## Tasks

- [x] **T1** · S1-S3 · Route: parent integration + bounded writer · Replaced simulated authentication with `/api/auth/login`, `/api/auth/me`, and `/api/auth/logout`; guards validate restored sessions, `401` expiry stays visible after redirect, and inactive accounts retain their specific message. Commit: `0a2cccf`.
- [x] **T2** · S1-S3 · Route: bounded writer · Replaced simulated operator and parking-spot administration services with the real T20/T21 APIs; pages now load and mutate asynchronously, display backend errors, use numeric cell IDs, and handle physical `204` versus history-preserving `200` deletion. Commit: `0a2cccf`.
- [x] **T3** · S1-S3 · Route: bounded writer · Adapted entry, exit, occupancy, active movements, reports, and correction to T22: requests no longer send operator identity, current actions use the authenticated session label, inactive cells are excluded, load failures stay visible, and `/correccion/:id` is reachable for both roles. Commit: `adc59cc`.
- [x] **T4** · S1-S4 · Route: failed writer recovered inline · Added authenticated read-only `GET /api/clientes`, extended vehicle lookup with client/active data, and added both-role registration plus administrator-only update/retirement pages with client selection. Commit: `dde0b72`.
- [x] **T5** · S1-S3 · Route: parent integration · Reconciled routes/navigation/errors, updated README, and verified TypeScript, Angular production build, 120 backend tests, Compose configuration, and diff hygiene. Live Docker HTTP checks were unavailable because the local Compose invocation had no `AUTH_SECRET`. Commit: `fced286`.

## Allowed edit surfaces

- **Auth unit:** `frontend/src/app/core/**`, `frontend/src/app/models/auth.model.ts`, `frontend/src/app/pages/login/**`, auth-focused frontend test/config files.
- **Administration unit:** `frontend/src/app/services/operadores.service.ts`, `frontend/src/app/services/celdas.service.ts`, `frontend/src/app/pages/admin/operadores/**`, `frontend/src/app/pages/admin/celdas/**`, related models/tests.
- **Operational unit:** `frontend/src/app/services/acceso.service.ts`, `frontend/src/app/pages/entrada/**`, `frontend/src/app/pages/salida/**`, `frontend/src/app/pages/ocupacion/**`, `frontend/src/app/pages/presentes/**`, `frontend/src/app/pages/reportes/**`, `frontend/src/app/pages/correccion/**`, related models/tests.
- **Vehicle unit:** new vehicle service/pages/models/tests under `frontend/src/app/`.
- **Parent-only integration:** `frontend/src/app/app.routes.ts`, `frontend/src/app/app.config.ts`, `frontend/src/app/layout/**`, `README.md`, this task document.

## Log

- **L1** — User request (original): “sigamos con t25 pero ve mostrandome que cambios vas haciendo”
- **L2** — Starting evidence: backend T19–T22 is present; T23–T24 screens exist but authentication, operator administration, and parking-spot administration still use simulated in-memory data. `AccesoService` already calls FastAPI but still sends a fixed `operario_id`, while T22 derives identity from the bearer token. No frontend vehicle administration flow exists.
- **L3** — Frontend test runner is not configured in `frontend/angular.json`; T25 will use focused TypeScript/build/runtime checks and will not claim T26 frontend test completion.
- **L4** — Vehicle integration exposed that `POST /api/vehiculos` requires `cliente_id` but no client-list API exists. User decision (verbatim option selected): “Agregar selector de clientes”. T4 therefore includes a read-only client endpoint and a visible existing-client selector; no client CRUD is added.
- **L5** — T1/T2 implementation replaced all auth/operator/cell mocks. Parent verification passed `npx tsc -p tsconfig.app.json --noEmit`, `npm run build`, and `git diff --check`; the Angular build retains the existing bundle-budget warning (700.47 kB versus 500 kB). Independent verification found two visible-auth-message defects: expired sessions redirected silently and inactive accounts were labeled as bad credentials. Both were corrected by preserving one consumable login notice and branching on backend code `ACCOUNT_INACTIVE`; the applicable independent verifier was not rerun.
- **L6** — Work-unit commit `0a2cccf` contains T1/T2 and their task evidence (404 insertions, 288 deletions). Native review was due for the committed range from `47853c4`, but START failed before lineage creation during provider candidate-view worktree preparation; no native authority or verdict was created.
- **L7** — T3 removed fixed `operario_id` payloads and fixed operator labels, mapped inactive cells, preserved last known operational state on refresh failure, exposed loading/errors, and restored the missing correction route. Parent checks passed TypeScript, Angular production build (existing warning: 710.98 kB versus 500 kB), structural identity assertions, and `git diff --check`. Independent verification found optional vehicle-detail enrichment could set the shared load error and disable a valid correction; the lookup is now non-blocking and final TypeScript compilation passes. The applicable independent verifier was not rerun. Work-unit commit: `adc59cc` (125 insertions, 66 deletions).
- **L8** — Review slices are bounded as `0a2cccf` (T1/T2 auth + administration) and `adc59cc` (T3 operational integration). T4 remains a separate vehicle/client contract slice because it adds a new read-only backend endpoint and new frontend behavior.
- **L9** — The T4 writer failed twice (first before edits, then after adding only tests because it invoked the system Python without pytest). Parent recovery used `backend/.venv`, observed RED with four `404` failures, then GREEN with 4/4 client endpoint tests. Vehicle lookup was extended by RED/GREEN with `cliente_id` and `activo`. Final focused backend suites passed 18/18; TypeScript and Angular production build passed with the existing bundle warning (721.16 kB versus 500 kB); `git diff --check` passed. Independent verification found failed lookups discarded edit state, invalid forms were silent, success messages became stale, and client-load failures could disappear. Corrections preserve forms, expose validation, clear stale messages, and keep a dedicated retryable client-load error; the verifier was not rerun. Work-unit commit: `dde0b72` (307 insertions, 3 deletions).
- **L10** — Final regression: backend suite passed 120/120 with one dependency deprecation warning; Angular TypeScript and production build passed; explicit-secret `docker compose config --quiet` passed; `git diff --check` passed. A live Compose status/runtime pass was skipped because the local environment did not provide the required `AUTH_SECRET`; no runtime success is claimed. README now documents authenticated request flow, role boundaries, vehicle/client selection, and automated tests.
- **Risk:** item 2 (authentication and role boundaries) and item 3 (shared frontend HTTP contracts and existing operational flows). Each work unit requires focused verification and an independent verifier before closure.
