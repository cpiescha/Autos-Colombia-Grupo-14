from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SpotCategory


class ParkingSpot(Base):
    __tablename__ = "parking_spots"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    category: Mapped[SpotCategory] = mapped_column(
        Enum(SpotCategory, name="spot_category"),
        nullable=False,
    )

    stays: Mapped[list["ParkingStay"]] = relationship(back_populates="parking_spot")
    previous_corrections: Mapped[list["CellCorrection"]] = relationship(
        back_populates="previous_spot",
        foreign_keys="CellCorrection.previous_spot_id",
    )
    new_corrections: Mapped[list["CellCorrection"]] = relationship(
        back_populates="new_spot",
        foreign_keys="CellCorrection.new_spot_id",
    )
