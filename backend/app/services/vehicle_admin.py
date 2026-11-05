from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Client, UserAccount, Vehicle, VehicleAudit
from app.schemas.vehicle import VehicleResponse, VehicleWriteRequest


def vehicle_state(vehicle: Vehicle) -> dict:
    return dict(id=vehicle.id, placa=vehicle.license_plate, tipo=vehicle.type.value,
                marca=vehicle.brand, modelo=vehicle.model, color=vehicle.color,
                cliente_id=vehicle.client_id, activo=vehicle.active)


class VehicleAdminService:
    def __init__(self, db: Session):
        self.db = db

    def write(self, account: UserAccount, data: VehicleWriteRequest | None = None,
              plate: str | None = None) -> VehicleResponse:
        vehicle = None
        before = None
        if plate is not None:
            vehicle = self.db.scalar(select(Vehicle).where(
                Vehicle.license_plate == plate.strip().upper()).with_for_update())
            if vehicle is None:
                raise HTTPException(404, 'Vehículo no registrado.')
            if not vehicle.active:
                raise HTTPException(409, 'El vehículo está retirado.')
            before = vehicle_state(vehicle)
        if data is not None:
            if self.db.get(Client, data.cliente_id) is None:
                raise HTTPException(422, 'Cliente no registrado.')
            duplicate = self.db.scalar(select(Vehicle).where(Vehicle.license_plate == data.placa))
            if duplicate is not None and duplicate is not vehicle:
                raise HTTPException(409, 'La placa ya está registrada.')
        action = 'CREATE' if vehicle is None else ('RETIRE' if data is None else 'UPDATE')
        try:
            if vehicle is None:
                vehicle = Vehicle(active=True)
                self.db.add(vehicle)
            if data is None:
                vehicle.active = False
            else:
                vehicle.license_plate = data.placa
                vehicle.type = data.tipo
                vehicle.brand = data.marca
                vehicle.model = data.modelo
                vehicle.color = data.color
                vehicle.client_id = data.cliente_id
            self.db.flush()
            after = vehicle_state(vehicle)
            self.db.add(VehicleAudit(vehicle_id=vehicle.id, account_id=account.id,
                                     action=action, before_state=before, after_state=after))
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise HTTPException(409, 'El vehículo entra en conflicto con un registro existente.') from error
        return VehicleResponse(**after)
