import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import UserAccount

_DUMMY_PASSWORD_HASH = b"$2b$12$4lMJXy0QLFfIfSi7Fe197e2XMrGSEqsN7RUpZHiYoeWVJkx7mYJCC"


class AuthenticationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class AuthorizationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def forbidden_error() -> AuthorizationError:
    return AuthorizationError(
        "FORBIDDEN",
        "No tiene permisos para realizar esta acción.",
    )


def invalid_credentials_error() -> AuthenticationError:
    return AuthenticationError(
        "INVALID_CREDENTIALS",
        "Usuario o contraseña inválidos.",
    )


def account_inactive_error() -> AuthenticationError:
    return AuthenticationError(
        "ACCOUNT_INACTIVE",
        "La cuenta está anulada.",
    )


def invalid_session_error() -> AuthenticationError:
    return AuthenticationError(
        "INVALID_SESSION",
        "La sesión no es válida o venció.",
    )


def _auth_secret() -> str:
    secret = os.getenv("AUTH_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("AUTH_SECRET must contain at least 32 characters")
    return secret


def _auth_algorithm() -> str:
    algorithm = os.getenv("AUTH_ALGORITHM", "HS256")
    if algorithm != "HS256":
        raise RuntimeError("AUTH_ALGORITHM must be HS256")
    return algorithm


def _auth_ttl() -> timedelta:
    raw_minutes = os.getenv("AUTH_TTL_MINUTES", "60")
    try:
        minutes = int(raw_minutes)
    except ValueError as error:
        raise RuntimeError("AUTH_TTL_MINUTES must be an integer") from error
    if minutes <= 0:
        raise RuntimeError("AUTH_TTL_MINUTES must be positive")
    return timedelta(minutes=minutes)


def _account_by_username(db: Session, username: str) -> UserAccount | None:
    return db.scalar(
        select(UserAccount)
        .options(joinedload(UserAccount.operator))
        .where(UserAccount.username == username)
    )


def _account_by_id(db: Session, account_id: int) -> UserAccount | None:
    return db.scalar(
        select(UserAccount)
        .options(joinedload(UserAccount.operator))
        .where(UserAccount.id == account_id)
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (TypeError, ValueError):
        return False


def authenticate_account(db: Session, username: str, password: str) -> UserAccount:
    account = _account_by_username(db, username.strip().lower())
    candidate_hash = account.password_hash.encode("utf-8") if account else _DUMMY_PASSWORD_HASH

    try:
        password_matches = bcrypt.checkpw(password.encode("utf-8"), candidate_hash)
    except (TypeError, ValueError):
        password_matches = False

    if account is None or not password_matches:
        raise invalid_credentials_error()
    if not account.active:
        raise account_inactive_error()
    return account


def create_access_token(account_id: int) -> str:
    issued_at = datetime.now(timezone.utc)
    payload = {
        "sub": str(account_id),
        "iat": issued_at,
        "exp": issued_at + _auth_ttl(),
    }
    return jwt.encode(payload, _auth_secret(), algorithm=_auth_algorithm())


def resolve_current_account(db: Session, token: str) -> UserAccount:
    try:
        payload = jwt.decode(
            token,
            _auth_secret(),
            algorithms=[_auth_algorithm()],
            options={"require": ["sub", "iat", "exp"]},
        )
        account_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise invalid_session_error() from None

    account = _account_by_id(db, account_id)
    if account is None or not account.active:
        raise invalid_session_error()
    return account
