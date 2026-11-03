# T19 Authentication

Implement the Iteration 2 authentication boundary on `feat/i2-t19-authentication`. Keep role administration and authorization policy changes for T20–T22.

## Specs

1. **S1** — “sigamos con t19”
2. **S2** — “Login, validación de contraseña, sesión/token y obtención del usuario actual”
3. **S3** — “Credenciales válidas ingresan; inválidas o anuladas se rechazan”
4. **S4** — “`POST /api/auth/login` valida la contraseña y devuelve un token firmado de duración limitada.”
5. **S5** — “El token identifica la cuenta, pero FastAPI vuelve a consultar que siga activa antes de autorizar la operación.”
6. **S6** — “No se implementan refresh tokens, recuperación por correo ni OAuth en esta entrega.”

## Tasks

- [x] **T1** · S2-S6 · Route: parent inline · Added behavior-first authentication tests and observed RED. Evidence: six tests failed against missing `/api/auth/*` routes with `404`. Commit: `6af4dcd`.
- [x] **T2** · S2-S6 · Route: parent inline · Implemented password verification, signed access tokens, current-account resolution, and `/api/auth/*`. Evidence: eight focused tests pass after security hardening. Commit: `6af4dcd`.
- [x] **T3** · S2-S6 · Route: parent inline · Added bcrypt/PyJWT, authentication environment configuration, Compose wiring, and runtime documentation. Evidence: dependency installation and explicit-secret Compose validation pass. Commit: `6af4dcd`.
- [x] **T4** · S1-S6 · Route: independent verifier for security risk · Completed focused, regression, Docker/PostgreSQL, configuration, and independent security verification; corrected the verifier's high finding. Commit: `6af4dcd`.

## Log

- **L1** — User request (original): "sigamos con t19"
- **L2** — Referenced T19 source: `docs/PLAN_DESARROLLO_GITHUB.md` defines login, password validation, session/token, current-user retrieval, and rejection of invalid or inactive accounts.
- **L3** — Security boundary: the token carries only account identity; every protected request reloads the account and rejects missing, invalid, expired, or inactive identity with `401`. T20–T22 will add role administration and protect the existing business endpoints.
- **L4** — Delivery strategy: one backend authentication work-unit commit with tests, dependencies, configuration, and docs. Work remains on the feature branch until publication is explicitly authorized.
- **L5** — RED: `.venv/Scripts/python.exe -m pytest -q tests/test_auth.py` produced 6 failures. Login, current-user, and logout requests returned `404`; no authentication implementation existed.
- **L6** — GREEN focused verification: seven tests cover valid login, invalid password with unchanged account state, inactive-account rejection, invalid token, expired token, active-account reload on every request, and authenticated logout. All 7 passed.
- **L7** — The token contains only account identity plus `iat`/`exp`; `GET /api/auth/me` and logout reload the account and reject an inactive account. `AUTH_SECRET` requires 32+ characters and only `HS256` is admitted. The frontend remains simulated until T25.
- **L8** — Self-verification: focused authentication tests passed 7/7; the complete backend suite passed 68/68 with one Starlette/anyio deprecation warning; `docker compose config --quiet`, `git diff --check`, `pip check`, and Python compileall passed.
- **L9** — Isolated Docker/PostgreSQL verification built all three services with a fresh named volume. Seeded `admin` login returned a signed bearer token, `/api/auth/me` returned the same active administrator, an invalid/inactive-style login returned `401`, and the isolated project plus volume were removed afterward.
- **L10** — Independent security verification found the public Compose fallback for `AUTH_SECRET` unsafe for shared deployment. Added a RED/GREEN regression check, removed the fallback, made Compose fail when `AUTH_SECRET` is absent, and updated README setup instructions. Focused authentication tests now pass 8/8.
- **L11** — Final verification: complete backend suite passed 69/69 with one Starlette/anyio deprecation warning; Compose accepts an explicit 32+ character secret and rejects a missing secret; `git diff --check`, `pip check`, compileall, static response/claim checks, and isolated Docker/PostgreSQL login + `/me` passed.
- **L12** — Review workload: the cohesive authentication boundary is approximately 500 authored lines including 235 lines of behavior-first tests and the ODD evidence. It remains one security work unit because splitting tests, token validation, endpoints, and configuration would produce commits that are not independently safe or executable.
- **L13** — Native review was due for the exact committed range `f9cb4fec9838b32ef708b8eeca3c411613310699..6af4dcd`, but START failed before lineage creation in the provider candidate-view `git worktree` step. No native verdict or authority was created; the independent security verifier and functional checks remain the available proof.
- **Risk:** item 2 (authentication, credentials, signed tokens, and identity boundary) and item 5 (new runtime dependencies/configuration). Mitigation: fail-closed secret configuration, HS256 allowlist, required JWT claims, database account reload, RED/GREEN tests, full regression suite, isolated PostgreSQL runtime check, and one independent security verification pass.
