from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint("expires_at > starts_at", name="ck_membership_dates"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_cutoff_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.id", use_alter=True, name="fk_memberships_last_payment")
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    vehicle: Mapped["Vehicle"] = relationship(back_populates="memberships")
