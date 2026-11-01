from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_vehicle_repository
from app.main import app


class FakeVehicleRepository:
    def __init__(self) -> None:
        now = datetime.now(timezone.utc)
        self.vehicles = {
            "ABC123": SimpleNamespace(
                id=1,
                license_plate="ABC123",
                type="CARRO",
                brand="Chevrolet",
                model="Onix",
                color="Blanco",
            ),
            "VENC001": SimpleNamespace(
                id=2,
                license_plate="VENC001",
                type="MOTO",
                brand="Yamaha",
                model="FZ",
                color="Negro",
            ),
            "CAM001": SimpleNamespace(
                id=3,
                license_plate="CAM001",
                type="CAMION",
                brand="Volvo",
                model="FMX",
                color="Azul",
            ),
            "ABI001": SimpleNamespace(
                id=4,
                license_plate="ABI001",
                type="CARRO",
                brand="Renault",
                model="Logan",
                color="Rojo",
            ),
        }
        self.memberships = {
            1: (now - timedelta(days=1), now + timedelta(days=1)),
            2: (now - timedelta(days=2), now - timedelta(days=1)),
            3: (now - timedelta(days=1), now + timedelta(days=1)),
            4: (now - timedelta(days=1), now + timedelta(days=1)),
        }
        self.open_stay_vehicle_ids = {4}
        self.queried_plates: list[str] = []

    def find_by_plate(self, plate: str):
        self.queried_plates.append(plate)
        return self.vehicles.get(plate)

    def has_active_membership(self, vehicle_id: int, at: datetime) -> bool:
        starts_at, expires_at = self.memberships[vehicle_id]
        return starts_at <= at <= expires_at

    def has_open_stay(self, vehicle_id: int) -> bool:
        return vehicle_id in self.open_stay_vehicle_ids

    def state(self) -> tuple[dict[str, object], dict[int, tuple[datetime, datetime]], set[int]]:
        return (
            deepcopy(self.vehicles),
            deepcopy(self.memberships),
            deepcopy(self.open_stay_vehicle_ids),
        )


@pytest.fixture
def repository() -> FakeVehicleRepository:
    return FakeVehicleRepository()


@pytest.fixture
def client(repository: FakeVehicleRepository):
    app.dependency_overrides[get_vehicle_repository] = lambda: repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_normalizes_plate_before_looking_up_vehicle(
    client: TestClient, repository: FakeVehicleRepository
) -> None:
    response = client.get("/api/vehiculos/%20abc123%20")

    assert response.status_code == 200
    assert repository.queried_plates == ["ABC123"]


def test_returns_existing_vehicle_with_authorization_data(client: TestClient) -> None:
    response = client.get("/api/vehiculos/ABC123")

    assert response.status_code == 200
    assert response.json() == {
        "placa": "ABC123",
        "tipo": "CARRO",
        "marca": "Chevrolet",
        "modelo": "Onix",
        "color": "Blanco",
        "estado_mensualidad": "vigente",
        "authorized": True,
        "rejection_reason": None,
    }


def test_returns_404_only_when_vehicle_does_not_exist(client: TestClient) -> None:
    response = client.get("/api/vehiculos/NOEXISTE")

    assert response.status_code == 404
    assert response.json() == {"detail": "Vehículo no registrado."}


def test_reports_expired_membership_without_hiding_vehicle_data(client: TestClient) -> None:
    response = client.get("/api/vehiculos/VENC001")

    assert response.status_code == 200
    assert response.json()["estado_mensualidad"] == "vencida"
    assert response.json()["authorized"] is False
    assert response.json()["rejection_reason"] == "La mensualidad no está vigente."
    assert response.json()["placa"] == "VENC001"


def test_reports_disallowed_vehicle_type_without_hiding_vehicle_data(client: TestClient) -> None:
    response = client.get("/api/vehiculos/CAM001")

    assert response.status_code == 200
    assert response.json()["estado_mensualidad"] == "vigente"
    assert response.json()["authorized"] is False
    assert response.json()["rejection_reason"] == "El tipo de vehículo no está permitido."
    assert response.json()["tipo"] == "CAMION"


def test_reports_open_stay_without_hiding_vehicle_data(client: TestClient) -> None:
    response = client.get("/api/vehiculos/ABI001")

    assert response.status_code == 200
    assert response.json()["estado_mensualidad"] == "vigente"
    assert response.json()["authorized"] is False
    assert response.json()["rejection_reason"] == "El vehículo ya tiene una permanencia abierta."


@pytest.mark.parametrize("plate", ["VENC001", "CAM001", "ABI001"])
def test_rejections_do_not_mutate_vehicles_or_occupancy(
    client: TestClient, repository: FakeVehicleRepository, plate: str
) -> None:
    before = repository.state()

    response = client.get(f"/api/vehiculos/{plate}")

    assert response.status_code == 200
    assert response.json()["authorized"] is False
    assert repository.state() == before
