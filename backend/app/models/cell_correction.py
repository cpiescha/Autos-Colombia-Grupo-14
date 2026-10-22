from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CellCorrection(Base):
    __tablename__ = "cell_corrections"
    __table_args__ = (
        CheckConstraint(
            "previous_spot_id <> new_spot_id",
            name="ck_correction_different_spots",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    parking_stay_id: Mapped[int] = mapped_column(
        ForeignKey("parking_stays.id"),
        nullable=False,
    )
    previous_spot_id: Mapped[int] = mapped_column(
        ForeignKey("parking_spots.id"),
        nullable=False,
    )
    new_spot_id: Mapped[int] = mapped_column(
        ForeignKey("parking_spots.id"),
        nullable=False,
    )
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id"), nullable=False)
    corrected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    parking_stay: Mapped["ParkingStay"] = relationship(back_populates="cell_corrections")
    previous_spot: Mapped["ParkingSpot"] = relationship(
        back_populates="previous_corrections",
        foreign_keys=[previous_spot_id],
    )
    new_spot: Mapped["ParkingSpot"] = relationship(
        back_populates="new_corrections",
        foreign_keys=[new_spot_id],
    )
    operator: Mapped["Operator"] = relationship(back_populates="cell_corrections")
