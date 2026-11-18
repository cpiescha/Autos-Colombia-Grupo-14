from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PaymentAudit(Base):
    __tablename__ = "payment_audits"
    __table_args__ = (
        CheckConstraint(
            "action IN ('CREATE', 'ANNUL')",
            name="ck_payment_audit_action",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    previous_state: Mapped[dict | None] = mapped_column(JSON)
    new_state: Mapped[dict] = mapped_column(JSON, nullable=False)


class ClientStatusAudit(Base):
    __tablename__ = "client_status_audits"
    __table_args__ = (
        CheckConstraint(
            "action IN ('INACTIVATE', 'REACTIVATE')",
            name="ck_client_status_audit_action",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(String(255))
