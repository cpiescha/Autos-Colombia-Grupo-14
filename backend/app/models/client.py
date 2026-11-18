from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ClientStatus


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_client_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ClientStatus.ACTIVE.value,
        server_default=text("'ACTIVE'"),
    )
    inactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inactivated_by: Mapped[int | None] = mapped_column(ForeignKey("user_accounts.id"))
    inactivation_reason: Mapped[str | None] = mapped_column(String(255))
    reactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reactivated_by: Mapped[int | None] = mapped_column(ForeignKey("user_accounts.id"))

    vehicles: Mapped[list[Vehicle]] = relationship(back_populates="client")
