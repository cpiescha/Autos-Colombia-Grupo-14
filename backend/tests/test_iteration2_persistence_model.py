from sqlalchemy import CheckConstraint, UniqueConstraint

from app.models import ParkingSpot, UserAccount
from app.models.enums import AccountRole


def _check_names(table) -> set[str]:
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }


def test_user_account_links_one_operator_and_rejects_plaintext() -> None:
    columns = UserAccount.__table__.c
    assert columns.operator_id.unique is True
    assert columns.username.unique is True
    assert columns.password_hash.nullable is False
    assert AccountRole.ADMINISTRADOR.value == "ADMINISTRADOR"
    assert AccountRole.OPERADOR.value == "OPERADOR"
    assert _check_names(UserAccount.__table__) == {
        "ck_password_is_hash",
        "ck_username_normalized",
    }
    assert any(
        isinstance(constraint, UniqueConstraint)
        for constraint in UserAccount.__table__.constraints
    )


def test_parking_spot_keeps_code_type_and_active_state() -> None:
    columns = ParkingSpot.__table__.c
    assert columns.code.unique is True
    assert columns.category.nullable is False
    assert columns.active.nullable is False
    assert columns.active.default.arg is True
