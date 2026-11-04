from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_account, require_administrator
from app.db.session import get_db
from app.models import UserAccount
from app.schemas.parking_spot_admin import (
    ParkingSpotCreateRequest,
    ParkingSpotResponse,
    ParkingSpotStateRequest,
)
from app.services.parking_spot_admin import ParkingSpotAdminService, ParkingSpotView

router = APIRouter(prefix="/api/celdas", tags=["celdas"])


def _spot_response(spot: ParkingSpotView) -> ParkingSpotResponse:
    return ParkingSpotResponse(
        id=spot.id,
        codigo=spot.code,
        categoria=spot.category,
        estado=spot.state,
        placa=spot.plate,
        tiene_historial=spot.has_history,
    )


@router.get("", response_model=list[ParkingSpotResponse])
def list_spots(
    account: UserAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> list[ParkingSpotResponse]:
    del account
    return [
        _spot_response(spot)
        for spot in ParkingSpotAdminService(db).list_spots()
    ]


@router.post(
    "",
    response_model=ParkingSpotResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_spot(
    payload: ParkingSpotCreateRequest,
    administrator: UserAccount = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> ParkingSpotResponse:
    del administrator
    return _spot_response(
        ParkingSpotAdminService(db).create_spot(
            code=payload.codigo,
            category=payload.categoria,
        )
    )


@router.patch("/{spot_id}", response_model=ParkingSpotResponse)
def change_spot_state(
    spot_id: int,
    payload: ParkingSpotStateRequest,
    administrator: UserAccount = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> ParkingSpotResponse:
    del administrator
    return _spot_response(
        ParkingSpotAdminService(db).change_state(
            spot_id=spot_id,
            active=payload.estado == "ACTIVA",
        )
    )


@router.delete(
    "/{spot_id}",
    response_model=ParkingSpotResponse,
    responses={status.HTTP_204_NO_CONTENT: {"description": "Celda sin historial retirada."}},
)
def remove_spot(
    spot_id: int,
    administrator: UserAccount = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> ParkingSpotResponse | Response:
    del administrator
    spot = ParkingSpotAdminService(db).remove_spot(spot_id)
    if spot is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return _spot_response(spot)
