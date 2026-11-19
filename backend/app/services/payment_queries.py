from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Payment, UserAccount
from app.models.enums import AccountRole


class PaymentQueryError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class PaymentQueryService:
    """Read payment history according to the authenticated account's scope."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_payments(self, account: UserAccount) -> list[Payment]:
        query = select(Payment)
        if account.role != AccountRole.ADMINISTRADOR:
            query = query.where(Payment.recorded_by == account.id)
        query = query.order_by(Payment.paid_at.desc(), Payment.id.desc())
        return list(self.db.scalars(query))

    def get_payment(self, payment_id: int, account: UserAccount) -> Payment:
        query = select(Payment).where(Payment.id == payment_id)
        if account.role != AccountRole.ADMINISTRADOR:
            query = query.where(Payment.recorded_by == account.id)
        payment = self.db.scalar(query)
        if payment is None:
            raise PaymentQueryError(
                404,
                "PAYMENT_NOT_FOUND",
                "El pago no existe.",
            )
        return payment
