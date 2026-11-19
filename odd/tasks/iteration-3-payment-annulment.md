# Iteration 3 — Payment Annulment (T35)
Feature branch: `feat/i3-t35-payment-annulment`, stacked on completed T34 at `20ee6cb`.
Scope: administrator-only LIFO payment annulment, cutoff rollback, audit integrity, and focused verification; T36 remains separate.

## Specs

1. **S1 — User direction:** “continuemos con t35”.
2. **S2 — T35 contract:** “`PATCH /api/pagos/{id}/anular`, exclusivo de administrador, reversión de corte y conservación del registro”.
3. **S3 — Authorization:** Unauthenticated requests return `401`; operators return `403`; rejected requests leave payments, membership state, and audits unchanged.
4. **S4 — LIFO rollback:** Only the latest applied registered payment can be annulled. An intermediate or already annulled payment returns `409` without mutation.
5. **S5 — Membership restoration:** Annulment restores `current_cutoff_date`, `expires_at`, and `last_payment_id` to the predecessor payment state; repeated LIFO annulments step backward correctly.
6. **S6 — Reactivation rollback decision:** “A — Marcarla vencida sin migración”. When `previous_cutoff` is `NULL`, restore a `NULL` cutoff and an expired membership without adding a historical snapshot column.
7. **S7 — Atomic audit:** Payment annulment, membership rollback, and one `PaymentAudit(ANNUL)` are one transaction; persistence failure rolls everything back and leaves the session reusable.
8. **S8 — Public errors:** Preserve Spanish domain errors: `PAYMENT_NOT_FOUND`, `PAYMENT_ALREADY_ANNULLED`, and a stable `409` for attempting to annul a non-latest payment.

## Allowed edit surfaces

- `backend/app/services/payment_annulment.py`
- `backend/tests/test_payment_persistence.py`
- `backend/tests/test_payment_api.py`
- `odd/tasks/iteration-3-payment-annulment.md`

## Tasks

- [x] **T1** (`S2-S4`, inline, commit `7d363fd`): Add RED HTTP/service tests for authentication, role authorization, missing/already-annulled payments, and non-LIFO rejection with unchanged state.
- [x] **T2** (`S4-S7`, inline, commit `7d363fd`): Implement predecessor restoration, expired reactivation rollback, complete audit snapshots, and transactional rollback.
- [x] **T3** (`S2-S8`, inline, commit `7d363fd`): Prove successful and repeated LIFO annulment through the public API, including exact Spanish DTO/errors and no mutation on rejection.
- [x] **T4** (`S2-S8`, independent verification, commit `a0501cf`): Run focused payment, membership, persistence, cycle, and entry regressions; record independent verdicts.

Risk: item 1 — annulment changes persisted payment, membership eligibility, and audit state.
Risk: item 2 — administrator authorization protects a financial mutation boundary.
Risk: item 3 — T35 finalizes a public HTTP contract consumed by the frontend.

## Log

- **L1:** “continuemos con t35”
- **L2:** Exploration found an existing partial route/service and persistence model. The current service restored the cutoff but always cleared `last_payment_id`, allowed non-LIFO annulment, and lacked explicit rollback protection.
- **L3:** Architecture limits annulment to the latest applied payment. The user selected “A — Marcarla vencida sin migración” for a reactivation payment whose `previous_cutoff` is `NULL`; exact historical `expires_at` restoration is intentionally outside T35.
- **L4:** T1–T3 implemented; coverage S2, S3, S4, S5, S6, S7, S8. Before production edits, focused RED observed 6 failed / 25 passed: non-LIFO accepted, predecessor lost, incomplete audit snapshots, missing rollback on audit/commit failures, and an over-broad future-start NULL-cutoff test. The latter was corrected to historical reactivation because `expires_at > starts_at` forbids expiring a future-start membership without changing its start. Existing historical NULL-cutoff behavior was preserved, without migration.
- **L5:** GREEN: `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_payment_persistence.py tests/test_payment_api.py` — 31 passed. HTTP tests assert exact Spanish JSON and persisted snapshots; repeated LIFO restoration also skips an already-annulled newer payment and ignores payment-date ordering. Audit/commit fault injection verifies rollback and successful session reuse. Both authorization layers remain unchanged.
- **L6:** Proportional regression: `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_payment_api.py tests/test_membership_api.py tests/test_payment_registration.py tests/test_payment_persistence.py tests/test_membership_cycle.py tests/test_entry.py` — 81 passed. Both commands report the existing Starlette/AnyIO deprecation warning. T4 independent verification remains pending; no commit or push. PostgreSQL concurrency was not exercised by these SQLite tests.
- **L7:** T1–T3 were committed locally as `7d363fd`. The required independent T4 verifier failed before running any probe because its model quota was unavailable. Per the bounded verification policy, it was not retried or replaced. T4 remained open and publication stayed blocked.
- **L8:** The user explicitly authorized one new bounded T35/T4 verification attempt. That attempt also stopped during preparation before pytest because CodeGraph timed out (`Failed to call tool: Request timed out`). It executed zero tests, made no repository changes, and was not retried. Parent confirmed the branch remained clean. T4 and publication remain blocked; the failed setup attempt is preserved.
- **L9:** The parent-reported independent verification ran 81 tests successfully but rejected S4/S5: locking queries could reuse stale payment/membership identity-map attributes. Added a two-session service regression covering a newer applied payment and an already-annulled payment; both retain cached instances in session A while session B commits changes. Full persisted Payment, Membership, and PaymentAudit snapshots must remain unchanged on rejection. RED before production edits: `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_payment_persistence.py -k refreshes_cached` — 2 failed / 7 deselected, both showing incorrect persisted mutation. Added `populate_existing=True` to both locking queries, retaining PostgreSQL `FOR UPDATE`. GREEN with the same command — 2 passed / 7 deselected; exact 409 codes verified. Protects S4/S5 and audit/error invariants S7/S8.
- **L10:** Exact six-file regression: `cd backend && PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider tests/test_payment_api.py tests/test_membership_api.py tests/test_payment_registration.py tests/test_payment_persistence.py tests/test_membership_cycle.py tests/test_entry.py` — 83 passed (81 existing + 2 new), one existing Starlette/AnyIO deprecation warning. Tests use sequential sessions over SQLite, not PostgreSQL concurrent row locks. Post-commit `refresh()` low finding deliberately unchanged. T4 remains open for independent verification; no commit or push.
- **L11:** After CodeGraph was repaired, final independent verification passed S2-S8. It confirmed `populate_existing=True` on both locked queries before status/LIFO evaluation, retained PostgreSQL `FOR UPDATE`, reproduced both stale-session variants, and executed the exact regression once: `83 passed, 1 warning in 11.30s`. No high or critical findings remain. Residual risks are SQLite-only sequential coverage and the non-blocking post-commit `refresh()` behavior. The stale-state correction is commit `a0501cf`.
