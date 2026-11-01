from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.exceptions import PersistenceError
from app.db.operations import correct_parking_spot
from app.models.cell_correction import CellCorrection
from app.models.operator import Operator
from app.models.parking_spot import ParkingSpot


@dataclass(frozen=True)
class CellCorrectionResult:
    stay_id: int
    previous_spot_code: str
    new_spot_code: str
    operator_id: int
    corrected_at: datetime


class CellCorrectionError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class CellCorrectionRepository(Protocol):
    def transaction(self) -> AbstractContextManager[None]: ...

    def operator_exists(self, operator_id: int) -> bool: ...

    def find_spot_by_code(self, code: str) -> ParkingSpot | None: ...

    def correct_spot(
        self, stay_id: int, new_spot_id: int, operator_id: int
    ) -> CellCorrection: ...

    def spot_code(self, spot_id: int) -> str: ...


class SqlAlchemyCellCorrectionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def transaction(self) -> AbstractContextManager[None]:
        return self.session.begin()

    def operator_exists(self, operator_id: int) -> bool:
        statement = select(Operator.id).where(Operator.id == operator_id).limit(1)
        return self.session.scalar(statement) is not None

    def find_spot_by_code(self, code: str) -> ParkingSpot | None:
        statement = select(ParkingSpot).where(ParkingSpot.code == code).limit(1)
        return self.session.scalar(statement)

    def correct_spot(
        self, stay_id: int, new_spot_id: int, operator_id: int
    ) -> CellCorrection:
        return correct_parking_spot(
            self.session,
            stay_id=stay_id,
            new_spot_id=new_spot_id,
            operator_id=operator_id,
        )

    def spot_code(self, spot_id: int) -> str:
        spot = self.session.get(ParkingSpot, spot_id)
        if spot is None:
            raise RuntimeError("Correction references a missing parking spot.")
        return spot.code


class CellCorrectionService:
    def __init__(self, repository: CellCorrectionRepository) -> None:
        self.repository = repository

    def correct(
        self, stay_id: int, spot_code: str, operator_id: int
    ) -> CellCorrectionResult:
        normalized_spot_code = normalize_spot_code(spot_code)
        try:
            with self.repository.transaction():
                if not self.repository.operator_exists(operator_id):
                    raise CellCorrectionError(
                        422,
                        "OPERATOR_NOT_FOUND",
                        "El operario no está registrado.",
                    )

                new_spot = self.repository.find_spot_by_code(normalized_spot_code)
                if new_spot is None:
                    raise CellCorrectionError(
                        404,
                        "SPOT_NOT_FOUND",
                        "La celda indicada no existe.",
                    )

                correction = self.repository.correct_spot(
                    stay_id=stay_id,
                    new_spot_id=new_spot.id,
                    operator_id=operator_id,
                )
                previous_spot_code = self.repository.spot_code(
                    correction.previous_spot_id
                )

                return CellCorrectionResult(
                    stay_id=correction.parking_stay_id,
                    previous_spot_code=previous_spot_code,
                    new_spot_code=new_spot.code,
                    operator_id=correction.operator_id,
                    corrected_at=correction.corrected_at,
                )
        except PersistenceError as error:
            raise _persistence_error(error) from error
        except IntegrityError as error:
            raise CellCorrectionError(
                409,
                "CORRECTION_CONFLICT",
                "No fue posible confirmar la corrección por un conflicto de concurrencia.",
            ) from error


def normalize_spot_code(code: str) -> str:
    return code.strip().upper()


def _persistence_error(error: PersistenceError) -> CellCorrectionError:
    status_codes = {
        "STAY_NOT_FOUND": 404,
        "SPOT_NOT_FOUND": 404,
        "STAY_ALREADY_CLOSED": 409,
        "SAME_SPOT": 409,
        "SPOT_INCOMPATIBLE": 409,
        "SPOT_OCCUPIED": 409,
    }
    return CellCorrectionError(
        status_codes.get(error.code, 409),
        error.code,
        error.message,
    )
