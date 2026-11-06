from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, aliased

from app.models.cell_correction import CellCorrection
from app.models.enums import SpotCategory
from app.models.operator import Operator
from app.models.parking_spot import ParkingSpot
from app.models.parking_stay import ParkingStay
from app.models.receipt import Receipt
from app.models.vehicle import Vehicle


@dataclass(frozen=True)
class Celda:
    codigo: str
    categoria: str
    estado: str
    placa: str | None


@dataclass(frozen=True)
class MovimientoActivo:
    permanencia_id: int
    placa: str
    celda: str
    fecha_entrada: datetime
    operario_entrada: str
    comprobante: str | None = None


@dataclass(frozen=True)
class CorreccionHistorica:
    celda_anterior: str
    celda_nueva: str
    operario: str
    fecha_correccion: datetime


@dataclass(frozen=True)
class MovimientoHistorico:
    permanencia_id: int
    placa: str
    celda_final: str
    fecha_entrada: datetime
    fecha_salida: datetime
    comprobante: str | None
    operario_entrada: str
    operario_salida: str
    correcciones: list[CorreccionHistorica]


@dataclass(frozen=True)
class TotalesOcupacion:
    capacidad: int
    ocupadas: int
    disponibles: int


@dataclass(frozen=True)
class ReporteOcupacion:
    vehiculos_registrados: int
    vehiculos_presentes: int
    moto: TotalesOcupacion
    automovil: TotalesOcupacion
    total: TotalesOcupacion


def _with_timezone(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class OccupancyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_cells(self) -> list[Celda]:
        statement = (
            select(
                ParkingSpot.code,
                ParkingSpot.category,
                Vehicle.license_plate,
            )
            .outerjoin(
                ParkingStay,
                and_(
                    ParkingStay.parking_spot_id == ParkingSpot.id,
                    ParkingStay.exited_at.is_(None),
                ),
            )
            .outerjoin(Vehicle, Vehicle.id == ParkingStay.vehicle_id)
            .order_by(ParkingSpot.code)
        )
        return [
            Celda(
                codigo=code,
                categoria=category.value,
                estado="ocupada" if plate is not None else "disponible",
                placa=plate,
            )
            for code, category, plate in self.db.execute(statement)
        ]

    def list_active_movements(self) -> list[MovimientoActivo]:
        statement = (
            select(
                ParkingStay.id,
                Vehicle.license_plate,
                ParkingSpot.code,
                ParkingStay.entered_at,
                Operator.name,
                Receipt.code,
            )
            .join(Vehicle, Vehicle.id == ParkingStay.vehicle_id)
            .join(ParkingSpot, ParkingSpot.id == ParkingStay.parking_spot_id)
            .join(Operator, Operator.id == ParkingStay.entry_operator_id)
            .outerjoin(Receipt, Receipt.parking_stay_id == ParkingStay.id)
            .where(ParkingStay.exited_at.is_(None))
            .order_by(ParkingStay.entered_at, ParkingStay.id)
        )
        return [
            MovimientoActivo(
                permanencia_id=stay_id,
                placa=plate,
                celda=spot_code,
                comprobante=receipt_code,
                operario_entrada=operator_name,
                fecha_entrada=(
                    entered_at.replace(tzinfo=timezone.utc)
                    if entered_at.tzinfo is None
                    else entered_at
                ),
            )
            for stay_id, plate, spot_code, entered_at, operator_name, receipt_code in self.db.execute(statement)
        ]

    def list_movement_history(self) -> list[MovimientoHistorico]:
        entry_operator = aliased(Operator)
        exit_operator = aliased(Operator)
        statement = (
            select(
                ParkingStay.id,
                Vehicle.license_plate,
                ParkingSpot.code,
                ParkingStay.entered_at,
                ParkingStay.exited_at,
                Receipt.code,
                entry_operator.name,
                exit_operator.name,
            )
            .join(Vehicle, Vehicle.id == ParkingStay.vehicle_id)
            .join(ParkingSpot, ParkingSpot.id == ParkingStay.parking_spot_id)
            .join(entry_operator, entry_operator.id == ParkingStay.entry_operator_id)
            .join(exit_operator, exit_operator.id == ParkingStay.exit_operator_id)
            .outerjoin(Receipt, Receipt.parking_stay_id == ParkingStay.id)
            .where(ParkingStay.exited_at.is_not(None))
            .order_by(ParkingStay.exited_at.desc(), ParkingStay.id.desc())
        )
        rows = list(self.db.execute(statement))
        corrections_by_stay = self._historical_corrections([row[0] for row in rows])
        return [
            MovimientoHistorico(
                permanencia_id=stay_id,
                placa=plate,
                celda_final=spot_code,
                fecha_entrada=_with_timezone(entered_at),
                fecha_salida=_with_timezone(exited_at),
                comprobante=receipt_code,
                operario_entrada=entry_operator_name,
                operario_salida=exit_operator_name,
                correcciones=corrections_by_stay.get(stay_id, []),
            )
            for (
                stay_id,
                plate,
                spot_code,
                entered_at,
                exited_at,
                receipt_code,
                entry_operator_name,
                exit_operator_name,
            ) in rows
        ]

    def _historical_corrections(
        self, stay_ids: list[int]
    ) -> dict[int, list[CorreccionHistorica]]:
        if not stay_ids:
            return {}
        previous_spot = aliased(ParkingSpot)
        new_spot = aliased(ParkingSpot)
        correction_operator = aliased(Operator)
        statement = (
            select(
                CellCorrection.parking_stay_id,
                previous_spot.code,
                new_spot.code,
                correction_operator.name,
                CellCorrection.corrected_at,
            )
            .join(previous_spot, previous_spot.id == CellCorrection.previous_spot_id)
            .join(new_spot, new_spot.id == CellCorrection.new_spot_id)
            .join(correction_operator, correction_operator.id == CellCorrection.operator_id)
            .where(CellCorrection.parking_stay_id.in_(stay_ids))
            .order_by(CellCorrection.corrected_at, CellCorrection.id)
        )
        corrections_by_stay: dict[int, list[CorreccionHistorica]] = {}
        for stay_id, previous_code, new_code, operator_name, corrected_at in self.db.execute(statement):
            corrections_by_stay.setdefault(stay_id, []).append(
                CorreccionHistorica(
                    celda_anterior=previous_code,
                    celda_nueva=new_code,
                    operario=operator_name,
                    fecha_correccion=_with_timezone(corrected_at),
                )
            )
        return corrections_by_stay

    def occupancy_report(self) -> ReporteOcupacion:
        statement = (
            select(
                ParkingSpot.category,
                func.count(ParkingSpot.id),
                func.count(ParkingStay.id),
            )
            .outerjoin(
                ParkingStay,
                and_(
                    ParkingStay.parking_spot_id == ParkingSpot.id,
                    ParkingStay.exited_at.is_(None),
                ),
            )
            .where(ParkingSpot.active.is_(True))
            .group_by(ParkingSpot.category)
        )
        totals_by_category = {
            SpotCategory.MOTO: TotalesOcupacion(
                capacidad=0, ocupadas=0, disponibles=0
            ),
            SpotCategory.AUTOMOVIL: TotalesOcupacion(
                capacidad=0, ocupadas=0, disponibles=0
            ),
        }
        for category, total, occupied in self.db.execute(statement):
            totals_by_category[category] = TotalesOcupacion(
                capacidad=total,
                ocupadas=occupied,
                disponibles=total - occupied,
            )

        registered = self.db.scalar(select(func.count(Vehicle.id))) or 0
        moto = totals_by_category[SpotCategory.MOTO]
        automovil = totals_by_category[SpotCategory.AUTOMOVIL]
        present = moto.ocupadas + automovil.ocupadas
        return ReporteOcupacion(
            vehiculos_registrados=registered,
            vehiculos_presentes=present,
            moto=moto,
            automovil=automovil,
            total=TotalesOcupacion(
                capacidad=moto.capacidad + automovil.capacidad,
                ocupadas=moto.ocupadas + automovil.ocupadas,
                disponibles=moto.disponibles + automovil.disponibles,
            ),
        )
