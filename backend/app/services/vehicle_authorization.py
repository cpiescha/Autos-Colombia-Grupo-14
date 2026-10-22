from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.models.parking_stay import ParkingStay
from app.models.vehicle import Vehicle


PERMITTED_VEHICLE_TYPES = {"MOTO", "CARRO", "CAMIONETA"}
EXPIRED_MEMBERSHIP_REASON = "La mensualidad no está vigente."
DISALLOWED_VEHICLE_TYPE_REASON = "El tipo de vehículo no está permitido."
OPEN_STAY_REASON = "El vehículo ya tiene una permanencia abierta."


def normalize_plate(plate: str) -> str:
    return plate.strip().upper()


class VehicleRepository(Protocol):
    def find_by_plate(self, plate: str) -> Vehicle | None: ...

    def has_active_membership(self, vehicle_id: int, at: datetime) -> bool: ...

    def has_open_stay(self, vehicle_id: int) -> bool: ...


class SqlAlchemyVehicleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_plate(self, plate: str) -> Vehicle | None:
        statement = select(Vehicle).where(Vehicle.license_plate == plate)
        return self.session.scalar(statement)

    def has_active_membership(self, vehicle_id: int, at: datetime) -> bool:
        statement = (
            select(Membership.id)
            .where(
                Membership.vehicle_id == vehicle_id,
                Membership.starts_at <= at,
                Membership.expires_at >= at,
            )
            .limit(1)
        )
        return self.session.scalar(statement) is not None

    def has_open_stay(self, vehicle_id: int) -> bool:
        statement = (
            select(ParkingStay.id)
            .where(
                ParkingStay.vehicle_id == vehicle_id,
                ParkingStay.exited_at.is_(None),
            )
            .limit(1)
        )
        return self.session.scalar(statement) is not None


@dataclass(frozen=True)
class VehicleAuthorization:
    vehicle: Vehicle
    vehicle_type: str
    membership_active: bool
    authorized: bool
    rejection_reason: str | None


class VehicleAuthorizationService:
    def __init__(self, repository: VehicleRepository) -> None:
        self.repository = repository

    def lookup(
        self, plate: str, now: datetime | None = None
    ) -> VehicleAuthorization | None:
        vehicle = self.repository.find_by_plate(normalize_plate(plate))
        if vehicle is None:
            return None

        checked_at = now or datetime.now(timezone.utc)
        vehicle_type = self._vehicle_type_value(vehicle.type)
        membership_active = self.repository.has_active_membership(vehicle.id, checked_at)
        has_open_stay = self.repository.has_open_stay(vehicle.id)
        rejection_reason = self._rejection_reason(
            membership_active=membership_active,
            vehicle_type=vehicle_type,
            has_open_stay=has_open_stay,
        )

        return VehicleAuthorization(
            vehicle=vehicle,
            vehicle_type=vehicle_type,
            membership_active=membership_active,
            authorized=rejection_reason is None,
            rejection_reason=rejection_reason,
        )

    @staticmethod
    def _vehicle_type_value(vehicle_type: object) -> str:
        return str(getattr(vehicle_type, "value", vehicle_type))

    @staticmethod
    def _rejection_reason(
        membership_active: bool, vehicle_type: str, has_open_stay: bool
    ) -> str | None:
        if not membership_active:
            return EXPIRED_MEMBERSHIP_REASON
        if vehicle_type not in PERMITTED_VEHICLE_TYPES:
            return DISALLOWED_VEHICLE_TYPE_REASON
        if has_open_stay:
            return OPEN_STAY_REASON
        return None
