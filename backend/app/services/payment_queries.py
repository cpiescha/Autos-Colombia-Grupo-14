from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Client, Membership, Payment, UserAccount, Vehicle
from app.services.vehicle_authorization import normalize_plate
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


class MembershipQueryService:
    """Read the latest membership per vehicle without changing payment state."""

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _query():
        latest_id = (
            select(Membership.id)
            .where(Membership.vehicle_id == Vehicle.id)
            .order_by(Membership.starts_at.desc(), Membership.id.desc())
            .limit(1)
            .correlate(Vehicle)
            .scalar_subquery()
        )
        return (
            select(Vehicle, Membership, Payment)
            .outerjoin(Membership, Membership.id == latest_id)
            .outerjoin(Payment, Payment.id == Membership.last_payment_id)
            .order_by(Vehicle.id)
        )

    def for_vehicle(self, plate: str):
        row = self.db.execute(
            self._query().where(Vehicle.license_plate == normalize_plate(plate))
        ).first()
        if row is None:
            raise PaymentQueryError(404, "VEHICLE_NOT_FOUND", "El vehículo no existe.")
        return row

    def for_client(self, client_id: int):
        if self.db.get(Client, client_id) is None:
            raise PaymentQueryError(404, "CLIENT_NOT_FOUND", "El cliente no existe.")
        return self.db.execute(
            self._query().where(Vehicle.client_id == client_id)
        ).all()

    def expiring(self, days: int):
        # Compare calendar-day offsets rather than adding unbounded user input
        # to a datetime (which can overflow).
        today = datetime.now(timezone.utc).date()
        rows = self.db.execute(
            self._query().where(Membership.current_cutoff_date.is_not(None))
        ).all()
        return [row for row in rows
                if 0 <= (row[1].current_cutoff_date.date() - today).days <= days]
