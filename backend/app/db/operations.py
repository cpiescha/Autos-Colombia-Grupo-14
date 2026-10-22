from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.exceptions import PersistenceError
from app.models import CellCorrection, ParkingSpot, ParkingStay, Receipt, Vehicle
from app.models.enums import SpotCategory, VehicleType


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _spot_compatible(vehicle_type: VehicleType, category: SpotCategory) -> bool:
    if vehicle_type is VehicleType.MOTO:
        return category is SpotCategory.MOTO
    return category is SpotCategory.AUTOMOVIL


def close_stay_by_receipt(
    session: Session,
    receipt_code: str,
    exit_operator_id: int,
    exited_at: datetime | None = None,
) -> ParkingStay:
    """Cierra la permanencia y marca el comprobante como usado en la misma transacción.

    La celda queda libre al dejar de existir una permanencia abierta.
    El caller abre y confirma la transacción.
    """
    code = receipt_code.strip()
    closed_at = exited_at or _now()

    receipt = session.execute(
        select(Receipt).where(Receipt.code == code).with_for_update()
    ).scalar_one_or_none()
    if receipt is None:
        raise PersistenceError("RECEIPT_NOT_FOUND", "El comprobante no existe.")
    if receipt.used_at is not None:
        raise PersistenceError(
            "RECEIPT_ALREADY_USED",
            "El comprobante ya fue utilizado.",
        )

    stay = session.execute(
        select(ParkingStay)
        .where(ParkingStay.id == receipt.parking_stay_id)
        .with_for_update()
    ).scalar_one_or_none()
    if stay is None:
        raise PersistenceError("STAY_NOT_FOUND", "No existe la permanencia asociada.")
    if stay.exited_at is not None:
        raise PersistenceError(
            "STAY_ALREADY_CLOSED",
            "La permanencia ya está cerrada.",
        )

    stay.exit_operator_id = exit_operator_id
    stay.exited_at = closed_at
    receipt.used_at = closed_at
    session.flush()
    return stay


def correct_parking_spot(
    session: Session,
    stay_id: int,
    new_spot_id: int,
    operator_id: int,
    corrected_at: datetime | None = None,
) -> CellCorrection:
    """Cambia la celda de una permanencia abierta y deja auditoría atómica."""
    stay = session.execute(
        select(ParkingStay)
        .options(selectinload(ParkingStay.vehicle))
        .where(ParkingStay.id == stay_id)
        .with_for_update()
    ).scalar_one_or_none()
    if stay is None:
        raise PersistenceError("STAY_NOT_FOUND", "No existe el movimiento.")
    if stay.exited_at is not None:
        raise PersistenceError(
            "STAY_ALREADY_CLOSED",
            "No se puede corregir una permanencia cerrada.",
        )
    if stay.parking_spot_id == new_spot_id:
        raise PersistenceError(
            "SAME_SPOT",
            "La celda nueva debe ser distinta a la asignada.",
        )

    new_spot = session.execute(
        select(ParkingSpot).where(ParkingSpot.id == new_spot_id).with_for_update()
    ).scalar_one_or_none()
    if new_spot is None:
        raise PersistenceError("SPOT_NOT_FOUND", "La celda indicada no existe.")

    vehicle = stay.vehicle or session.get(Vehicle, stay.vehicle_id)
    if vehicle is None or not _spot_compatible(vehicle.type, new_spot.category):
        raise PersistenceError(
            "SPOT_INCOMPATIBLE",
            "La celda no es compatible con el tipo de vehículo.",
        )

    occupied = session.execute(
        select(ParkingStay.id)
        .where(
            ParkingStay.parking_spot_id == new_spot_id,
            ParkingStay.exited_at.is_(None),
        )
        .with_for_update()
    ).scalar_one_or_none()
    if occupied is not None:
        raise PersistenceError(
            "SPOT_OCCUPIED",
            "La celda ya pertenece a otra permanencia abierta.",
        )

    previous_spot_id = stay.parking_spot_id
    correction = CellCorrection(
        parking_stay_id=stay.id,
        previous_spot_id=previous_spot_id,
        new_spot_id=new_spot_id,
        operator_id=operator_id,
        corrected_at=corrected_at or _now(),
    )
    stay.parking_spot_id = new_spot_id
    session.add(correction)
    session.flush()
    return correction
