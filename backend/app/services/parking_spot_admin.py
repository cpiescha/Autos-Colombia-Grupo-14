from dataclasses import dataclass

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import CellCorrection, ParkingSpot, ParkingStay, Vehicle
from app.models.enums import SpotCategory


class ParkingSpotAdminError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ParkingSpotView:
    id: int
    code: str
    category: SpotCategory
    active: bool
    plate: str | None
    has_history: bool

    @property
    def state(self) -> str:
        if not self.active:
            return "inactiva"
        return "ocupada" if self.plate is not None else "disponible"


def spot_code_exists_error() -> ParkingSpotAdminError:
    return ParkingSpotAdminError(
        409,
        "SPOT_CODE_EXISTS",
        "El código de celda ya está registrado.",
    )


def spot_not_found_error() -> ParkingSpotAdminError:
    return ParkingSpotAdminError(
        404,
        "SPOT_NOT_FOUND",
        "La celda no existe.",
    )


def spot_occupied_error() -> ParkingSpotAdminError:
    return ParkingSpotAdminError(
        409,
        "SPOT_OCCUPIED",
        "Una celda ocupada no se puede inactivar ni retirar.",
    )


class ParkingSpotAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_spots(self) -> list[ParkingSpotView]:
        return [self._view(spot) for spot in self.db.scalars(select(ParkingSpot).order_by(ParkingSpot.code))]

    def create_spot(self, code: str, category: SpotCategory) -> ParkingSpotView:
        if self.db.scalar(select(ParkingSpot.id).where(ParkingSpot.code == code)) is not None:
            raise spot_code_exists_error()

        spot = ParkingSpot(code=code, category=category, active=True)
        self.db.add(spot)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise spot_code_exists_error() from None
        self.db.refresh(spot)
        return self._view(spot)

    def change_state(self, spot_id: int, active: bool) -> ParkingSpotView:
        spot = self._spot_for_update(spot_id)
        if not active and self._is_occupied(spot.id):
            raise spot_occupied_error()
        spot.active = active
        self.db.commit()
        self.db.refresh(spot)
        return self._view(spot)

    def remove_spot(self, spot_id: int) -> ParkingSpotView | None:
        spot = self._spot_for_update(spot_id)
        if self._is_occupied(spot.id):
            raise spot_occupied_error()
        if self._has_history(spot.id):
            spot.active = False
            self.db.commit()
            self.db.refresh(spot)
            return self._view(spot)

        self.db.delete(spot)
        self.db.commit()
        return None

    def _spot_for_update(self, spot_id: int) -> ParkingSpot:
        spot = self.db.scalar(
            select(ParkingSpot)
            .where(ParkingSpot.id == spot_id)
            .with_for_update()
        )
        if spot is None:
            raise spot_not_found_error()
        return spot

    def _is_occupied(self, spot_id: int) -> bool:
        return bool(
            self.db.scalar(
                select(
                    exists().where(
                        ParkingStay.parking_spot_id == spot_id,
                        ParkingStay.exited_at.is_(None),
                    )
                )
            )
        )

    def _has_history(self, spot_id: int) -> bool:
        stay_history = self.db.scalar(
            select(exists().where(ParkingStay.parking_spot_id == spot_id))
        )
        correction_history = self.db.scalar(
            select(
                exists().where(
                    (CellCorrection.previous_spot_id == spot_id)
                    | (CellCorrection.new_spot_id == spot_id)
                )
            )
        )
        return bool(stay_history or correction_history)

    def _view(self, spot: ParkingSpot) -> ParkingSpotView:
        plate = self.db.scalar(
            select(Vehicle.license_plate)
            .join(ParkingStay, ParkingStay.vehicle_id == Vehicle.id)
            .where(
                ParkingStay.parking_spot_id == spot.id,
                ParkingStay.exited_at.is_(None),
            )
            .limit(1)
        )
        return ParkingSpotView(
            id=spot.id,
            code=spot.code,
            category=spot.category,
            active=spot.active,
            plate=plate,
            has_history=self._has_history(spot.id),
        )
