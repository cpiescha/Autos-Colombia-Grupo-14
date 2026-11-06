from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_current_account
from app.api.occupancy import router
from app.api.parking_spots import router as parking_spots_router
from app.db.base import Base
from app.db.session import get_db
from app.models import (
    CellCorrection,
    Client,
    Operator,
    ParkingSpot,
    ParkingStay,
    Receipt,
    Vehicle,
)
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
    app.include_router(parking_spots_router)

    def get_test_db() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_current_account] = lambda: SimpleNamespace(id=1, operator_id=1)
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
            ParkingSpot(
                code="A-02",
                category=SpotCategory.AUTOMOVIL,
                active=False,
            ),
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


def test_empty_state_excludes_inactive_cells_from_available_capacity(
    client: TestClient, session: Session
) -> None:
    create_parking_data(session)

    movements = client.get("/api/movimientos/activos")
    report = client.get("/api/reportes/ocupacion")

    assert movements.status_code == report.status_code == 200
    assert movements.json() == []
    assert report.json() == {
        "vehiculos_registrados": 3,
        "vehiculos_presentes": 0,
        "moto": {"capacidad": 2, "ocupadas": 0, "disponibles": 2},
        "automovil": {"capacidad": 1, "ocupadas": 0, "disponibles": 1},
        "total": {"capacidad": 3, "ocupadas": 0, "disponibles": 3},
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

    assert cells.status_code == 200
    cells_by_code = {cell["codigo"]: cell for cell in cells.json()}
    assert cells_by_code["A-02"]["estado"] == "inactiva"
    assert cells_by_code["A-02"]["placa"] is None

    movement_data = movements.json()
    assert [movement["placa"] for movement in movement_data] == ["CAR001", "MOT001"]
    assert [movement["celda"] for movement in movement_data] == ["A-01", "M-02"]
    assert [movement["permanencia_id"] for movement in movement_data] == [2, 1]
    assert [movement["operario_entrada"] for movement in movement_data] == [
        "Operario de prueba",
        "Operario de prueba",
    ]
    assert [
        datetime.fromisoformat(movement["fecha_entrada"]).astimezone(timezone.utc)
        for movement in movement_data
    ] == [earlier, later]
    assert report.json() == {
        "vehiculos_registrados": 3,
        "vehiculos_presentes": 2,
        "moto": {"capacidad": 2, "ocupadas": 1, "disponibles": 1},
        "automovil": {"capacidad": 1, "ocupadas": 1, "disponibles": 0},
        "total": {"capacidad": 3, "ocupadas": 2, "disponibles": 1},
    }


def test_history_returns_closed_stays_and_persisted_corrections_after_reload(
    client: TestClient, session: Session
) -> None:
    create_parking_data(session)
    spots = {spot.code: spot for spot in session.query(ParkingSpot).all()}
    vehicles = {vehicle.license_plate: vehicle for vehicle in session.query(Vehicle).all()}
    operator = session.query(Operator).one()
    entered_at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    corrected_at = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)
    exited_at = datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc)
    stay = ParkingStay(
        vehicle_id=vehicles["HIS001"].id,
        parking_spot_id=spots["A-02"].id,
        entry_operator_id=operator.id,
        entered_at=entered_at,
        exit_operator_id=operator.id,
        exited_at=exited_at,
    )
    session.add(stay)
    session.flush()
    session.add_all(
        [
            Receipt(code="HISTORICO-001", parking_stay_id=stay.id, used_at=exited_at),
            CellCorrection(
                parking_stay_id=stay.id,
                previous_spot_id=spots["A-01"].id,
                new_spot_id=spots["A-02"].id,
                operator_id=operator.id,
                corrected_at=corrected_at,
            ),
        ]
    )
    session.commit()

    response = client.get("/api/movimientos/historial")

    assert response.status_code == 200
    assert response.json() == [
        {
            "permanencia_id": stay.id,
            "placa": "HIS001",
            "celda_final": "A-02",
            "fecha_entrada": entered_at.isoformat().replace("+00:00", "Z"),
            "fecha_salida": exited_at.isoformat().replace("+00:00", "Z"),
            "comprobante": "HISTORICO-001",
            "operario_entrada": "Operario de prueba",
            "operario_salida": "Operario de prueba",
            "correcciones": [
                {
                    "celda_anterior": "A-01",
                    "celda_nueva": "A-02",
                    "operario": "Operario de prueba",
                    "fecha_correccion": corrected_at.isoformat().replace("+00:00", "Z"),
                }
            ],
        }
    ]


def test_history_excludes_open_stays(
    client: TestClient, session: Session
) -> None:
    create_parking_data(session)
    spots = {spot.code: spot for spot in session.query(ParkingSpot).all()}
    vehicles = {vehicle.license_plate: vehicle for vehicle in session.query(Vehicle).all()}
    operator = session.query(Operator).one()
    session.add(
        ParkingStay(
            vehicle_id=vehicles["CAR001"].id,
            parking_spot_id=spots["A-01"].id,
            entry_operator_id=operator.id,
            entered_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )
    session.commit()

    response = client.get("/api/movimientos/historial")

    assert response.status_code == 200
    assert response.json() == []


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
        "automovil": {"capacidad": 1, "ocupadas": 1, "disponibles": 0},
        "total": {"capacidad": 3, "ocupadas": 2, "disponibles": 1},
    }


@pytest.mark.parametrize(
    ("path", "method_name"),
    [
        ("/api/movimientos/activos", "list_active_movements"),
        ("/api/movimientos/historial", "list_movement_history"),
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
