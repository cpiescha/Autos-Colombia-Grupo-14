from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.exceptions import PersistenceError
from app.db.operations import close_stay_by_receipt
from app.models import Operator, ParkingSpot, ParkingStay, Receipt, Vehicle


@dataclass(frozen=True)
class ExitPreview:
    stay_id: int
    plate: str
    spot_code: str
    entered_at: datetime


@dataclass(frozen=True)
class ExitResult:
    stay_id: int
    plate: str
    spot_code: str
    entered_at: datetime
    exited_at: datetime


class ExitError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class ExitService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def preview(self, receipt_code: str) -> ExitPreview:
        statement = (
            select(ParkingStay, Vehicle, ParkingSpot, Receipt.used_at)
            .join(Receipt, Receipt.parking_stay_id == ParkingStay.id)
            .join(Vehicle, Vehicle.id == ParkingStay.vehicle_id)
            .join(ParkingSpot, ParkingSpot.id == ParkingStay.parking_spot_id)
            .where(Receipt.code == receipt_code.strip())
        )
        row = self.session.execute(statement).one_or_none()
        if row is None:
            raise ExitError(404, "RECEIPT_NOT_FOUND", "El comprobante no existe.")

        stay, vehicle, spot, used_at = row
        if used_at is not None:
            raise ExitError(
                409,
                "RECEIPT_ALREADY_USED",
                "El comprobante ya fue utilizado.",
            )
        if stay.exited_at is not None:
            raise ExitError(
                409,
                "STAY_ALREADY_CLOSED",
                "La permanencia ya está cerrada.",
            )

        return ExitPreview(
            stay_id=stay.id,
            plate=vehicle.license_plate,
            spot_code=spot.code,
            entered_at=stay.entered_at,
        )

    def confirm(self, receipt_code: str, operator_id: int) -> ExitResult:
        try:
            with self.session.begin():
                if self.session.get(Operator, operator_id) is None:
                    raise ExitError(
                        422,
                        "OPERATOR_NOT_FOUND",
                        "El operario no está registrado.",
                    )

                stay = close_stay_by_receipt(
                    self.session,
                    receipt_code,
                    operator_id,
                )
                vehicle = self.session.get(Vehicle, stay.vehicle_id)
                spot = self.session.get(ParkingSpot, stay.parking_spot_id)
                if vehicle is None or spot is None:
                    raise ExitError(
                        500,
                        "EXIT_CONFIRMATION_FAILED",
                        "No fue posible registrar la salida.",
                    )

                return ExitResult(
                    stay_id=stay.id,
                    plate=vehicle.license_plate,
                    spot_code=spot.code,
                    entered_at=stay.entered_at,
                    exited_at=stay.exited_at,
                )
        except PersistenceError as error:
            raise self._translate_persistence_error(error) from error

    @staticmethod
    def _translate_persistence_error(error: PersistenceError) -> ExitError:
        if error.code == "RECEIPT_NOT_FOUND":
            return ExitError(404, error.code, error.message)
        if error.code in {"RECEIPT_ALREADY_USED", "STAY_ALREADY_CLOSED"}:
            return ExitError(409, error.code, error.message)
        return ExitError(409, error.code, error.message)
