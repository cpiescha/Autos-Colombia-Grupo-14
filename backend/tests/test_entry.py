from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_entry_repository
from app.main import app


class FakeEntryRepository:
    def __init__(self) -> None:
        self.vehicles = {
            "MOTO001": SimpleNamespace(id=1, license_plate="MOTO001", type="MOTO"),
            "CAR001": SimpleNamespace(id=2, license_plate="CAR001", type="CARRO"),
            "CAMIONETA1": SimpleNamespace(
                id=3, license_plate="CAMIONETA1", type="CAMIONETA"
            ),
            "VENC001": SimpleNamespace(id=4, license_plate="VENC001", type="MOTO"),
            "CAMION001": SimpleNamespace(id=5, license_plate="CAMION001", type="CAMION"),
            "ABIERTA1": SimpleNamespace(id=6, license_plate="ABIERTA1", type="CARRO"),
        }
        self.operator_ids = {1}
        self.active_membership_vehicle_ids = {1, 2, 3, 5, 6}
        self.open_stay_vehicle_ids = {6}
        self.spots = [
            SimpleNamespace(id=1, code="M-02", category="MOTO"),
            SimpleNamespace(id=2, code="M-01", category="MOTO"),
            SimpleNamespace(id=3, code="A-02", category="AUTOMOVIL"),
            SimpleNamespace(id=4, code="A-01", category="AUTOMOVIL"),
        ]
        self.stays: list[SimpleNamespace] = []
        self.receipts: list[SimpleNamespace] = []
        self.fail_on_receipt = False
        self.queried_plates: list[str] = []

    @contextmanager
    def transaction(self) -> Iterator[None]:
        before = self.state()
        try:
            yield
        except Exception:
            self.restore(before)
            raise

    def find_vehicle_for_update(self, plate: str):
        self.queried_plates.append(plate)
        return self.vehicles.get(plate)

    def operator_exists(self, operator_id: int) -> bool:
        return operator_id in self.operator_ids

    def has_active_membership(self, vehicle_id: int, at: datetime) -> bool:
        return vehicle_id in self.active_membership_vehicle_ids

    def has_open_stay(self, vehicle_id: int) -> bool:
        return vehicle_id in self.open_stay_vehicle_ids

    def find_first_free_spot_for_update(self, category: str):
        occupied_spot_ids = {stay.parking_spot_id for stay in self.stays}
        available = [
            spot
            for spot in self.spots
            if spot.category == category and spot.id not in occupied_spot_ids
        ]
        return min(available, key=lambda spot: spot.code, default=None)

    def create_stay(
        self, vehicle_id: int, parking_spot_id: int, operator_id: int, entered_at: datetime
    ):
        stay = SimpleNamespace(
            id=len(self.stays) + 1,
            vehicle_id=vehicle_id,
            parking_spot_id=parking_spot_id,
            entry_operator_id=operator_id,
            entered_at=entered_at,
        )
        self.stays.append(stay)
        self.open_stay_vehicle_ids.add(vehicle_id)
        return stay

    def create_receipt(self, parking_stay_id: int, code: str) -> None:
        if self.fail_on_receipt:
            raise RuntimeError("receipt persistence failed")
        self.receipts.append(
            SimpleNamespace(parking_stay_id=parking_stay_id, code=code)
        )

    def state(self):
        return deepcopy(
            (
                self.vehicles,
                self.operator_ids,
                self.active_membership_vehicle_ids,
                self.open_stay_vehicle_ids,
                self.spots,
                self.stays,
                self.receipts,
            )
        )

    def restore(self, state) -> None:
        (
            self.vehicles,
            self.operator_ids,
            self.active_membership_vehicle_ids,
            self.open_stay_vehicle_ids,
            self.spots,
            self.stays,
            self.receipts,
        ) = state


@pytest.fixture
def repository() -> FakeEntryRepository:
    return FakeEntryRepository()


@pytest.fixture
def client(repository: FakeEntryRepository) -> Iterator[TestClient]:
    app.dependency_overrides[get_entry_repository] = lambda: repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def assert_error(response, status_code: int, code: str, message: str) -> None:
    assert response.status_code == status_code
    assert response.json() == {"code": code, "message": message, "details": None}


@pytest.mark.parametrize(
    ("plate", "expected_category", "expected_cell"),
    [
        ("MOTO001", "MOTO", "M-01"),
        ("CAR001", "AUTOMOVIL", "A-01"),
        ("CAMIONETA1", "AUTOMOVIL", "A-01"),
    ],
)
def test_creates_an_entry_in_the_first_compatible_cell(
    client: TestClient,
    repository: FakeEntryRepository,
    plate: str,
    expected_category: str,
    expected_cell: str,
) -> None:
    response = client.post("/api/entradas", json={"placa": f" {plate.lower()} ", "operario_id": 1})

    assert response.status_code == 201
    body = response.json()
    assert body["permanencia_id"] == 1
    assert body["placa"] == plate
    assert body["celda"] == expected_cell
    assert isinstance(body["comprobante"], str) and body["comprobante"]
    assert datetime.fromisoformat(body["fecha_entrada"]).tzinfo is not None
    assert len(repository.stays) == 1
    assert repository.spots[repository.stays[0].parking_spot_id - 1].category == expected_category
    assert repository.queried_plates == [plate]
    assert len(repository.receipts) == 1


def test_creates_distinct_unpredictable_receipts_for_confirmed_entries(
    client: TestClient, repository: FakeEntryRepository
) -> None:
    first = client.post("/api/entradas", json={"placa": "MOTO001", "operario_id": 1})
    second = client.post("/api/entradas", json={"placa": "CAR001", "operario_id": 1})

    assert first.status_code == second.status_code == 201
    assert first.json()["comprobante"] != second.json()["comprobante"]
    assert len(repository.receipts) == 2


def test_rejects_an_unknown_vehicle_without_persisting_state(
    client: TestClient, repository: FakeEntryRepository
) -> None:
    before = repository.state()

    response = client.post("/api/entradas", json={"placa": "NOEXISTE", "operario_id": 1})

    assert_error(response, 404, "VEHICLE_NOT_FOUND", "El vehículo no está registrado.")
    assert repository.state() == before


def test_rejects_an_unknown_operator_without_persisting_state(
    client: TestClient, repository: FakeEntryRepository
) -> None:
    before = repository.state()

    response = client.post("/api/entradas", json={"placa": "MOTO001", "operario_id": 99})

    assert_error(response, 422, "OPERATOR_NOT_FOUND", "El operario no está registrado.")
    assert repository.state() == before


def test_rejects_an_expired_membership_without_persisting_state(
    client: TestClient, repository: FakeEntryRepository
) -> None:
    before = repository.state()

    response = client.post("/api/entradas", json={"placa": "VENC001", "operario_id": 1})

    assert_error(response, 409, "MEMBERSHIP_NOT_CURRENT", "La mensualidad no está vigente.")
    assert repository.state() == before


def test_rejects_a_disallowed_vehicle_type_without_persisting_state(
    client: TestClient, repository: FakeEntryRepository
) -> None:
    before = repository.state()

    response = client.post("/api/entradas", json={"placa": "CAMION001", "operario_id": 1})

    assert_error(
        response,
        409,
        "VEHICLE_TYPE_NOT_ALLOWED",
        "El tipo de vehículo no está permitido.",
    )
    assert repository.state() == before


def test_rejects_a_vehicle_with_an_open_stay_without_persisting_state(
    client: TestClient, repository: FakeEntryRepository
) -> None:
    before = repository.state()

    response = client.post("/api/entradas", json={"placa": "ABIERTA1", "operario_id": 1})

    assert_error(response, 409, "OPEN_STAY_EXISTS", "El vehículo ya tiene una permanencia abierta.")
    assert repository.state() == before


def test_rejects_when_no_compatible_spot_is_available_without_persisting_state(
    client: TestClient, repository: FakeEntryRepository
) -> None:
    repository.stays.extend(
        [
            SimpleNamespace(parking_spot_id=1),
            SimpleNamespace(parking_spot_id=2),
        ]
    )
    before = repository.state()

    response = client.post("/api/entradas", json={"placa": "MOTO001", "operario_id": 1})

    assert_error(
        response,
        409,
        "NO_COMPATIBLE_SPACE",
        "No hay celdas disponibles para este tipo de vehículo.",
    )
    assert repository.state() == before


@pytest.mark.parametrize(
    "payload",
    [
        {"placa": "   ", "operario_id": 1},
        {"placa": "MOTO001", "operario_id": 0},
        {"placa": "MOTO001", "operario_id": "1"},
    ],
)
def test_rejects_invalid_entry_data_without_persisting_state(
    client: TestClient, repository: FakeEntryRepository, payload: dict[str, object]
) -> None:
    before = repository.state()

    response = client.post("/api/entradas", json=payload)

    assert_error(response, 422, "INVALID_ENTRY_DATA", "Los datos de entrada no son válidos.")
    assert repository.state() == before


def test_rolls_back_an_unexpected_persistence_error_without_partial_state(
    client: TestClient, repository: FakeEntryRepository
) -> None:
    repository.fail_on_receipt = True
    before = repository.state()

    response = client.post("/api/entradas", json={"placa": "MOTO001", "operario_id": 1})

    assert_error(response, 500, "ENTRY_CREATION_FAILED", "No fue posible registrar la entrada.")
    assert repository.state() == before
