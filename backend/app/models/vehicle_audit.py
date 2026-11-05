from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VehicleAudit(Base):
    __tablename__ = "vehicle_audits"
    __table_args__ = (CheckConstraint("action IN ('CREATE', 'UPDATE', 'RETIRE')", name="ck_vehicle_audit_action"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("user_accounts.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    before_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
