import os
from collections.abc import Generator

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["AUTH_SECRET"] = "test-auth-secret-at-least-32-characters"
os.environ["AUTH_TTL_MINUTES"] = "30"
os.environ["AUTH_ALGORITHM"] = "HS256"

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Operator, UserAccount
from app.models.enums import AccountRole

ADMIN_PASSWORD_HASH = "$2b$12$4lMJXy0QLFfIfSi7Fe197e2XMrGSEqsN7RUpZHiYoeWVJkx7mYJCC"
OPERATOR_PASSWORD_HASH = "$2b$12$mDJesC5e95PWwluP4SPjhOoj5yN3n1nOOqaeC4bp.97GKLkOPu4Fe"
FORBIDDEN_BODY = {
    "code": "FORBIDDEN",
    "message": "No tiene permisos para realizar esta acción.",
    "details": None,
}


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    with factory.begin() as session:
        administrator = Operator(name="Administrador Parqueadero")
        operator = Operator(name="Operario Diurno 1")
        session.add_all([administrator, operator])
        session.flush()
        session.add_all(
            [
                UserAccount(
                    operator_id=administrator.id,
                    username="admin",
                    password_hash=ADMIN_PASSWORD_HASH,
                    role=AccountRole.ADMINISTRADOR,
                    active=True,
                ),
                UserAccount(
                    operator_id=operator.id,
                    username="operario1",
                    password_hash=OPERATOR_PASSWORD_HASH,
                    role=AccountRole.OPERADOR,
                    active=True,
                ),
            ]
        )

    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def _token(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_requests_cannot_administer_accounts(client: TestClient) -> None:
    responses = [
        client.get("/api/operadores"),
        client.post(
            "/api/operadores",
            json={
                "nombre": "Operario Sin Sesión",
                "usuario": "sin.sesion",
                "clave": "Temporal2026",
            },
        ),
        client.patch(
            "/api/operadores/2/estado",
            json={"estado": "ANULADA"},
        ),
    ]

    assert [(response.status_code, response.json()) for response in responses] == [
        (
            401,
            {
                "code": "INVALID_SESSION",
                "message": "La sesión no es válida o venció.",
                "details": None,
            },
        ),
        (
            401,
            {
                "code": "INVALID_SESSION",
                "message": "La sesión no es válida o venció.",
                "details": None,
            },
        ),
        (
            401,
            {
                "code": "INVALID_SESSION",
                "message": "La sesión no es válida o venció.",
                "details": None,
            },
        ),
    ]


def test_administrator_lists_accounts_without_exposing_credentials(
    client: TestClient,
) -> None:
    token = _token(client, "admin", "Admin2026")

    response = client.get("/api/operadores", headers=_authorization(token))

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 2,
            "operador_id": 2,
            "nombre": "Operario Diurno 1",
            "usuario": "operario1",
            "rol": "OPERADOR",
            "estado": "ACTIVA",
            "creado_en": response.json()[0]["creado_en"],
            "actualizado_en": response.json()[0]["actualizado_en"],
        },
    ]
    assert "password" not in str(response.json()).lower()
    assert "hash" not in str(response.json()).lower()


def test_operator_cannot_administer_accounts_or_change_state(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    token = _token(client, "operario1", "Operario2026")
    headers = _authorization(token)

    with session_factory() as session:
        operator_count = session.scalar(select(func.count()).select_from(Operator))
        account_count = session.scalar(select(func.count()).select_from(UserAccount))

    responses = [
        client.get("/api/operadores", headers=headers),
        client.post(
            "/api/operadores",
            headers=headers,
            json={
                "nombre": "Operario Bloqueado",
                "usuario": "bloqueado",
                "clave": "Temporal2026",
            },
        ),
        client.patch(
            "/api/operadores/2/estado",
            headers=headers,
            json={"estado": "ANULADA"},
        ),
    ]

    assert [(response.status_code, response.json()) for response in responses] == [
        (403, FORBIDDEN_BODY),
        (403, FORBIDDEN_BODY),
        (403, FORBIDDEN_BODY),
    ]
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Operator)) == operator_count
        assert session.scalar(select(func.count()).select_from(UserAccount)) == account_count
        target = session.scalar(
            select(UserAccount).where(UserAccount.username == "operario1")
        )
        assert target is not None
        assert target.active is True
        assert session.scalar(
            select(UserAccount).where(UserAccount.username == "bloqueado")
        ) is None


def test_administrator_creates_operator_with_hashed_password(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    token = _token(client, "admin", "Admin2026")

    response = client.post(
        "/api/operadores",
        headers=_authorization(token),
        json={
            "nombre": "Sofía Ramírez",
            "usuario": "sofia.ramirez",
            "clave": "Temporal2026",
        },
    )

    assert response.status_code == 201
    assert response.json()["nombre"] == "Sofía Ramírez"
    assert response.json()["usuario"] == "sofia.ramirez"
    assert response.json()["rol"] == "OPERADOR"
    assert response.json()["estado"] == "ACTIVA"
    with session_factory() as session:
        account = session.scalar(
            select(UserAccount).where(UserAccount.username == "sofia.ramirez")
        )
        assert account is not None
        assert account.password_hash != "Temporal2026"
        assert bcrypt.checkpw(b"Temporal2026", account.password_hash.encode("utf-8"))
        assert account.operator.name == "Sofía Ramírez"


def test_blank_operator_name_is_rejected_without_partial_rows(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    token = _token(client, "admin", "Admin2026")
    with session_factory() as session:
        operator_count = session.scalar(select(func.count()).select_from(Operator))
        account_count = session.scalar(select(func.count()).select_from(UserAccount))

    response = client.post(
        "/api/operadores",
        headers=_authorization(token),
        json={
            "nombre": "   ",
            "usuario": "nombre.vacio",
            "clave": "Temporal2026",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "code": "INVALID_OPERATOR_DATA",
        "message": "Los datos del operador no son válidos.",
        "details": None,
    }
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Operator)) == operator_count
        assert session.scalar(select(func.count()).select_from(UserAccount)) == account_count


def test_duplicate_username_is_rejected_without_partial_operator(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    token = _token(client, "admin", "Admin2026")
    with session_factory() as session:
        operator_count = session.scalar(select(func.count()).select_from(Operator))
        account_count = session.scalar(select(func.count()).select_from(UserAccount))

    response = client.post(
        "/api/operadores",
        headers=_authorization(token),
        json={
            "nombre": "Nombre Duplicado",
            "usuario": "operario1",
            "clave": "Temporal2026",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "code": "USERNAME_EXISTS",
        "message": "El nombre de usuario ya está registrado.",
        "details": None,
    }
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Operator)) == operator_count
        assert session.scalar(select(func.count()).select_from(UserAccount)) == account_count
        assert session.scalar(
            select(Operator).where(Operator.name == "Nombre Duplicado")
        ) is None


def test_operator_endpoint_does_not_change_administrator_accounts(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    token = _token(client, "admin", "Admin2026")

    response = client.patch(
        "/api/operadores/1/estado",
        headers=_authorization(token),
        json={"estado": "ANULADA"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "OPERATOR_ACCOUNT_NOT_FOUND",
        "message": "La cuenta de operador no existe.",
        "details": None,
    }
    with session_factory() as session:
        administrator = session.get(UserAccount, 1)
        assert administrator is not None
        assert administrator.active is True
        assert administrator.role == AccountRole.ADMINISTRADOR


def test_administrator_deactivates_and_reactivates_account_without_deleting_history(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    admin_token = _token(client, "admin", "Admin2026")
    operator_token = _token(client, "operario1", "Operario2026")
    headers = _authorization(admin_token)

    deactivate = client.patch(
        "/api/operadores/2/estado",
        headers=headers,
        json={"estado": "ANULADA"},
    )

    assert deactivate.status_code == 200
    assert deactivate.json()["estado"] == "ANULADA"
    rejected_login = client.post(
        "/api/auth/login",
        json={"username": "operario1", "password": "Operario2026"},
    )
    assert rejected_login.status_code == 401
    assert rejected_login.json()["code"] == "ACCOUNT_INACTIVE"
    rejected_existing_token = client.get(
        "/api/operadores",
        headers=_authorization(operator_token),
    )
    assert rejected_existing_token.status_code == 401
    assert rejected_existing_token.json()["code"] == "INVALID_SESSION"
    with session_factory() as session:
        account = session.get(UserAccount, 2)
        assert account is not None
        assert account.operator.name == "Operario Diurno 1"

    reactivate = client.patch(
        "/api/operadores/2/estado",
        headers=headers,
        json={"estado": "ACTIVA"},
    )

    assert reactivate.status_code == 200
    assert reactivate.json()["estado"] == "ACTIVA"
    assert client.post(
        "/api/auth/login",
        json={"username": "operario1", "password": "Operario2026"},
    ).status_code == 200
