from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.corrections import router
from app.db.base import Base
from app.db.session import get_db
from app.models.cell_correction import CellCorrection
from app.models.client import Client
from app.models.enums import SpotCategory, VehicleType
from app.models.operator import Operator
from app.models.parking_spot import ParkingSpot
from app.models.parking_stay import ParkingStay
from app.models.vehicle import Vehicle


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    with factory.begin() as session:
        session.add_all(
            [
                Client(id=1, name="Cliente de prueba"),
                Operator(id=1, name="Operario de prueba"),
                ParkingSpot(id=1, code="A-01", category=SpotCategory.AUTOMOVIL),
                ParkingSpot(id=2, code="A-02", category=SpotCategory.AUTOMOVIL),
                ParkingSpot(id=3, code="M-01", category=SpotCategory.MOTO),
                ParkingSpot(id=4, code="A-03", category=SpotCategory.AUTOMOVIL),
                ParkingSpot(id=5, code="A-04", category=SpotCategory.AUTOMOVIL),
                Vehicle(
                    id=1,
                    license_plate="CAR001",
                    type=VehicleType.CARRO,
                    brand="Marca",
                    model="Modelo",
                    color="Azul",
                    client_id=1,
                ),
                Vehicle(
                    id=2,
                    license_plate="CAR002",
                    type=VehicleType.CARRO,
                    brand="Marca",
                    model="Modelo",
                    color="Rojo",
                    client_id=1,
                ),
                Vehicle(
                    id=3,
                    license_plate="HIS001",
                    type=VehicleType.CARRO,
                    brand="Marca",
                    model="Histórico",
                    color="Gris",
                    client_id=1,
                ),
                ParkingStay(
                    id=1,
                    vehicle_id=1,
                    parking_spot_id=1,
                    entry_operator_id=1,
                    entered_at=datetime.now(timezone.utc),
                ),
                ParkingStay(
                    id=2,
                    vehicle_id=3,
                    parking_spot_id=5,
                    entry_operator_id=1,
                    entered_at=datetime.now(timezone.utc),
                    exit_operator_id=1,
                    exited_at=datetime.now(timezone.utc),
                ),
                ParkingStay(
                    id=3,
                    vehicle_id=2,
                    parking_spot_id=4,
                    entry_operator_id=1,
                    entered_at=datetime.now(timezone.utc),
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
    test_app = FastAPI()
    test_app.include_router(router)

    def override_get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    test_app.dependency_overrides[get_db] = override_get_db
    with TestClient(test_app) as test_client:
        yield test_client


def state(session_factory: sessionmaker[Session]) -> tuple[list[tuple[int, int]], int]:
    with session_factory() as session:
        stays = list(
            session.execute(
                select(ParkingStay.id, ParkingStay.parking_spot_id).order_by(ParkingStay.id)
            )
        )
        audits = list(session.scalars(select(CellCorrection)))
    return ([(stay_id, spot_id) for stay_id, spot_id in stays], len(audits))


def assert_error(response, status_code: int, code: str, message: str) -> None:
    assert response.status_code == status_code
    assert response.json() == {"code": code, "message": message, "details": None}


def test_openapi_publishes_the_correction_request_body(client: TestClient) -> None:
    operation = client.get("/openapi.json").json()["paths"][
        "/api/movimientos/{movement_id}/celda"
    ]["patch"]

    assert operation["requestBody"]["required"] is True
    schema = operation["requestBody"]["content"]["application/json"]["schema"]
    assert schema == {"$ref": "#/components/schemas/CellCorrectionRequest"}


def test_corrects_a_normalized_compatible_free_spot_and_audits_once(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    response = client.patch(
        "/api/movimientos/1/celda",
        json={"celda": " a-02 ", "operario_id": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["movimiento_id"] == 1
    assert body["celda_anterior"] == "A-01"
    assert body["celda_nueva"] == "A-02"
    assert body["operario_id"] == 1
    assert datetime.fromisoformat(body["fecha_correccion"]).tzinfo is not None

    with session_factory() as session:
        assert session.get(ParkingStay, 1).parking_spot_id == 2
        audits = list(session.scalars(select(CellCorrection)))

    assert len(audits) == 1
    assert audits[0].parking_stay_id == 1
    assert audits[0].previous_spot_id == 1
    assert audits[0].new_spot_id == 2
    assert audits[0].operator_id == 1


@pytest.mark.parametrize(
    ("movement_id", "payload", "status_code", "code", "message"),
    [
        (99, {"celda": "A-02", "operario_id": 1}, 404, "STAY_NOT_FOUND", "No existe el movimiento."),
        (2, {"celda": "A-01", "operario_id": 1}, 409, "STAY_ALREADY_CLOSED", "No se puede corregir una permanencia cerrada."),
        (1, {"celda": "A-01", "operario_id": 1}, 409, "SAME_SPOT", "La celda nueva debe ser distinta a la asignada."),
        (1, {"celda": "M-01", "operario_id": 1}, 409, "SPOT_INCOMPATIBLE", "La celda no es compatible con el tipo de vehículo."),
        (1, {"celda": "A-03", "operario_id": 1}, 409, "SPOT_OCCUPIED", "La celda ya pertenece a otra permanencia abierta."),
        (1, {"celda": "Z-99", "operario_id": 1}, 404, "SPOT_NOT_FOUND", "La celda indicada no existe."),
        (1, {"celda": "A-02", "operario_id": 99}, 422, "OPERATOR_NOT_FOUND", "El operario no está registrado."),
    ],
)
def test_rejects_each_business_rule_without_changing_stay_or_audit(
    client: TestClient,
    session_factory: sessionmaker[Session],
    movement_id: int,
    payload: dict[str, object],
    status_code: int,
    code: str,
    message: str,
) -> None:
    before = state(session_factory)

    response = client.patch(f"/api/movimientos/{movement_id}/celda", json=payload)

    assert_error(response, status_code, code, message)
    assert state(session_factory) == before


@pytest.mark.parametrize(
    "payload",
    [
        {"celda": "   ", "operario_id": 1},
        {"celda": "A-02", "operario_id": 0},
        {"celda": "A-02", "operario_id": "1"},
        {"operario_id": 1},
        [],
    ],
)
def test_rejects_invalid_correction_data_without_changing_state(
    client: TestClient, session_factory: sessionmaker[Session], payload: object
) -> None:
    before = state(session_factory)

    response = client.patch("/api/movimientos/1/celda", json=payload)

    assert_error(
        response,
        422,
        "INVALID_CORRECTION_DATA",
        "Los datos de corrección de celda no son válidos.",
    )
    assert state(session_factory) == before
