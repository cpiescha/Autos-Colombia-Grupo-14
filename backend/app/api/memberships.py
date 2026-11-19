from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_account, require_administrator
from app.db.session import get_db
from app.models import Membership, Payment, UserAccount, Vehicle
from app.schemas.membership import MembershipResponse
from app.services.payment_queries import MembershipQueryService

router = APIRouter(prefix="/api/mensualidades", tags=["mensualidades"])


def _response(
    vehicle: Vehicle, membership: Membership | None, payment: Payment | None
) -> MembershipResponse:
    cutoff = membership.current_cutoff_date if membership else None
    today = datetime.now(timezone.utc).date()
    return MembershipResponse(
        vehiculo_id=vehicle.id,
        cliente_id=vehicle.client_id,
        placa=vehicle.license_plate,
        mensualidad_id=membership.id if membership else None,
        fecha_corte=cutoff,
        estado="vigente" if cutoff is not None and cutoff.date() >= today else "vencido",
        fecha_ultimo_pago=payment.paid_at if payment else None,
    )


@router.get("/vehiculo/{placa}", response_model=MembershipResponse)
def vehicle_membership(
    placa: str,
    account: UserAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> MembershipResponse:
    return _response(*MembershipQueryService(db).for_vehicle(placa))


@router.get("/cliente/{client_id}", response_model=list[MembershipResponse])
def client_memberships(
    client_id: int,
    account: UserAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> list[MembershipResponse]:
    return [_response(*row) for row in MembershipQueryService(db).for_client(client_id)]


@router.get("/por-vencer", response_model=list[MembershipResponse])
def expiring_memberships(
    dias: int = Query(default=7, ge=0),
    account: UserAccount = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> list[MembershipResponse]:
    return [_response(*row) for row in MembershipQueryService(db).expiring(dias)]
