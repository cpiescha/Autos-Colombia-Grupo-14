from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Operator(Base):
    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    entry_stays: Mapped[list["ParkingStay"]] = relationship(
        back_populates="entry_operator",
        foreign_keys="ParkingStay.entry_operator_id",
    )
    exit_stays: Mapped[list["ParkingStay"]] = relationship(
        back_populates="exit_operator",
        foreign_keys="ParkingStay.exit_operator_id",
    )
    cell_corrections: Mapped[list["CellCorrection"]] = relationship(
        back_populates="operator"
    )
