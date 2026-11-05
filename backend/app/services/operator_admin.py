import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import Operator, UserAccount
from app.models.enums import AccountRole


class OperatorAdminError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def username_exists_error() -> OperatorAdminError:
    return OperatorAdminError(
        409,
        "USERNAME_EXISTS",
        "El nombre de usuario ya está registrado.",
    )


def account_not_found_error() -> OperatorAdminError:
    return OperatorAdminError(
        404,
        "OPERATOR_ACCOUNT_NOT_FOUND",
        "La cuenta de operador no existe.",
    )


class OperatorAdminService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_accounts(self) -> list[UserAccount]:
        return list(
            self.db.scalars(
                select(UserAccount)
                .options(joinedload(UserAccount.operator))
                .where(UserAccount.role == AccountRole.OPERADOR)
                .order_by(UserAccount.id)
            )
        )

    def create_operator(
        self,
        name: str,
        username: str,
        password: str,
    ) -> UserAccount:
        if self.db.scalar(
            select(UserAccount.id).where(UserAccount.username == username)
        ) is not None:
            raise username_exists_error()

        operator = Operator(name=name)
        account = UserAccount(
            operator=operator,
            username=username,
            password_hash=bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt(rounds=12),
            ).decode("utf-8"),
            role=AccountRole.OPERADOR,
            active=True,
        )
        self.db.add(account)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise username_exists_error() from None
        return self._account_by_id(account.id)

    def change_state(self, account_id: int, active: bool) -> UserAccount:
        account = self._account_by_id(account_id, required=False)
        if account is None:
            raise account_not_found_error()
        account.active = active
        self.db.commit()
        return self._account_by_id(account.id)

    def _account_by_id(
        self,
        account_id: int,
        required: bool = True,
    ) -> UserAccount | None:
        account = self.db.scalar(
            select(UserAccount)
            .options(joinedload(UserAccount.operator))
            .where(
                UserAccount.id == account_id,
                UserAccount.role == AccountRole.OPERADOR,
            )
        )
        if required and account is None:
            raise account_not_found_error()
        return account
