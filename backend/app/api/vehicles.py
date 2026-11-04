from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.api.dependencies import get_current_account, get_vehicle_repository, require_administrator
from app.db.session import get_db
from app.models import UserAccount
from app.schemas.vehicle import VehicleResponse, VehicleWriteRequest
from app.services.vehicle_admin import VehicleAdminService
from app.schemas.vehicle import VehicleLookupResponse
from app.services.vehicle_authorization import (
    VehicleAuthorizationService,
    VehicleRepository,
)

router = APIRouter(prefix="/api/vehiculos", tags=["vehiculos"])


@router.post("", response_model=VehicleResponse, status_code=201)
def create_vehicle(
    data: VehicleWriteRequest,
    account: UserAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> VehicleResponse:
    return VehicleAdminService(db).write(account, data)


@router.put("/{placa}", response_model=VehicleResponse)
def update_vehicle(
    placa: str,
    data: VehicleWriteRequest,
    account: UserAccount = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> VehicleResponse:
    return VehicleAdminService(db).write(account, data, placa)


@router.delete("/{placa}", response_model=VehicleResponse)
def retire_vehicle(
    placa: str,
    account: UserAccount = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> VehicleResponse:
    return VehicleAdminService(db).write(account, plate=placa)


@router.get("/{placa}", response_model=VehicleLookupResponse, dependencies=[Depends(get_current_account)])
def get_vehicle(
    placa: str,
    repository: VehicleRepository = Depends(get_vehicle_repository),
) -> VehicleLookupResponse:
    authorization = VehicleAuthorizationService(repository).lookup(placa)
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehículo no registrado.",
        )

    vehicle = authorization.vehicle
    return VehicleLookupResponse(
        placa=vehicle.license_plate,
        tipo=authorization.vehicle_type,
        marca=vehicle.brand,
        modelo=vehicle.model,
        color=vehicle.color,
        estado_mensualidad=(
            "vigente" if authorization.membership_active else "vencida"
        ),
        authorized=authorization.authorized,
        rejection_reason=authorization.rejection_reason,
    )
