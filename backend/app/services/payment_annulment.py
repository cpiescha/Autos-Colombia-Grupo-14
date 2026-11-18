from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Membership, Payment, PaymentAudit, UserAccount
from app.models.enums import AccountRole


class PaymentAnnulmentError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class PaymentAnnulmentService:
    """Anula un pago y devuelve la mensualidad al corte anterior.

    El cálculo del corte nuevo al registrar un pago lo hace MembershipCycleService.
    Aquí solo se revierte lo que ese pago había dejado guardado en previous_cutoff.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def annul(self, payment_id: int, account: UserAccount, reason: str) -> Payment:
        if account.role != AccountRole.ADMINISTRADOR:
            raise PaymentAnnulmentError(
                403,
                "FORBIDDEN",
                "Solo el administrador puede anular un pago.",
            )
        clean_reason = reason.strip()
        if not clean_reason:
            raise PaymentAnnulmentError(
                422,
                "INVALID_PAYMENT_DATA",
                "La anulación requiere un motivo.",
            )

        payment = self._lock_payment(payment_id)
        if payment is None:
            raise PaymentAnnulmentError(404, "PAYMENT_NOT_FOUND", "El pago no existe.")
        if payment.status == "ANNULLED":
            raise PaymentAnnulmentError(
                409,
                "PAYMENT_ALREADY_ANNULLED",
                "El pago ya está anulado.",
            )

        membership = self._lock_membership(payment.membership_id)
        previous_state = {
            "status": payment.status,
            "current_cutoff_date": _iso(membership.current_cutoff_date),
        }
        membership.current_cutoff_date = payment.previous_cutoff
        membership.expires_at = payment.previous_cutoff or (
            membership.starts_at + timedelta(seconds=1)
        )
        if membership.last_payment_id == payment.id:
            membership.last_payment_id = None

        payment.status = "ANNULLED"
        payment.annulled_by = account.id
        payment.annulment_reason = clean_reason
        payment.annulled_at = _now(self.db)
        self.db.add(PaymentAudit(
            payment_id=payment.id,
            account_id=account.id,
            action="ANNUL",
            previous_state=previous_state,
            new_state={
                "status": "ANNULLED",
                "current_cutoff_date": _iso(membership.current_cutoff_date),
                "reason": clean_reason,
            },
        ))
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def _lock_payment(self, payment_id: int) -> Payment | None:
        query = select(Payment).where(Payment.id == payment_id)
        if self.db.get_bind().dialect.name == "postgresql":
            query = query.with_for_update()
        return self.db.execute(query).scalar_one_or_none()

    def _lock_membership(self, membership_id: int) -> Membership:
        query = select(Membership).where(Membership.id == membership_id)
        if self.db.get_bind().dialect.name == "postgresql":
            query = query.with_for_update()
        return self.db.execute(query).scalar_one()


def _iso(value) -> str | None:
    return None if value is None else value.isoformat()


def _now(db: Session):
    from datetime import datetime, timezone

    del db
    return datetime.now(timezone.utc)
