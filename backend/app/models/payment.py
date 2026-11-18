from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Payment(Base):
    """Un pago de mensualidad. Nunca se borra: un error se anula y queda auditable."""

    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_payments_idempotency_key"),
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
        CheckConstraint(
            "payment_method IN ('EFECTIVO', 'TRANSFERENCIA', 'QR')",
            name="ck_payment_method",
        ),
        CheckConstraint(
            "status IN ('REGISTERED', 'ANNULLED')",
            name="ck_payment_status",
        ),
        CheckConstraint(
            "(status = 'REGISTERED' AND annulled_at IS NULL AND annulled_by IS NULL)"
            " OR (status = 'ANNULLED' AND annulled_at IS NOT NULL"
            " AND annulled_by IS NOT NULL AND annulment_reason IS NOT NULL)",
            name="ck_payment_annulment_pair",
        ),
        CheckConstraint("coverage_end > coverage_start", name="ck_payment_coverage"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    membership_id: Mapped[int] = mapped_column(ForeignKey("memberships.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    coverage_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    coverage_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    previous_cutoff: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="REGISTERED")
    annulled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    annulled_by: Mapped[int | None] = mapped_column(ForeignKey("user_accounts.id"))
    annulment_reason: Mapped[str | None] = mapped_column(String(255))
    idempotency_key: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    vehicle: Mapped["Vehicle"] = relationship()
    client: Mapped["Client"] = relationship()
    membership: Mapped["Membership"] = relationship(foreign_keys=[membership_id])
