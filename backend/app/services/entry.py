from __future__ import annotations

import secrets
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import SpotCategory
from app.models.membership import Membership
from app.models.operator import Operator
from app.models.parking_spot import ParkingSpot
from app.models.parking_stay import ParkingStay
from app.models.receipt import Receipt
from app.models.vehicle import Vehicle
from app.services.vehicle_authorization import normalize_plate


@dataclass(frozen=True)
class EntryResult:
    stay_id: int
    plate: str
    spot_code: str
    receipt_code: str
    entered_at: datetime


class EntryError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class EntryRepository(Protocol):
    def transaction(self) -> AbstractContextManager[None]: ...

    def find_vehicle_for_update(self, plate: str) -> Vehicle | None: ...

    def operator_exists(self, operator_id: int) -> bool: ...

    def has_active_membership(self, vehicle_id: int, at: datetime) -> bool: ...

    def has_open_stay(self, vehicle_id: int) -> bool: ...

    def find_first_free_spot_for_update(
        self, category: SpotCategory
    ) -> ParkingSpot | None: ...

    def create_stay(
        self,
        vehicle_id: int,
        parking_spot_id: int,
        operator_id: int,
        entered_at: datetime,
    ) -> ParkingStay: ...

    def create_receipt(self, parking_stay_id: int, code: str) -> None: ...


class SqlAlchemyEntryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def transaction(self) -> AbstractContextManager[None]:
        return self.session.begin()

    def find_vehicle_for_update(self, plate: str) -> Vehicle | None:
        statement = (
            select(Vehicle)
            .where(Vehicle.license_plate == plate)
            .with_for_update()
        )
        return self.session.scalar(statement)

    def operator_exists(self, operator_id: int) -> bool:
        statement = select(Operator.id).where(Operator.id == operator_id).limit(1)
        return self.session.scalar(statement) is not None

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

    def find_first_free_spot_for_update(
        self, category: SpotCategory
    ) -> ParkingSpot | None:
        open_stay_for_spot = select(ParkingStay.id).where(
            ParkingStay.parking_spot_id == ParkingSpot.id,
            ParkingStay.exited_at.is_(None),
        )
        statement = (
            select(ParkingSpot)
            .where(
                ParkingSpot.category == category,
                ~exists(open_stay_for_spot),
            )
            .order_by(ParkingSpot.code)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        return self.session.scalar(statement)

    def create_stay(
        self,
        vehicle_id: int,
        parking_spot_id: int,
        operator_id: int,
        entered_at: datetime,
    ) -> ParkingStay:
        stay = ParkingStay(
            vehicle_id=vehicle_id,
            parking_spot_id=parking_spot_id,
            entry_operator_id=operator_id,
            entered_at=entered_at,
        )
        self.session.add(stay)
        self.session.flush()
        return stay

    def create_receipt(self, parking_stay_id: int, code: str) -> None:
        self.session.add(Receipt(parking_stay_id=parking_stay_id, code=code))


class EntryService:
    def __init__(self, repository: EntryRepository) -> None:
        self.repository = repository

    def create(self, plate: str, operator_id: int) -> EntryResult:
        entered_at = datetime.now(timezone.utc)
        try:
            with self.repository.transaction():
                normalized_plate = normalize_plate(plate)
                vehicle = self.repository.find_vehicle_for_update(normalized_plate)
                if vehicle is None:
                    raise EntryError(
                        404,
                        "VEHICLE_NOT_FOUND",
                        "El vehículo no está registrado.",
                    )

                if not self.repository.operator_exists(operator_id):
                    raise EntryError(
                        422,
                        "OPERATOR_NOT_FOUND",
                        "El operario no está registrado.",
                    )

                if not self.repository.has_active_membership(vehicle.id, entered_at):
                    raise EntryError(
                        409,
                        "MEMBERSHIP_NOT_CURRENT",
                        "La mensualidad no está vigente.",
                    )

                spot_category = self._spot_category_for(vehicle.type)
                if spot_category is None:
                    raise EntryError(
                        409,
                        "VEHICLE_TYPE_NOT_ALLOWED",
                        "El tipo de vehículo no está permitido.",
                    )

                if self.repository.has_open_stay(vehicle.id):
                    raise EntryError(
                        409,
                        "OPEN_STAY_EXISTS",
                        "El vehículo ya tiene una permanencia abierta.",
                    )

                spot = self.repository.find_first_free_spot_for_update(spot_category)
                if spot is None:
                    raise EntryError(
                        409,
                        "NO_COMPATIBLE_SPACE",
                        "No hay celdas disponibles para este tipo de vehículo.",
                    )

                stay = self.repository.create_stay(
                    vehicle_id=vehicle.id,
                    parking_spot_id=spot.id,
                    operator_id=operator_id,
                    entered_at=entered_at,
                )
                receipt_code = secrets.token_urlsafe(24)
                self.repository.create_receipt(stay.id, receipt_code)

                return EntryResult(
                    stay_id=stay.id,
                    plate=vehicle.license_plate,
                    spot_code=spot.code,
                    receipt_code=receipt_code,
                    entered_at=entered_at,
                )
        except IntegrityError as error:
            raise EntryError(
                409,
                "ENTRY_CONFLICT",
                "No fue posible confirmar la entrada por un conflicto de concurrencia.",
            ) from error

    @staticmethod
    def _spot_category_for(vehicle_type: object) -> SpotCategory | None:
        value = str(getattr(vehicle_type, "value", vehicle_type))
        if value == "MOTO":
            return SpotCategory.MOTO
        if value in {"CARRO", "CAMIONETA"}:
            return SpotCategory.AUTOMOVIL
        return None
