from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Operator, ParkingSpot, ParkingStay, Receipt, UserAccount, Vehicle
from app.models.cell_correction import CellCorrection
from app.models.enums import AccountRole, SpotCategory, VehicleType
from app.models.membership import Membership
from app.schemas.entry import EntryCreateRequest
from app.schemas.exit import ExitCreateRequest
from app.schemas.correction import CellCorrectionRequest
from app.services.auth import create_access_token
from test_correction import session_factory


@pytest.fixture
def operational(session_factory, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "operational-test-secret-not-production-123456")
    with session_factory.begin() as db:
        db.add(Operator(id=7, name="Authenticated actor"))
        db.add(UserAccount(id=17, operator_id=7, username="actor", password_hash="unused", role=AccountRole.OPERADOR))
        db.add(Receipt(code="existing", parking_stay_id=1))
        db.add(ParkingSpot(id=7, code="A-00", category=SpotCategory.AUTOMOVIL))
        db.add(Vehicle(id=4, license_plate="NEW001", type=VehicleType.CARRO, brand="Test", model="Test", color="Blue", client_id=1))
        db.add(Membership(vehicle_id=4, starts_at=datetime.now(timezone.utc) - timedelta(days=1), expires_at=datetime.now(timezone.utc) + timedelta(days=1)))
    def database():
        with session_factory() as db:
            yield db
    app.dependency_overrides[get_db] = database
    try:
        with TestClient(app) as client:
            yield client, session_factory, create_access_token(17)
    finally:
        app.dependency_overrides.clear()


def snapshot(factory):
    with factory() as db:
        return {table.name: list(db.execute(select(table)).all()) for table in Base.metadata.sorted_tables}


OPERATIONS = [
    ("post", "/api/entradas", {"placa": "NEW001"}),
    ("get", "/api/salidas/comprobantes/existing", None),
    ("post", "/api/salidas", {"comprobante": "existing"}),
    ("get", "/api/movimientos/activos", None),
    ("get", "/api/reportes/ocupacion", None),
    ("patch", "/api/movimientos/1/celda", {"celda": "A-02"}),
]


@pytest.mark.parametrize("method,path,payload", OPERATIONS)
@pytest.mark.parametrize("session_kind", ["missing", "invalid", "inactive"])
def test_rejected_sessions_do_not_change_any_state(operational, method, path, payload, session_kind):
    client, factory, token = operational
    if session_kind == "inactive":
        with factory.begin() as db:
            db.get(UserAccount, 17).active = False
    headers = {} if session_kind == "missing" else {"Authorization": f"Bearer {token if session_kind == 'inactive' else 'invalid'}"}
    before = snapshot(factory)
    response = client.request(method, path, json=payload, headers=headers)
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_SESSION"
    assert response.headers["www-authenticate"] == "Bearer"
    assert snapshot(factory) == before


@pytest.mark.parametrize("role", list(AccountRole))
def test_both_roles_operate_and_persist_authenticated_actor(operational, role):
    client, factory, token = operational
    with factory.begin() as db:
        db.get(UserAccount, 17).role = role
    client.headers["Authorization"] = f"Bearer {token}"
    # A forged legacy field must never control the persisted identity.
    entry = client.post("/api/entradas", json={"placa": "NEW001", "operario_id": 1})
    assert entry.status_code == 201, entry.text
    correction = client.patch("/api/movimientos/1/celda", json={"celda": "A-02", "operario_id": 1})
    assert correction.status_code == 200, correction.text
    assert correction.json()["operario_id"] == 7
    assert client.get("/api/salidas/comprobantes/existing").status_code == 200
    assert client.get("/api/movimientos/activos").status_code == 200
    assert client.get("/api/reportes/ocupacion").status_code == 200
    exit_response = client.post("/api/salidas", json={"comprobante": "existing", "operario_id": 1})
    assert exit_response.status_code == 200, exit_response.text
    with factory() as db:
        assert db.get(ParkingStay, entry.json()["permanencia_id"]).entry_operator_id == 7
        assert db.get(ParkingStay, 1).exit_operator_id == 7
        assert db.scalar(select(CellCorrection)).operator_id == 7


@pytest.mark.parametrize("schema,payload", [(EntryCreateRequest, {"placa": "ABC"}), (ExitCreateRequest, {"comprobante": "receipt"}), (CellCorrectionRequest, {"celda": "A-02"})])
def test_operator_is_not_part_of_request_contract(schema, payload):
    assert "operario_id" not in schema.model_json_schema()["properties"]
    assert schema.model_validate(payload)
