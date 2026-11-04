# T21 Cell Administration

Implement administrator-only parking-spot management on `camilo-backend`, while authenticated operators can consult cells. Inactive cells must remain historical but must never be assigned or selected for correction.

## Specs

1. **S1** — “listo ahora sigamos con la tarea 21”
2. **S2** — “API administrativa de celdas y adaptación de asignación/corrección”
3. **S3** — “Solo administrador modifica; celdas anuladas nunca se asignan”
4. **S4** — “Una celda inactiva no se asigna.”
5. **S5** — “Una celda ocupada no se puede anular.”
6. **S6** — “El código no se duplica.”

## Tasks

- [x] **T1** · S2-S6 · Route: parent inline · Added RED public-interface tests for authenticated listing, administrator-only creation/state/removal, duplicate and occupied-cell rejection, and unchanged state after rejection. Evidence: `tests/test_cell_admin.py` failed 6/6 against the missing contract (`405`, `404`, and incomplete list shape). Commit: `b4d2b25`.
- [x] **T2** · S2-S6 · Route: parent inline · Implemented parking-spot schemas, service, authenticated API routes, stable errors, normalized unique codes, occupied-cell protection, reversible state, physical removal without history, and history-preserving logical removal. Evidence: T21 API tests passed 11/11 after correction. Commit: `b4d2b25`.
- [x] **T3** · S3-S5 · Route: parent inline · Excluded inactive cells from automatic entry assignment, correction targets, and active capacity while preserving historical visibility in the administrative listing. Evidence: focused cell/entry/correction/occupancy suite passed 46/46. Commit: `b4d2b25`.
- [x] **T4** · S1-S6 · Route: independent verifier for items 1 and 3 · Ran focused tests, full backend regression, frontend build, structural checks, one independent review, and isolated Docker/PostgreSQL verification. The verifier found corrected-away history was omitted; the defect was reproduced and fixed. Evidence: focused 46/46 and full backend 89/89 passed; Angular build passed with the existing budget warning; isolated PostgreSQL 16 API checks passed; native review failed before lineage creation in candidate-view worktree preparation. Commit: `b4d2b25` plus runtime evidence commit.
- [x] **T5** · S1-S6 · Route: parent inline · Updated README/contract evidence, committed and pushed the verified work directly on `camilo-backend`, and confirmed the local/remote revision. Commits: `b4d2b25`, `de592cb`, and final publication evidence commit.

## Log

- **L1** — User request (original): "listo ahora sigamos con la tarea 21"
- **L2** — Source contract: `docs/PLAN_DESARROLLO_GITHUB.md`, `docs/PRD_Autos_Colombia_Iteracion_2.md`, and `docs/ARQUITECTURA_TECNICA_AUTOS_COLOMBIA.md` define T21 as administrator-only cell mutation, authenticated consultation, occupied-cell rejection, history preservation, and exclusion of inactive cells from assignment/correction.
- **L3** — Starting state: T18 already supplies `parking_spots.active` and persistence protections; T19/T20 supply authentication and the administrator guard. Existing Iteration 1 `/api/celdas` is unauthenticated and does not represent inactive state; entry and correction queries do not yet filter `active`.
- **L4** — RED observed: `.venv/Scripts/python.exe -m pytest -q tests/test_cell_admin.py` exited 1 with six failures. Listing lacked ID/history/inactive state, mutation routes returned `404`/`405`, and no T21 authorization or business behavior existed.
- **L5** — GREEN API: authenticated administrators and operators can list cells; only administrators can create, change state, or remove. Duplicate codes and occupied-cell mutations return `409` without state changes. Removing a historical cell inactivates it; removing an unused cell deletes it.
- **L6** — RED/GREEN operational rules: focused entry, correction, and occupancy tests first failed because inactive cells could be selected or counted; after adding active filters and `SPOT_INACTIVE`, the combined focused suite passed 41/41.
- **L7** — Independent verifier blocked the first candidate because history detection only inspected a cell's current `ParkingStay`; a corrected-away cell remains referenced by `CellCorrection.previous_spot_id` and could be physically deleted or fail with an integrity error. Added a reproducing RED case, expanded history detection to both stay and correction references, and restored GREEN.
- **L8** — Post-correction verification: focused T21/entry/correction/occupancy suite passed 46/46; complete backend suite passed 89/89 with one existing Starlette/anyio deprecation warning; Angular production build passed with the existing bundle-budget warning; Compose configuration, compileall, pip check, and `git diff --check` passed. Live PostgreSQL execution was unavailable because Docker Desktop was stopped.
- **L9** — Work-unit commit `b4d2b25` contains T21 API behavior, operational active-cell filters, tests, README, and ODD evidence. The 803-line commit exceeds the nominal review target because it includes 423 lines of behavior-first API/regression tests and one cohesive shared-contract change that is not safely executable if split from its tests and inactive-cell protections.
- **L10** — Published T21 through `de592cb`; fetch verification confirmed local and `origin/camilo-backend` at `de592cb8f873cb37ddaeb36950facc6ec781c16a` before the final evidence-only commit.
- **L11** — After Docker Desktop became available, rebuilt the primary stack successfully and ran an isolated Compose project against PostgreSQL 16 with a temporary volume and alternate ports. Verified health, administrator/operator login, unauthenticated `401`, operator mutation `403`, 80 seeded cells, normalized creation, duplicate `409`, inactive-capacity exclusion, inactive-correction `409` with unchanged movements, occupied-cell `409`, and physical removal of an unused cell. The isolated project and volume were removed automatically; the primary database was not modified.
- **Risk:** item 1 (cell state affects persisted capacity/history) and item 3 (shared `/api/celdas`, entry allocation, correction, and occupancy contracts). Verification must cover rejected writes leaving data unchanged and regression of existing flows.
