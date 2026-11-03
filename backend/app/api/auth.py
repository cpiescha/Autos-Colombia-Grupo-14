from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_account
from app.db.session import get_db
from app.models import UserAccount
from app.schemas.auth import CurrentUserResponse, LoginRequest, LoginResponse
from app.services.auth import authenticate_account, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _current_user(account: UserAccount) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=account.id,
        username=account.username,
        name=account.operator.name,
        role=account.role,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    account = authenticate_account(db, payload.username, payload.password)
    return LoginResponse(
        access_token=create_access_token(account.id),
        user=_current_user(account),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    account: UserAccount = Depends(get_current_account),
) -> Response:
    del account
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=CurrentUserResponse)
def current_user(
    account: UserAccount = Depends(get_current_account),
) -> CurrentUserResponse:
    return _current_user(account)
