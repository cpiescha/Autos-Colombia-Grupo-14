# Iteration 3 — Payment API (T34)
Feature branch: `feat/i3-t34-payment-api`, stacked on completed T33.
Scope: payment registration and read-only payment/membership queries; annulment remains T35 and client lifecycle remains T36.

## Specs

1. **S1 — User direction:** “empecemos a avanzar por orden y tareas”.
2. **S2 — T34 contract:** “API `POST /api/pagos`, `GET /api/pagos`, `GET /api/pagos/{id}`, `GET /api/mensualidades/*` con autorización y auditoría”.
3. **S3 — T34 verification:** “Operador registra y consulta; administrador también; responsable derivado de sesión”.
4. **S4 — Payment consistency:** “El registro de un pago, la actualización de la fecha de corte y la reactivación del cliente deben ejecutarse en una sola transacción. Ante error, no debe quedar un pago sin vigencia actualizada ni una vigencia modificada sin pago.”
5. **S5 — Idempotency:** “si el frontend reintenta un pago por un problema de red, el backend debe reconocer el mismo intento dentro de una ventana corta y evitar duplicar el registro”.
6. **S6 — Membership queries:** “La consulta devuelve fecha de corte, estado vigente o vencido y fecha del último pago.”
7. **S7 — Membership selection decision:** “Usar la más reciente (recomendado)”.
8. **S8 — Idempotency decision:** “Devolver el pago original (recomendado)”.
9. **S9 — Activation decision:** “Solo primer pago o reactivación (recomendado)”.

## Allowed edit surfaces

- `backend/app/services/payment_registration.py`
- `backend/app/services/payment_queries.py`
- `backend/app/api/payments.py`
- `backend/app/api/memberships.py`
- `backend/app/schemas/payment.py`
- `backend/app/schemas/membership.py`
- `backend/app/main.py`
- `backend/tests/test_payment_registration.py`
- `backend/tests/test_payment_api.py`
- `backend/tests/test_membership_api.py`
- `odd/tasks/iteration-3-payment-api.md`

## Tasks

- [x] **T1** (`S2-S5`, `S7-S9`, inline, commit pending): Add RED service tests and implement atomic payment registration using `MembershipCycleService`.
- [~] **T2** (`S2-S3`, inline, commit pending): Add `POST /api/pagos` with authenticated operator/admin identity and idempotency handling.
- [ ] **T3** (`S2-S3`, inline, commit pending): Add payment list/detail queries and DTOs.
- [ ] **T4** (`S2`, `S6`, inline, commit pending): Add vehicle/client/expiring membership queries.
- [ ] **T5** (`S3-S6`, independent verification, commit pending): Run focused API, entry, persistence, and authorization regressions; record evidence.

Risk: item 1 — payment registration atomically changes persisted money/audit records and access eligibility.
Risk: item 3 — T34 adds public HTTP contracts consumed by the frontend.

## Log

- **L1:** “empecemos a avanzar por orden y tareas”
- **L2:** T33 completed in commits `a5f3f21` and `e32ff11`; T34 starts as a separate stacked work unit.
- **L3:** User selected the most recent membership, permanent same-key replay returning the original payment, and `activated_at` updates only for first payment or reactivation.
- **L4:** T1 RED observed because `app.services.payment_registration` did not exist.
- **L5:** T1 GREEN passed `4 passed`; focused registration, cycle, and persistence regression passed `12 passed`.
