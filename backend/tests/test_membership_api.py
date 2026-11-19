from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models import Client, Membership, Payment, PaymentAudit, Vehicle
from app.models.enums import VehicleType
from test_payment_api import payment_api, _headers
from test_correction import session_factory


@pytest.fixture
def membership_api(payment_api):
    today = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    with payment_api["factory"].begin() as db:
        db.add(Client(id=80, name="Cliente sin vehículos"))
        for vehicle_id, days in [(70, 0), (71, 7), (72, 8), (73, -1), (74, None)]:
            if vehicle_id != 70:
                db.add(Vehicle(id=vehicle_id, license_plate=f"API{vehicle_id:03}",
                               type=VehicleType.CARRO, brand="Renault", model="Logan",
                               color="Azul", client_id=70))
            cutoff = today + timedelta(days=days or 0)
            if vehicle_id == 70:
                membership = db.get(Membership, 70)
                membership.starts_at = today - timedelta(days=60)
                membership.expires_at = today + timedelta(days=100)
                membership.current_cutoff_date = membership.expires_at
            db.add(Membership(id=vehicle_id + 100, vehicle_id=vehicle_id,
                              starts_at=today - timedelta(days=30),
                              expires_at=cutoff + timedelta(days=100),
                              current_cutoff_date=cutoff if days is not None else None))
        db.flush()
        db.add(Payment(id=170, vehicle_id=70, client_id=70, membership_id=170,
                       amount=120000, payment_method="EFECTIVO", paid_at=today - timedelta(days=5),
                       coverage_start=today - timedelta(days=30), coverage_end=today,
                       recorded_by=71, status="REGISTERED", idempotency_key="private-key"))
        db.flush()
        db.get(Membership, 170).last_payment_id = 170
    return {**payment_api, "today": today}


def _snapshot(factory):
    with factory() as db:
        return [
            [tuple(getattr(row, column.name) for column in model.__table__.columns)
             for row in db.scalars(select(model).order_by(model.id))]
            for model in (Client, Vehicle, Membership, Payment, PaymentAudit)
        ]


def _get(api, path, role="operator_token"):
    before = _snapshot(api["factory"])
    response = api["client"].get("/api/mensualidades/" + path,
                                  headers=_headers(api[role]) if role else {})
    assert _snapshot(api["factory"]) == before
    return response


def _expected(api, vehicle_id, days, paid=False):
    return {
        "vehiculo_id": vehicle_id, "cliente_id": 70, "placa": f"API{vehicle_id:03}",
        "mensualidad_id": vehicle_id + 100,
        "fecha_corte": (api["today"] + timedelta(days=days)).replace(tzinfo=None).isoformat() if days is not None else None,
        "estado": "vigente" if days is not None and days >= 0 else "vencido",
        "fecha_ultimo_pago": (api["today"] - timedelta(days=5)).replace(tzinfo=None).isoformat() if paid else None,
    }


@pytest.mark.parametrize("path", ["vehiculo/API070", "cliente/70", "por-vencer"])
def test_all_queries_require_authentication(membership_api, path):
    response = _get(membership_api, path, None)
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_SESSION"
    assert response.json()["details"] is None
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("role", ["operator_token", "admin_token"])
@pytest.mark.parametrize("vehicle_id,days", [(70, 0), (71, 7), (73, -1), (74, None)])
def test_vehicle_current_membership_and_private_dto(membership_api, role, vehicle_id, days):
    response = _get(membership_api, f"vehiculo/api{vehicle_id:03}", role)
    assert response.status_code == 200
    assert response.json() == _expected(membership_api, vehicle_id, days, vehicle_id == 70)


@pytest.mark.parametrize("role", ["operator_token", "admin_token"])
def test_client_all_vehicles_and_empty_client(membership_api, role):
    response = _get(membership_api, "cliente/70", role)
    assert response.status_code == 200
    assert response.json() == [_expected(membership_api, v, d, v == 70)
                               for v, d in [(70, 0), (71, 7), (72, 8), (73, -1), (74, None)]]
    empty = _get(membership_api, "cliente/80", role)
    assert empty.status_code == 200
    assert empty.json() == []


@pytest.mark.parametrize("path,code,message", [
    ("vehiculo/UNKNOWN", "VEHICLE_NOT_FOUND", "El vehículo no existe."),
    ("cliente/999", "CLIENT_NOT_FOUND", "El cliente no existe."),
])
def test_missing_resources(membership_api, path, code, message):
    response = _get(membership_api, path)
    assert response.status_code == 404
    assert response.json() == {"code": code, "message": message, "details": None}


def test_vehicle_without_membership(membership_api):
    with membership_api["factory"].begin() as db:
        db.add(Vehicle(id=90, license_plate="API090", type=VehicleType.CARRO,
                       brand="Renault", model="Logan", color="Azul", client_id=80))
    response = _get(membership_api, "vehiculo/API090")
    assert response.status_code == 200
    expected = {"vehiculo_id": 90, "cliente_id": 80, "placa": "API090",
                "mensualidad_id": None, "fecha_corte": None, "estado": "vencido",
                "fecha_ultimo_pago": None}
    assert response.json() == expected
    response = _get(membership_api, "cliente/80")
    assert response.status_code == 200
    assert response.json() == [expected]


def test_expiring_forbidden_to_operator_without_disclosure(membership_api):
    response = _get(membership_api, "por-vencer")
    assert response.status_code == 403
    assert response.json()["details"] is None
    assert "API070" not in response.text
    assert "fecha_corte" not in response.text


@pytest.mark.parametrize("query,vehicles", [("", [70, 71]), ("?dias=0", [70]),
                                             ("?dias=7", [70, 71]), ("?dias=8", [70, 71, 72])])
def test_expiring_default_and_inclusive_boundaries(membership_api, query, vehicles):
    response = _get(membership_api, "por-vencer" + query, "admin_token")
    assert response.status_code == 200
    assert response.json() == [_expected(membership_api, v, {70: 0, 71: 7, 72: 8}[v], v == 70)
                               for v in vehicles]


@pytest.mark.parametrize("value", ["-1", "1.5", "abc", ""])
def test_expiring_invalid_days(membership_api, value):
    response = _get(membership_api, "por-vencer?dias=" + value, "admin_token")
    assert response.status_code == 422
    assert response.json() == {"code": "INVALID_MEMBERSHIP_DATA",
                               "message": "Los datos de consulta de mensualidad no son válidos.",
                               "details": None}
