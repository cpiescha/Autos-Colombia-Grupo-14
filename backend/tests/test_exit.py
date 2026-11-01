from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.exits import router
from app.db.base import Base
from app.db.session import get_db
from app.models import Client, Operator, ParkingSpot, ParkingStay, Receipt, Vehicle
from app.models.enums import SpotCategory, VehicleType


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    try:
        yield factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(router)

    def override_get_db() -> Iterator[Session]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


def create_exit_data(
    session_factory: sessionmaker[Session],
    *,
    receipt_code: str = "mIxEd-case_receipt",
    receipt_used_at: datetime | None = None,
    stay_exited_at: datetime | None = None,
) -> tuple[int, int]:
    with session_factory.begin() as session:
        client = Client(name="Cliente de prueba")
        entry_operator = Operator(name="Operario de entrada")
        exit_operator = Operator(name="Operario de salida")
        spot = ParkingSpot(code="A-01", category=SpotCategory.AUTOMOVIL)
        session.add_all([client, entry_operator, exit_operator, spot])
        session.flush()

        vehicle = Vehicle(
            license_plate="ABC123",
            type=VehicleType.CARRO,
            brand="Mazda",
            model="3",
            color="Rojo",
            client_id=client.id,
        )
        session.add(vehicle)
        session.flush()

        stay = ParkingStay(
            vehicle_id=vehicle.id,
            parking_spot_id=spot.id,
            entry_operator_id=entry_operator.id,
            entered_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            exit_operator_id=exit_operator.id if stay_exited_at else None,
            exited_at=stay_exited_at,
        )
        session.add(stay)
        session.flush()
        session.add(
            Receipt(
                code=receipt_code,
                parking_stay_id=stay.id,
                used_at=receipt_used_at,
            )
        )
        return exit_operator.id, stay.id


def assert_error(response, status_code: int, code: str, message: str) -> None:
    assert response.status_code == status_code
    assert response.json() == {"code": code, "message": message, "details": None}


def test_previews_vehicle_and_spot_without_changing_state(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _, stay_id = create_exit_data(session_factory, receipt_code="AbC_123-xYz")

    response = client.get("/api/salidas/comprobantes/AbC_123-xYz")

    assert response.status_code == 200
    body = response.json()
    assert body["permanencia_id"] == stay_id
    assert body["placa"] == "ABC123"
    assert body["celda"] == "A-01"
    assert datetime.fromisoformat(body["fecha_entrada"]) == datetime(2025, 1, 1)
    with session_factory() as session:
        stay = session.get(ParkingStay, stay_id)
        receipt = session.scalar(select(Receipt))
        assert stay is not None and stay.exited_at is None
        assert receipt is not None and receipt.used_at is None


def test_preview_rejects_wrong_receipt_case(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    create_exit_data(session_factory, receipt_code="AbC_123-xYz")

    response = client.get("/api/salidas/comprobantes/abc_123-xyz")

    assert_error(response, 404, "RECEIPT_NOT_FOUND", "El comprobante no existe.")


def test_confirms_exit_and_frees_spot(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    operator_id, stay_id = create_exit_data(session_factory)

    response = client.post(
        "/api/salidas",
        json={"comprobante": "  mIxEd-case_receipt  ", "operario_id": operator_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["permanencia_id"] == stay_id
    assert body["placa"] == "ABC123"
    assert body["celda"] == "A-01"
    assert datetime.fromisoformat(body["fecha_entrada"]) == datetime(2025, 1, 1)
    assert datetime.fromisoformat(body["fecha_salida"])
    with session_factory() as session:
        stay = session.get(ParkingStay, stay_id)
        receipt = session.scalar(select(Receipt))
        assert stay is not None and stay.exited_at is not None
        assert stay.exit_operator_id == operator_id
        assert receipt is not None and receipt.used_at == stay.exited_at


def test_accepts_a_mixed_case_receipt_code_without_normalizing_case(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    operator_id, _ = create_exit_data(session_factory, receipt_code="AbC_123-xYz")

    response = client.post(
        "/api/salidas",
        json={"comprobante": " AbC_123-xYz ", "operario_id": operator_id},
    )

    assert response.status_code == 200


def test_rejects_an_unknown_receipt(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    operator_id, _ = create_exit_data(session_factory)

    response = client.post(
        "/api/salidas",
        json={"comprobante": "desconocido", "operario_id": operator_id},
    )

    assert_error(response, 404, "RECEIPT_NOT_FOUND", "El comprobante no existe.")


def test_rejects_an_already_used_receipt(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    operator_id, _ = create_exit_data(
        session_factory,
        receipt_used_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
    )

    response = client.post(
        "/api/salidas",
        json={"comprobante": "mIxEd-case_receipt", "operario_id": operator_id},
    )

    assert_error(
        response,
        409,
        "RECEIPT_ALREADY_USED",
        "El comprobante ya fue utilizado.",
    )


def test_rejects_a_receipt_for_a_closed_stay(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    operator_id, _ = create_exit_data(
        session_factory,
        stay_exited_at=datetime(2025, 1, 2, tzinfo=timezone.utc),
    )

    response = client.post(
        "/api/salidas",
        json={"comprobante": "mIxEd-case_receipt", "operario_id": operator_id},
    )

    assert_error(
        response,
        409,
        "STAY_ALREADY_CLOSED",
        "La permanencia ya está cerrada.",
    )


def test_rejects_an_unknown_operator_without_state_changes(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    _, stay_id = create_exit_data(session_factory)

    response = client.post(
        "/api/salidas",
        json={"comprobante": "mIxEd-case_receipt", "operario_id": 999},
    )

    assert_error(response, 422, "OPERATOR_NOT_FOUND", "El operario no está registrado.")
    with session_factory() as session:
        stay = session.get(ParkingStay, stay_id)
        receipt = session.scalar(select(Receipt))
        assert stay is not None and stay.exited_at is None
        assert receipt is not None and receipt.used_at is None


@pytest.mark.parametrize(
    "payload",
    [
        {"comprobante": "   ", "operario_id": 1},
        {"comprobante": "valid", "operario_id": 0},
        {"comprobante": "valid", "operario_id": "1"},
    ],
)
def test_rejects_invalid_exit_data_with_the_common_error_shape(
    client: TestClient, payload: dict[str, object]
) -> None:
    response = client.post("/api/salidas", json=payload)

    assert_error(
        response,
        422,
        "INVALID_EXIT_DATA",
        "Los datos de salida no son válidos.",
    )


def test_rolls_back_when_exit_confirmation_fails(
    client: TestClient,
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.services.exit as exit_service

    operator_id, stay_id = create_exit_data(session_factory)
    original_close = exit_service.close_stay_by_receipt

    def fail_after_close(*args, **kwargs):
        original_close(*args, **kwargs)
        raise RuntimeError("simulated persistence failure")

    monkeypatch.setattr(exit_service, "close_stay_by_receipt", fail_after_close)

    response = client.post(
        "/api/salidas",
        json={"comprobante": "mIxEd-case_receipt", "operario_id": operator_id},
    )

    assert_error(
        response,
        500,
        "EXIT_CONFIRMATION_FAILED",
        "No fue posible registrar la salida.",
    )
    with session_factory() as session:
        stay = session.get(ParkingStay, stay_id)
        receipt = session.scalar(select(Receipt))
        assert stay is not None and stay.exited_at is None
        assert receipt is not None and receipt.used_at is None
