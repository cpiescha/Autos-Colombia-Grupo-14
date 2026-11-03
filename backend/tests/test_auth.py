import os
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

TEST_AUTH_SECRET = "test-auth-secret-at-least-32-characters"
os.environ["AUTH_SECRET"] = TEST_AUTH_SECRET
os.environ["AUTH_TTL_MINUTES"] = "30"
os.environ["AUTH_ALGORITHM"] = "HS256"

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Operator, UserAccount
from app.models.enums import AccountRole

ADMIN_PASSWORD_HASH = "$2b$12$4lMJXy0QLFfIfSi7Fe197e2XMrGSEqsN7RUpZHiYoeWVJkx7mYJCC"
OPERATOR_PASSWORD_HASH = "$2b$12$mDJesC5e95PWwluP4SPjhOoj5yN3n1nOOqaeC4bp.97GKLkOPu4Fe"


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
        inactive_operator = Operator(name="Operario Anulado")
        session.add_all([administrator, inactive_operator])
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
                    operator_id=inactive_operator.id,
                    username="anulado",
                    password_hash=OPERATOR_PASSWORD_HASH,
                    role=AccountRole.OPERADOR,
                    active=False,
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


def test_compose_requires_an_explicit_auth_secret() -> None:
    compose = (Path(__file__).parents[2] / "docker-compose.yml").read_text(
        encoding="utf-8"
    )

    assert "AUTH_SECRET: ${AUTH_SECRET:?" in compose


def test_valid_credentials_return_token_and_current_user(client: TestClient) -> None:
    login = client.post(
        "/api/auth/login",
        json={"username": " ADMIN ", "password": "Admin2026"},
    )

    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"] == {
        "id": body["user"]["id"],
        "username": "admin",
        "name": "Administrador Parqueadero",
        "role": "ADMINISTRADOR",
    }
    assert "password" not in str(body).lower()
    assert "hash" not in str(body).lower()

    current_user = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )

    assert current_user.status_code == 200
    assert current_user.json() == body["user"]


def test_invalid_password_is_rejected_without_changing_account(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "incorrecta"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "INVALID_CREDENTIALS",
        "message": "Usuario o contraseña inválidos.",
        "details": None,
    }
    with session_factory() as session:
        account = session.scalar(select(UserAccount).where(UserAccount.username == "admin"))
        assert account is not None
        assert account.active is True
        assert account.password_hash == ADMIN_PASSWORD_HASH


def test_inactive_account_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "anulado", "password": "Operario2026"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "ACCOUNT_INACTIVE",
        "message": "La cuenta está anulada.",
        "details": None,
    }


def test_invalid_token_is_rejected(client: TestClient) -> None:
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer token-invalido"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "INVALID_SESSION",
        "message": "La sesión no es válida o venció.",
        "details": None,
    }


def test_expired_token_is_rejected(client: TestClient) -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "1",
            "iat": now - timedelta(minutes=2),
            "exp": now - timedelta(minutes=1),
        },
        TEST_AUTH_SECRET,
        algorithm="HS256",
    )

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "INVALID_SESSION",
        "message": "La sesión no es válida o venció.",
        "details": None,
    }


def test_active_account_is_reloaded_for_every_authenticated_request(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin2026"},
    )
    token = login.json()["access_token"]

    with session_factory.begin() as session:
        account = session.scalar(select(UserAccount).where(UserAccount.username == "admin"))
        assert account is not None
        account.active = False

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "INVALID_SESSION",
        "message": "La sesión no es válida o venció.",
        "details": None,
    }


def test_logout_requires_a_valid_session(client: TestClient) -> None:
    unauthenticated = client.post("/api/auth/logout")
    assert unauthenticated.status_code == 401

    login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin2026"},
    )
    response = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert response.status_code == 204
    assert response.content == b""
