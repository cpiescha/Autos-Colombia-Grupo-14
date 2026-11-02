from sqlalchemy import CheckConstraint, create_engine
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateTable

from app.db import Base, close_stay_by_receipt, correct_parking_spot
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


def test_user_account_constraints_are_postgresql_only() -> None:
    postgresql_ddl = str(
        CreateTable(UserAccount.__table__).compile(dialect=postgresql.dialect())
    )
    sqlite_ddl = str(CreateTable(UserAccount.__table__).compile(dialect=sqlite.dialect()))

    assert "CONSTRAINT ck_password_is_hash" in postgresql_ddl
    assert "CONSTRAINT ck_username_normalized" in postgresql_ddl
    assert "ck_password_is_hash" not in sqlite_ddl
    assert "ck_username_normalized" not in sqlite_ddl


def test_iteration2_models_create_on_sqlite_without_import_cycles() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    Base.metadata.create_all(engine)

    assert callable(close_stay_by_receipt)
    assert callable(correct_parking_spot)
    assert {"user_accounts", "parking_spots"}.issubset(Base.metadata.tables)


def test_parking_spot_keeps_code_type_and_active_state() -> None:
    columns = ParkingSpot.__table__.c
    assert columns.code.unique is True
    assert columns.category.nullable is False
    assert columns.active.nullable is False
    assert columns.active.default.arg is True
