from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_account
from app.db.session import get_db
from app.models import Client, UserAccount
from app.models.enums import AccountRole, ClientStatus
from app.schemas.client import ClientResponse, ClientDeactivationRequest, ClientLifecycleResponse
from app.services.client_lifecycle import ClientLifecycleService

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


@router.get("", response_model=list[ClientResponse])
def list_clients(
    account: UserAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> list[ClientResponse]:
    query = select(Client).order_by(Client.id)
    if account.role != AccountRole.ADMINISTRADOR:
        query = query.where(Client.status == ClientStatus.ACTIVE.value)
    return [
        ClientResponse(id=client.id, nombre=client.name)
        for client in db.scalars(query)
    ]


@router.patch('/{client_id}/baja', response_model=ClientLifecycleResponse)
def deactivate_client(
    client_id: int,
    request: ClientDeactivationRequest,
    account: UserAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> ClientLifecycleResponse:
    client = ClientLifecycleService(db).deactivate(client_id, request.motivo, account)
    return ClientLifecycleResponse(
        id=client.id, nombre=client.name,
        estado='INACTIVO' if client.status == ClientStatus.INACTIVE.value else 'ACTIVO',
        fecha_baja=client.inactivated_at, motivo=client.inactivation_reason,
        responsable_id=client.inactivated_by,
    )
