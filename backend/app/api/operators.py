from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_administrator
from app.db.session import get_db
from app.models import UserAccount
from app.schemas.operator_admin import (
    OperatorAccountResponse,
    OperatorCreateRequest,
    OperatorStateRequest,
)
from app.services.operator_admin import OperatorAdminService

router = APIRouter(prefix="/api/operadores", tags=["operadores"])


def _account_response(account: UserAccount) -> OperatorAccountResponse:
    return OperatorAccountResponse(
        id=account.id,
        operador_id=account.operator_id,
        nombre=account.operator.name,
        usuario=account.username,
        rol=account.role,
        estado="ACTIVA" if account.active else "ANULADA",
        creado_en=account.created_at,
        actualizado_en=account.updated_at,
    )


@router.get("", response_model=list[OperatorAccountResponse])
def list_operators(
    administrator: UserAccount = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> list[OperatorAccountResponse]:
    del administrator
    return [
        _account_response(account)
        for account in OperatorAdminService(db).list_accounts()
    ]


@router.post(
    "",
    response_model=OperatorAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_operator(
    payload: OperatorCreateRequest,
    administrator: UserAccount = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> OperatorAccountResponse:
    del administrator
    account = OperatorAdminService(db).create_operator(
        name=payload.nombre,
        username=payload.usuario,
        password=payload.clave,
    )
    return _account_response(account)


@router.patch("/{account_id}/estado", response_model=OperatorAccountResponse)
def change_operator_state(
    account_id: int,
    payload: OperatorStateRequest,
    administrator: UserAccount = Depends(require_administrator),
    db: Session = Depends(get_db),
) -> OperatorAccountResponse:
    del administrator
    account = OperatorAdminService(db).change_state(
        account_id=account_id,
        active=payload.estado == "ACTIVA",
    )
    return _account_response(account)
