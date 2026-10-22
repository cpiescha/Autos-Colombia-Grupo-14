from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ParkingStay(Base):
    __tablename__ = "parking_stays"
    __table_args__ = (
        Index(
            "uq_open_stay_per_vehicle",
            "vehicle_id",
            unique=True,
            postgresql_where=text("exited_at IS NULL"),
        ),
        Index(
            "uq_open_stay_per_spot",
            "parking_spot_id",
            unique=True,
            postgresql_where=text("exited_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    parking_spot_id: Mapped[int] = mapped_column(
        ForeignKey("parking_spots.id"),
        nullable=False,
    )
    entry_operator_id: Mapped[int] = mapped_column(
        ForeignKey("operators.id"),
        nullable=False,
    )
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_operator_id: Mapped[int | None] = mapped_column(ForeignKey("operators.id"))
    exited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    vehicle: Mapped["Vehicle"] = relationship(back_populates="stays")
    parking_spot: Mapped["ParkingSpot"] = relationship(back_populates="stays")
    entry_operator: Mapped["Operator"] = relationship(
        back_populates="entry_stays",
        foreign_keys=[entry_operator_id],
    )
    exit_operator: Mapped["Operator | None"] = relationship(
        back_populates="exit_stays",
        foreign_keys=[exit_operator_id],
    )
    receipt: Mapped["Receipt"] = relationship(back_populates="parking_stay")
    cell_corrections: Mapped[list["CellCorrection"]] = relationship(
        back_populates="parking_stay"
    )
