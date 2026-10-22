from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_vehicle_repository
from app.schemas.vehicle import VehicleLookupResponse
from app.services.vehicle_authorization import (
    VehicleAuthorizationService,
    VehicleRepository,
)

router = APIRouter(prefix="/api/vehiculos", tags=["vehiculos"])


@router.get("/{placa}", response_model=VehicleLookupResponse)
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
