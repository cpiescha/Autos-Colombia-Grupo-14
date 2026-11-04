# T25 Frontend API Integration

Integrate the existing Angular T23–T24 screens and Iteration 1 flows with the authenticated FastAPI APIs already delivered through T22. Work proceeds in reviewable units on `feat/i2-t25-frontend-api-integration`; publishing and merging remain separate decisions.

## Specs

1. **S1** — “sigamos con t25 pero ve mostrandome que cambios vas haciendo”
2. **S2** — “Integración completa del frontend con autenticación y APIs”
3. **S3** — “Recargar conserva o invalida correctamente la sesión; errores `401/403` se muestran sin romper la aplicación”
4. **S4** — “Agregar selector de clientes”

## Tasks

- [x] **T1** · S1-S3 · Route: parent integration + bounded writer · Replaced simulated authentication with `/api/auth/login`, `/api/auth/me`, and `/api/auth/logout`; guards validate restored sessions, `401` expiry stays visible after redirect, and inactive accounts retain their specific message. Commit: auth/admin work-unit commit pending.
- [x] **T2** · S1-S3 · Route: bounded writer · Replaced simulated operator and parking-spot administration services with the real T20/T21 APIs; pages now load and mutate asynchronously, display backend errors, use numeric cell IDs, and handle physical `204` versus history-preserving `200` deletion. Commit: auth/admin work-unit commit pending.
- [ ] **T3** · S1-S3 · Route: bounded writer · Adapt existing entry, exit, occupancy, movement, and correction flows to the T22 authenticated contracts, removing caller-controlled operator identity. Commit: pending.
- [ ] **T4** · S1-S4 · Route: bounded writer · Add a read-only existing-client endpoint and selector, plus the missing vehicle registration and administrator-only update/retirement frontend flows backed by the T22 vehicle API. Commit: pending.
- [ ] **T5** · S1-S3 · Route: parent integration · Reconcile shared models/routes/navigation/error handling, update runtime documentation, and verify TypeScript, Angular build, backend regression, and Docker HTTP flows where available. Commit: pending.

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
- **Risk:** item 2 (authentication and role boundaries) and item 3 (shared frontend HTTP contracts and existing operational flows). Each work unit requires focused verification and an independent verifier before closure.
