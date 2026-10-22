from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base
from app.models.enums import VehicleType


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    license_plate: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    type: Mapped[VehicleType] = mapped_column(
        Enum(VehicleType, name="vehicle_type"),
        nullable=False,
    )
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    color: Mapped[str] = mapped_column(String(40), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)

    client: Mapped["Client"] = relationship(back_populates="vehicles")
    memberships: Mapped[list["Membership"]] = relationship(back_populates="vehicle")
    stays: Mapped[list["ParkingStay"]] = relationship(back_populates="vehicle")

    @validates("license_plate")
    def normalize_license_plate(self, _key: str, value: str) -> str:
        return value.strip().upper()
