from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Client,
    ClientStatusAudit,
    Membership,
    Payment,
    PaymentAudit,
    UserAccount,
    Vehicle,
)
from app.models.enums import ClientStatus
from app.services.membership_cycle import MembershipCycleService


PAYMENT_METHODS = {"EFECTIVO", "TRANSFERENCIA", "QR"}


class PaymentRegistrationError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class PaymentRegistrationService:
    """Register a payment and its membership/client effects atomically."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def register(
        self,
        *,
        vehicle_id: int,
        amount: Decimal,
        payment_method: str,
        idempotency_key: str,
        account: UserAccount,
        paid_at: datetime | None = None,
    ) -> Payment:
        clean_method = payment_method.strip().upper()
        clean_key = idempotency_key.strip()
        payment_time = paid_at or datetime.now(timezone.utc)
        self._validate(amount, clean_method, clean_key, payment_time)

        existing = self._payment_by_key(clean_key)
        if existing is not None:
            return self._authorized_replay(existing, account)

        try:
            vehicle = self._lock_vehicle(vehicle_id)
            if vehicle is None:
                raise PaymentRegistrationError(
                    404,
                    "VEHICLE_NOT_FOUND",
                    "El vehículo no existe.",
                )
            client = self._lock_client(vehicle.client_id)
            membership = self._lock_latest_membership(vehicle.id)
            if membership is None:
                raise PaymentRegistrationError(
                    404,
                    "MEMBERSHIP_NOT_FOUND",
                    "El vehículo no tiene una mensualidad registrada.",
                )

            previous_cutoff = membership.current_cutoff_date
            reactivating = client.status == ClientStatus.INACTIVE.value
            cycle = MembershipCycleService.calculate(
                None if reactivating else previous_cutoff,
                payment_time,
            )
            payment = Payment(
                vehicle_id=vehicle.id,
                client_id=client.id,
                membership_id=membership.id,
                amount=amount,
                payment_method=clean_method,
                paid_at=payment_time,
                coverage_start=cycle.coverage_start,
                coverage_end=cycle.new_cutoff,
                previous_cutoff=previous_cutoff,
                recorded_by=account.id,
                status="REGISTERED",
                idempotency_key=clean_key,
            )
            self.db.add(payment)
            self.db.flush()

            membership.current_cutoff_date = cycle.new_cutoff
            membership.expires_at = cycle.new_cutoff
            membership.last_payment_id = payment.id
            if membership.activated_at is None or reactivating:
                membership.activated_at = payment_time

            if reactivating:
                client.status = ClientStatus.ACTIVE.value
                client.reactivated_at = payment_time
                client.reactivated_by = account.id
                self.db.add(ClientStatusAudit(
                    client_id=client.id,
                    account_id=account.id,
                    action="REACTIVATE",
                    reason="Reactivación mediante registro de pago.",
                ))

            self.db.add(PaymentAudit(
                payment_id=payment.id,
                account_id=account.id,
                action="CREATE",
                previous_state={
                    "current_cutoff_date": _iso(previous_cutoff),
                    "client_status": (
                        ClientStatus.INACTIVE.value
                        if reactivating
                        else client.status
                    ),
                },
                new_state={
                    "status": "REGISTERED",
                    "current_cutoff_date": _iso(cycle.new_cutoff),
                    "client_status": client.status,
                },
            ))
            self.db.commit()
            return payment
        except IntegrityError:
            self.db.rollback()
            replay = self._payment_by_key(clean_key)
            if replay is not None:
                return self._authorized_replay(replay, account)
            raise
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _authorized_replay(payment: Payment, account: UserAccount) -> Payment:
        if payment.recorded_by != account.id:
            raise PaymentRegistrationError(
                409,
                "IDEMPOTENCY_CONFLICT",
                "La clave de idempotencia no está disponible.",
            )
        return payment

    def _payment_by_key(self, key: str) -> Payment | None:
        return self.db.scalar(select(Payment).where(Payment.idempotency_key == key))

    def _lock_vehicle(self, vehicle_id: int) -> Vehicle | None:
        query = select(Vehicle).where(Vehicle.id == vehicle_id)
        return self._execute_locked(query)

    def _lock_client(self, client_id: int) -> Client:
        query = select(Client).where(Client.id == client_id)
        client = self._execute_locked(query)
        if client is None:
            raise PaymentRegistrationError(
                404,
                "CLIENT_NOT_FOUND",
                "El cliente del vehículo no existe.",
            )
        return client

    def _lock_latest_membership(self, vehicle_id: int) -> Membership | None:
        query = (
            select(Membership)
            .where(Membership.vehicle_id == vehicle_id)
            .order_by(Membership.starts_at.desc(), Membership.id.desc())
            .limit(1)
        )
        return self._execute_locked(query)

    def _execute_locked(self, query):
        if self.db.get_bind().dialect.name == "postgresql":
            query = query.with_for_update()
        return self.db.execute(query).scalar_one_or_none()

    @staticmethod
    def _validate(
        amount: Decimal,
        payment_method: str,
        idempotency_key: str,
        paid_at: datetime,
    ) -> None:
        if amount <= 0 or payment_method not in PAYMENT_METHODS or not idempotency_key:
            raise PaymentRegistrationError(
                422,
                "INVALID_PAYMENT_DATA",
                "Los datos del pago no son válidos.",
            )
        if paid_at.tzinfo is None or paid_at.utcoffset() is None:
            raise PaymentRegistrationError(
                422,
                "INVALID_PAYMENT_DATA",
                "La fecha del pago debe incluir zona horaria.",
            )


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()
