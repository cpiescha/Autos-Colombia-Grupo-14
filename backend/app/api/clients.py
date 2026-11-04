from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_account
from app.db.session import get_db
from app.models import Client, UserAccount
from app.schemas.client import ClientResponse

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


@router.get("", response_model=list[ClientResponse])
def list_clients(
    account: UserAccount = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> list[ClientResponse]:
    del account
    return [
        ClientResponse(id=client.id, nombre=client.name)
        for client in db.scalars(select(Client).order_by(Client.id))
    ]
