from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.occupancy import router
from app.db.base import Base
from app.db.session import get_db
from app.models import Client, Operator, ParkingSpot, ParkingStay, Vehicle
from app.models.enums import SpotCategory, VehicleType


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as database_session:
        yield database_session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(router)

    def get_test_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as test_client:
        yield test_client


def create_parking_data(session: Session) -> None:
    client = Client(name="Cliente de prueba")
    operator = Operator(name="Operario de prueba")
    session.add_all(
        [
            client,
            operator,
            ParkingSpot(code="M-02", category=SpotCategory.MOTO),
            ParkingSpot(code="M-01", category=SpotCategory.MOTO),
            ParkingSpot(code="A-02", category=SpotCategory.AUTOMOVIL),
            ParkingSpot(code="A-01", category=SpotCategory.AUTOMOVIL),
        ]
    )
    session.flush()

    session.add_all(
        [
            Vehicle(
                license_plate="MOT001",
                type=VehicleType.MOTO,
                brand="Yamaha",
                model="FZ",
                color="Negro",
                client_id=client.id,
            ),
            Vehicle(
                license_plate="CAR001",
                type=VehicleType.CARRO,
                brand="Chevrolet",
                model="Onix",
                color="Blanco",
                client_id=client.id,
            ),
            Vehicle(
                license_plate="HIS001",
                type=VehicleType.CARRO,
                brand="Renault",
                model="Logan",
                color="Rojo",
                client_id=client.id,
            ),
        ]
    )
    session.commit()


def test_empty_state_lists_free_cells_and_zero_active_movements(
    client: TestClient, session: Session
) -> None:
    create_parking_data(session)

    cells = client.get("/api/celdas")
    movements = client.get("/api/movimientos/activos")
    report = client.get("/api/reportes/ocupacion")

    assert cells.status_code == movements.status_code == report.status_code == 200
    assert cells.json() == [
        {"codigo": "A-01", "categoria": "AUTOMOVIL", "estado": "disponible", "placa": None},
        {"codigo": "A-02", "categoria": "AUTOMOVIL", "estado": "disponible", "placa": None},
        {"codigo": "M-01", "categoria": "MOTO", "estado": "disponible", "placa": None},
        {"codigo": "M-02", "categoria": "MOTO", "estado": "disponible", "placa": None},
    ]
    assert movements.json() == []
    assert report.json() == {
        "vehiculos_registrados": 3,
        "vehiculos_presentes": 0,
        "moto": {"capacidad": 2, "ocupadas": 0, "disponibles": 2},
        "automovil": {"capacidad": 2, "ocupadas": 0, "disponibles": 2},
        "total": {"capacidad": 4, "ocupadas": 0, "disponibles": 4},
    }


def test_open_stays_define_cell_status_and_active_movements_in_stable_order(
    client: TestClient, session: Session
) -> None:
    create_parking_data(session)
    spots = {spot.code: spot for spot in session.query(ParkingSpot).all()}
    vehicles = {vehicle.license_plate: vehicle for vehicle in session.query(Vehicle).all()}
    operator = session.query(Operator).one()
    earlier = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    later = datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc)
    session.add_all(
        [
            ParkingStay(
                vehicle_id=vehicles["MOT001"].id,
                parking_spot_id=spots["M-02"].id,
                entry_operator_id=operator.id,
                entered_at=later,
            ),
            ParkingStay(
                vehicle_id=vehicles["CAR001"].id,
                parking_spot_id=spots["A-01"].id,
                entry_operator_id=operator.id,
                entered_at=earlier,
            ),
            ParkingStay(
                vehicle_id=vehicles["HIS001"].id,
                parking_spot_id=spots["A-02"].id,
                entry_operator_id=operator.id,
                entered_at=earlier,
                exit_operator_id=operator.id,
                exited_at=later,
            ),
        ]
    )
    session.commit()

    cells = client.get("/api/celdas")
    movements = client.get("/api/movimientos/activos")
    report = client.get("/api/reportes/ocupacion")

    assert cells.json() == [
        {"codigo": "A-01", "categoria": "AUTOMOVIL", "estado": "ocupada", "placa": "CAR001"},
        {"codigo": "A-02", "categoria": "AUTOMOVIL", "estado": "disponible", "placa": None},
        {"codigo": "M-01", "categoria": "MOTO", "estado": "disponible", "placa": None},
        {"codigo": "M-02", "categoria": "MOTO", "estado": "ocupada", "placa": "MOT001"},
    ]
    movement_data = movements.json()
    assert [movement["placa"] for movement in movement_data] == ["CAR001", "MOT001"]
    assert [movement["celda"] for movement in movement_data] == ["A-01", "M-02"]
    assert [movement["permanencia_id"] for movement in movement_data] == [2, 1]
    assert [
        datetime.fromisoformat(movement["fecha_entrada"]).astimezone(timezone.utc)
        for movement in movement_data
    ] == [earlier, later]
    assert report.json() == {
        "vehiculos_registrados": 3,
        "vehiculos_presentes": 2,
        "moto": {"capacidad": 2, "ocupadas": 1, "disponibles": 1},
        "automovil": {"capacidad": 2, "ocupadas": 1, "disponibles": 1},
        "total": {"capacidad": 4, "ocupadas": 2, "disponibles": 2},
    }


def test_occupancy_report_has_category_counts_and_consistent_totals(
    client: TestClient, session: Session
) -> None:
    create_parking_data(session)
    spots = {spot.code: spot for spot in session.query(ParkingSpot).all()}
    vehicles = {vehicle.license_plate: vehicle for vehicle in session.query(Vehicle).all()}
    operator = session.query(Operator).one()
    session.add_all(
        [
            ParkingStay(
                vehicle_id=vehicles["MOT001"].id,
                parking_spot_id=spots["M-01"].id,
                entry_operator_id=operator.id,
                entered_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
            ParkingStay(
                vehicle_id=vehicles["CAR001"].id,
                parking_spot_id=spots["A-01"].id,
                entry_operator_id=operator.id,
                entered_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
        ]
    )
    session.commit()

    report = client.get("/api/reportes/ocupacion")

    assert report.status_code == 200
    assert report.json() == {
        "vehiculos_registrados": 3,
        "vehiculos_presentes": 2,
        "moto": {"capacidad": 2, "ocupadas": 1, "disponibles": 1},
        "automovil": {"capacidad": 2, "ocupadas": 1, "disponibles": 1},
        "total": {"capacidad": 4, "ocupadas": 2, "disponibles": 2},
    }


@pytest.mark.parametrize(
    ("path", "method_name"),
    [
        ("/api/celdas", "list_cells"),
        ("/api/movimientos/activos", "list_active_movements"),
        ("/api/reportes/ocupacion", "occupancy_report"),
    ],
)
def test_query_failures_use_the_common_error_contract(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    method_name: str,
) -> None:
    from app.services.occupancy import OccupancyService

    def fail(*args, **kwargs):
        raise RuntimeError("simulated query failure")

    monkeypatch.setattr(OccupancyService, method_name, fail)

    response = client.get(path)

    assert response.status_code == 500
    assert response.json() == {
        "code": "OCCUPANCY_QUERY_FAILED",
        "message": "No fue posible consultar la ocupación.",
        "details": None,
    }
