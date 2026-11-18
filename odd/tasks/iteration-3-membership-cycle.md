# Iteration 3 — Membership Cycle Service (T33)
Feature branch: `feat/i3-t33-membership-cycle` from synchronized `camilo-backend`.
Scope: complete T33 only; T34 payment HTTP endpoints remain a separate work unit.

## Specs

1. **S1 — User direction:** “empecemos a avanzar por orden y tareas”.
2. **S2 — T33 deliverable:** “Servicio `MembershipCycleService` que calcula la nueva fecha de corte como corte anterior + 30 días y maneja primer pago”.
3. **S3 — T33 verification:** “Pruebas unitarias para anticipado, mora, día exacto y primer pago; cero regresiones en la validación de ingreso”.
4. **S4 — Cycle rules:** “La fecha del pago no desplaza la fecha de corte.”, “La nueva fecha de corte se calcula como fecha de corte anterior + 30 días.”, and “El primer pago de un cliente nuevo o reactivado fija la fecha de corte 30 días después del día del pago.”

## Allowed edit surfaces

- `backend/app/services/membership_cycle.py`
- `backend/tests/test_membership_cycle.py`
- `odd/tasks/iteration-3-membership-cycle.md`

## Tasks

- [x] **T1** (`S2-S4`, inline, commit pending): Add RED unit tests for advance, overdue, exact-day, and first-payment cycles.
- [x] **T2** (`S2-S4`, inline, commit pending): Implement `MembershipCycleService` with timezone-aware 30-day calculations.
- [x] **T3** (`S3`, inline, commit pending): Run focused tests and entry-validation regression tests; record evidence.

Risk: item 1 — membership cutoff calculations affect persisted access eligibility and must not advance from the wrong date.

## Log

- **L1:** “empecemos a avanzar por orden y tareas”
- **L2:** T33 is the first unblocked Camilo backend task after Paul merged T31–T32 into `main` via PR #24 (`7f3f159`).
- **L3:** RED observed: `pytest tests/test_membership_cycle.py -q` failed during collection because `app.services.membership_cycle` did not exist.
- **L4:** GREEN observed: the focused cycle suite passed `4 passed` after implementing the service.
- **L5:** Focused T33 plus entry regression passed: `19 passed, 1 warning` in 5.69s.
- **L6:** The full backend suite reached 51% plus additional tests with no reported failure, then exceeded the 30-second command limit; it was not retried.
- **L7:** An initial independent-verifier command query expired before execution; no test result was claimed from that attempt.
- **L8:** Independent verification then passed S1-S4. Exact focused command result: `19 passed, 1 warning` with no failures or skips. Reactivation caller integration remains outside T33 and is deferred to T34.
