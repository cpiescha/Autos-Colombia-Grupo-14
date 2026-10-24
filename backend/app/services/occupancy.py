from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.enums import SpotCategory
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
    comprobante: str | None = None


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
                Receipt.code,
            )
            .join(Vehicle, Vehicle.id == ParkingStay.vehicle_id)
            .join(ParkingSpot, ParkingSpot.id == ParkingStay.parking_spot_id)
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
                fecha_entrada=(
                    entered_at.replace(tzinfo=timezone.utc)
                    if entered_at.tzinfo is None
                    else entered_at
                ),
            )
            for stay_id, plate, spot_code, entered_at, receipt_code in self.db.execute(statement)
        ]

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
