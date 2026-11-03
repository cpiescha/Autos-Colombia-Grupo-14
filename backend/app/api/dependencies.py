from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import UserAccount
from app.models.enums import AccountRole
from app.services.auth import forbidden_error, invalid_session_error, resolve_current_account
from app.services.entry import EntryRepository, SqlAlchemyEntryRepository
from app.services.vehicle_authorization import (
    SqlAlchemyVehicleRepository,
    VehicleRepository,
)


def get_vehicle_repository(
    db: Session = Depends(get_db),
) -> VehicleRepository:
    return SqlAlchemyVehicleRepository(db)


def get_entry_repository(
    db: Session = Depends(get_db),
) -> EntryRepository:
    return SqlAlchemyEntryRepository(db)


_bearer = HTTPBearer(auto_error=False)


def get_current_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> UserAccount:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise invalid_session_error()
    return resolve_current_account(db, credentials.credentials)


def require_administrator(
    account: UserAccount = Depends(get_current_account),
) -> UserAccount:
    if account.role != AccountRole.ADMINISTRADOR:
        raise forbidden_error()
    return account
