import os
from collections.abc import Generator
from datetime import datetime, timezone

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
from app.models import (
    CellCorrection,
    Client,
    Operator,
    ParkingSpot,
    ParkingStay,
    UserAccount,
    Vehicle,
)
from app.models.enums import AccountRole, SpotCategory, VehicleType

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
        client = Client(name="Cliente histórico")
        session.add_all([administrator, operator, client])
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
                ParkingSpot(id=1, code="A-01", category=SpotCategory.AUTOMOVIL),
                ParkingSpot(id=2, code="A-02", category=SpotCategory.AUTOMOVIL),
                ParkingSpot(
                    id=3,
                    code="M-01",
                    category=SpotCategory.MOTO,
                    active=False,
                ),
                ParkingSpot(id=4, code="A-03", category=SpotCategory.AUTOMOVIL),
                ParkingSpot(id=5, code="A-04", category=SpotCategory.AUTOMOVIL),
                Vehicle(
                    id=1,
                    license_plate="HIS001",
                    type=VehicleType.CARRO,
                    brand="Renault",
                    model="Logan",
                    color="Gris",
                    client_id=client.id,
                ),
            ]
        )
        session.flush()
        session.add(
            ParkingStay(
                id=1,
                vehicle_id=1,
                parking_spot_id=4,
                entry_operator_id=operator.id,
                entered_at=datetime.now(timezone.utc),
            )
        )
        session.flush()
        session.add(
            CellCorrection(
                id=1,
                parking_stay_id=1,
                previous_spot_id=2,
                new_spot_id=4,
                operator_id=operator.id,
                corrected_at=datetime.now(timezone.utc),
            )
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


def _cell_state(session_factory: sessionmaker[Session]) -> list[tuple[int, str, bool]]:
    with session_factory() as session:
        return list(
            session.execute(
                select(ParkingSpot.id, ParkingSpot.code, ParkingSpot.active).order_by(
                    ParkingSpot.id
                )
            )
        )


def test_authenticated_profiles_list_cells_with_active_occupied_and_history_state(
    client: TestClient,
) -> None:
    for username, password in [("admin", "Admin2026"), ("operario1", "Operario2026")]:
        response = client.get(
            "/api/celdas",
            headers=_authorization(_token(client, username, password)),
        )

        assert response.status_code == 200
        assert response.json() == [
            {
                "id": 1,
                "codigo": "A-01",
                "categoria": "AUTOMOVIL",
                "estado": "disponible",
                "placa": None,
                "tiene_historial": False,
            },
            {
                "id": 2,
                "codigo": "A-02",
                "categoria": "AUTOMOVIL",
                "estado": "disponible",
                "placa": None,
                "tiene_historial": True,
            },
            {
                "id": 4,
                "codigo": "A-03",
                "categoria": "AUTOMOVIL",
                "estado": "ocupada",
                "placa": "HIS001",
                "tiene_historial": True,
            },
            {
                "id": 5,
                "codigo": "A-04",
                "categoria": "AUTOMOVIL",
                "estado": "disponible",
                "placa": None,
                "tiene_historial": False,
            },
            {
                "id": 3,
                "codigo": "M-01",
                "categoria": "MOTO",
                "estado": "inactiva",
                "placa": None,
                "tiene_historial": False,
            },
        ]


def test_unauthenticated_and_operator_requests_cannot_mutate_cells(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    before = _cell_state(session_factory)
    operator_headers = _authorization(_token(client, "operario1", "Operario2026"))

    unauthenticated = client.post(
        "/api/celdas",
        json={"codigo": "M-02", "categoria": "MOTO"},
    )
    forbidden = [
        client.post(
            "/api/celdas",
            headers=operator_headers,
            json={"codigo": "M-02", "categoria": "MOTO"},
        ),
        client.patch(
            "/api/celdas/1",
            headers=operator_headers,
            json={"estado": "INACTIVA"},
        ),
        client.delete("/api/celdas/1", headers=operator_headers),
    ]

    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["code"] == "INVALID_SESSION"
    assert [(response.status_code, response.json()) for response in forbidden] == [
        (403, FORBIDDEN_BODY),
        (403, FORBIDDEN_BODY),
        (403, FORBIDDEN_BODY),
    ]
    assert _cell_state(session_factory) == before


def test_administrator_creates_normalized_unique_cell_and_duplicate_rolls_back(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    headers = _authorization(_token(client, "admin", "Admin2026"))

    created = client.post(
        "/api/celdas",
        headers=headers,
        json={"codigo": " m-02 ", "categoria": "MOTO"},
    )

    assert created.status_code == 201
    assert created.json() == {
        "id": created.json()["id"],
        "codigo": "M-02",
        "categoria": "MOTO",
        "estado": "disponible",
        "placa": None,
        "tiene_historial": False,
    }
    with session_factory() as session:
        count_after_create = session.scalar(select(func.count()).select_from(ParkingSpot))

    duplicate = client.post(
        "/api/celdas",
        headers=headers,
        json={"codigo": "M-02", "categoria": "AUTOMOVIL"},
    )

    assert duplicate.status_code == 409
    assert duplicate.json() == {
        "code": "SPOT_CODE_EXISTS",
        "message": "El código de celda ya está registrado.",
        "details": None,
    }
    with session_factory() as session:
        assert session.scalar(select(func.count()).select_from(ParkingSpot)) == count_after_create


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/api/celdas", {"codigo": "   ", "categoria": "MOTO"}),
        ("post", "/api/celdas", {"codigo": "A 99", "categoria": "AUTOMOVIL"}),
        ("post", "/api/celdas", {"codigo": "A-99", "categoria": "BICICLETA"}),
        ("patch", "/api/celdas/1", {"estado": "ELIMINADA"}),
    ],
)
def test_invalid_cell_data_is_rejected_without_changing_state(
    client: TestClient,
    session_factory: sessionmaker[Session],
    method: str,
    path: str,
    payload: dict[str, str],
) -> None:
    headers = _authorization(_token(client, "admin", "Admin2026"))
    before = _cell_state(session_factory)

    response = getattr(client, method)(path, headers=headers, json=payload)

    assert response.status_code == 422
    assert response.json() == {
        "code": "INVALID_SPOT_DATA",
        "message": "Los datos de la celda no son válidos.",
        "details": None,
    }
    assert _cell_state(session_factory) == before


def test_missing_cell_mutations_return_not_found_without_changing_state(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    headers = _authorization(_token(client, "admin", "Admin2026"))
    before = _cell_state(session_factory)

    responses = [
        client.patch(
            "/api/celdas/999",
            headers=headers,
            json={"estado": "INACTIVA"},
        ),
        client.delete("/api/celdas/999", headers=headers),
    ]

    for response in responses:
        assert response.status_code == 404
        assert response.json() == {
            "code": "SPOT_NOT_FOUND",
            "message": "La celda no existe.",
            "details": None,
        }
    assert _cell_state(session_factory) == before


def test_occupied_cell_cannot_be_deactivated_or_removed_and_state_is_unchanged(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    headers = _authorization(_token(client, "admin", "Admin2026"))
    before = _cell_state(session_factory)

    deactivate = client.patch(
        "/api/celdas/4",
        headers=headers,
        json={"estado": "INACTIVA"},
    )
    remove = client.delete("/api/celdas/4", headers=headers)

    for response in [deactivate, remove]:
        assert response.status_code == 409
        assert response.json() == {
            "code": "SPOT_OCCUPIED",
            "message": "Una celda ocupada no se puede inactivar ni retirar.",
            "details": None,
        }
    assert _cell_state(session_factory) == before


def test_administrator_deactivates_and_reactivates_cell_without_losing_row(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    headers = _authorization(_token(client, "admin", "Admin2026"))

    deactivate = client.patch(
        "/api/celdas/1",
        headers=headers,
        json={"estado": "INACTIVA"},
    )
    reactivate = client.patch(
        "/api/celdas/1",
        headers=headers,
        json={"estado": "ACTIVA"},
    )

    assert deactivate.status_code == reactivate.status_code == 200
    assert deactivate.json()["estado"] == "inactiva"
    assert reactivate.json()["estado"] == "disponible"
    with session_factory() as session:
        spot = session.get(ParkingSpot, 1)
        assert spot is not None
        assert spot.active is True


def test_removal_deletes_unused_cell_but_only_inactivates_historical_cell(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    headers = _authorization(_token(client, "admin", "Admin2026"))

    removed_unused = client.delete("/api/celdas/5", headers=headers)
    removed_historical = client.delete("/api/celdas/2", headers=headers)

    assert removed_unused.status_code == 204
    assert removed_unused.content == b""
    assert removed_historical.status_code == 200
    assert removed_historical.json()["estado"] == "inactiva"
    assert removed_historical.json()["tiene_historial"] is True
    with session_factory() as session:
        assert session.get(ParkingSpot, 5) is None
        assert session.get(ParkingSpot, 2) is not None
        assert session.get(ParkingStay, 1) is not None
        assert session.get(CellCorrection, 1) is not None
