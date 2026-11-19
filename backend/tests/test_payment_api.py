from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import get_db
from app.main import app
from app.models import (
    Client,
    ClientStatusAudit,
    Membership,
    Operator,
    Payment,
    PaymentAudit,
    UserAccount,
    Vehicle,
)
from app.models.enums import AccountRole, VehicleType
from app.services.auth import create_access_token
from test_correction import session_factory


@pytest.fixture
def payment_api(session_factory, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "payment-api-test-secret-not-production-123456")
    cutoff = datetime(2026, 12, 20, tzinfo=timezone.utc)
    with session_factory.begin() as db:
        db.add(Client(id=70, name="Cliente API pagos"))
        db.add(Vehicle(
            id=70,
            license_plate="API070",
            type=VehicleType.CARRO,
            brand="Renault",
            model="Logan",
            color="Azul",
            client_id=70,
        ))
        db.add(Membership(
            id=70,
            vehicle_id=70,
            starts_at=cutoff - timedelta(days=30),
            expires_at=cutoff,
            current_cutoff_date=cutoff,
            activated_at=cutoff - timedelta(days=30),
        ))
        db.add_all([
            Operator(id=70, name="Operador API pagos"),
            Operator(id=71, name="Administrador API pagos"),
        ])
        db.add_all([
            UserAccount(
                id=70,
                operator_id=70,
                username="payment-operator",
                password_hash="unused",
                role=AccountRole.OPERADOR,
            ),
            UserAccount(
                id=71,
                operator_id=71,
                username="payment-admin",
                password_hash="unused",
                role=AccountRole.ADMINISTRADOR,
            ),
        ])

    def database():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = database
    try:
        with TestClient(app) as client:
            yield {
                "client": client,
                "factory": session_factory,
                "cutoff": cutoff,
                "operator_token": create_access_token(70),
                "admin_token": create_access_token(71),
            }
    finally:
        app.dependency_overrides.clear()


def _body(key="payment-api-001"):
    return {
        "vehiculo_id": 70,
        "valor": "120000.00",
        "medio": "EFECTIVO",
        "clave_idempotencia": key,
        "fecha_pago": "2026-12-05T14:30:00+00:00",
    }


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _counts(factory):
    with factory() as db:
        return (
            db.scalar(select(func.count()).select_from(Payment)),
            db.scalar(select(func.count()).select_from(PaymentAudit)),
            db.get(Membership, 70).current_cutoff_date,
        )


@pytest.mark.parametrize(
    ("token_key", "account_id"),
    [("operator_token", 70), ("admin_token", 71)],
)
def test_operator_and_admin_register_with_authenticated_identity(
    payment_api,
    token_key,
    account_id,
):
    client = payment_api["client"]
    factory = payment_api["factory"]
    body = _body(f"payment-role-{account_id}")

    forged = client.post(
        "/api/pagos",
        json={**body, "responsable_id": 999},
        headers=_headers(payment_api[token_key]),
    )
    assert forged.status_code == 422
    assert forged.json() == {
        "code": "INVALID_PAYMENT_DATA",
        "message": "Los datos del pago no son válidos.",
        "details": None,
    }
    assert _counts(factory)[:2] == (0, 0)

    response = client.post(
        "/api/pagos",
        json=body,
        headers=_headers(payment_api[token_key]),
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert set(payload) == {
        "id",
        "vehiculo_id",
        "cliente_id",
        "mensualidad_id",
        "estado",
        "valor",
        "medio",
        "fecha_pago",
        "cobertura_desde",
        "fecha_corte",
        "fecha_corte_anterior",
        "responsable_id",
    }
    assert payload["vehiculo_id"] == 70
    assert payload["cliente_id"] == 70
    assert payload["mensualidad_id"] == 70
    assert payload["estado"] == "REGISTERED"
    assert Decimal(str(payload["valor"])) == Decimal("120000.00")
    assert payload["medio"] == "EFECTIVO"
    assert payload["responsable_id"] == account_id
    with factory() as db:
        payment = db.get(Payment, payload["id"])
        assert payment.recorded_by == account_id
        assert db.scalar(select(func.count()).select_from(PaymentAudit)) == 1
        membership = db.get(Membership, 70)
        assert membership.last_payment_id == payment.id


def test_same_idempotency_key_replays_original_without_second_mutation(payment_api):
    client = payment_api["client"]
    factory = payment_api["factory"]
    headers = _headers(payment_api["operator_token"])
    body = _body("payment-api-replay")

    first = client.post("/api/pagos", json=body, headers=headers)
    replay = client.post("/api/pagos", json=body, headers=headers)

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json() == first.json()
    payments, audits, cutoff = _counts(factory)
    assert payments == 1
    assert audits == 1
    assert cutoff.replace(tzinfo=timezone.utc) == payment_api["cutoff"] + timedelta(days=30)


@pytest.mark.parametrize(
    ("owner", "other"),
    [("admin_token", "operator_token"), ("operator_token", "admin_token")],
)
def test_cross_account_idempotency_replay_is_conflict_without_mutation(
    payment_api, owner, other,
):
    client = payment_api["client"]
    factory = payment_api["factory"]
    body = _body("payment-cross-account")
    first = client.post(
        "/api/pagos", json=body, headers=_headers(payment_api[owner]),
    )
    assert first.status_code == 201

    def snapshot():
        with factory() as db:
            return {
                model.__tablename__: db.execute(select(model.__table__)).all()
                for model in (Payment, PaymentAudit, ClientStatusAudit, Membership, Client)
            }

    before = snapshot()
    counts_before = _counts(factory)
    response = client.post(
        "/api/pagos", json=body, headers=_headers(payment_api[other]),
    )

    assert response.status_code == 409
    assert response.json() == {
        "code": "IDEMPOTENCY_CONFLICT",
        "message": "La clave de idempotencia no está disponible.",
        "details": None,
    }
    assert snapshot() == before
    assert _counts(factory) == counts_before
    replay = client.post(
        "/api/pagos", json=body, headers=_headers(payment_api[owner]),
    )
    assert replay.status_code == 201
    assert replay.json() == first.json()
    assert snapshot() == before


def test_unauthenticated_registration_leaves_payment_state_unchanged(payment_api):
    before = _counts(payment_api["factory"])

    response = payment_api["client"].post("/api/pagos", json=_body())

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_SESSION"
    assert response.headers["www-authenticate"] == "Bearer"
    assert _counts(payment_api["factory"]) == before


@pytest.mark.parametrize(
    "change",
    [
        {"valor": "0"},
        {"medio": "CHEQUE"},
        {"clave_idempotencia": ""},
        {"fecha_pago": "2026-12-05T14:30:00"},
    ],
)
def test_invalid_payment_data_returns_422_without_mutation(payment_api, change):
    before = _counts(payment_api["factory"])

    response = payment_api["client"].post(
        "/api/pagos",
        json={**_body(), **change},
        headers=_headers(payment_api["operator_token"]),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_PAYMENT_DATA"
    assert _counts(payment_api["factory"]) == before


def test_missing_vehicle_returns_404_without_partial_write(payment_api):
    body = {**_body(), "vehiculo_id": 999}

    response = payment_api["client"].post(
        "/api/pagos",
        json=body,
        headers=_headers(payment_api["operator_token"]),
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "VEHICLE_NOT_FOUND",
        "message": "El vehículo no existe.",
        "details": None,
    }
    assert _counts(payment_api["factory"])[:2] == (0, 0)


def test_existing_admin_annulment_route_still_works(payment_api):
    client = payment_api["client"]
    created = client.post(
        "/api/pagos",
        json=_body("payment-api-annul"),
        headers=_headers(payment_api["operator_token"]),
    )
    payment_id = created.json()["id"]

    response = client.patch(
        f"/api/pagos/{payment_id}/anular",
        json={"motivo": "Error de registro"},
        headers=_headers(payment_api["admin_token"]),
    )

    assert response.status_code == 200, response.text
    assert response.json()["id"] == payment_id
    assert response.json()["estado"] == "ANNULLED"
    assert response.json()["motivo_anulacion"] == "Error de registro"


def _annul_snapshot(factory):
    with factory() as db:
        return [db.execute(select(model.__table__)).all()
                for model in (Payment, Membership, PaymentAudit)]


@pytest.mark.parametrize(
    "case,status,code,message",
    [
        ("operator", 403, "FORBIDDEN", "No tiene permisos para realizar esta acción."),
        ("anonymous", 401, "INVALID_SESSION", "La sesión no es válida o venció."),
        ("missing", 404, "PAYMENT_NOT_FOUND", "El pago no existe."),
        ("invalid", 422, "INVALID_PAYMENT_DATA", "Los datos del pago no son válidos."),
        ("nonlatest", 409, "PAYMENT_NOT_LATEST", "Solo se puede anular el último pago aplicado."),
        ("annulled", 409, "PAYMENT_ALREADY_ANNULLED", "El pago ya está anulado."),
    ],
)
def test_annulment_rejections_preserve_snapshot(payment_api, case, status, code, message):
    client = payment_api["client"]
    token = payment_api["admin_token"]
    first = _create_payment(client, token, "annul-first", "2026-12-05T10:00:00+00:00")
    payment_id = first["id"]
    if case == "nonlatest":
        _create_payment(client, token, "annul-second", "2026-12-06T10:00:00+00:00")
    if case == "annulled":
        _assert_annul(payment_api, first, None)
    before = _annul_snapshot(payment_api["factory"])
    response = client.patch(
        f"/api/pagos/{999 if case == 'missing' else payment_id}/anular",
        json={} if case == "invalid" else {"motivo": "Error"},
        headers={} if case == "anonymous" else _headers(
            payment_api["operator_token"] if case == "operator" else token),
    )
    assert response.status_code == status
    assert response.json() == {"code": code, "message": message, "details": None}
    assert _annul_snapshot(payment_api["factory"]) == before


def _assert_annul(api, created, predecessor):
    before = _annul_snapshot(api["factory"])
    response = api["client"].patch(
        f"/api/pagos/{created['id']}/anular", json={"motivo": " Error "},
        headers=_headers(api["admin_token"]),
    )
    assert response.status_code == 200, response.text
    with api["factory"]() as db:
        payment = db.get(Payment, created["id"])
        membership = db.get(Membership, 70)
        assert response.json() == {
            "id": payment.id, "estado": "ANNULLED", "valor": "120000.00",
            "medio": "EFECTIVO",
            "fecha_corte_anterior": payment.previous_cutoff.isoformat(),
            "anulado_en": payment.annulled_at.isoformat(), "motivo_anulacion": "Error",
        }
        assert payment.status == "ANNULLED"
        assert payment.annulled_by == 71
        assert membership.current_cutoff_date == payment.previous_cutoff
        assert membership.expires_at == payment.previous_cutoff
        assert membership.last_payment_id == predecessor
        audits = db.scalars(select(PaymentAudit).where(
            PaymentAudit.payment_id == payment.id, PaymentAudit.action == "ANNUL")).all()
        assert len(audits) == 1
        audit = audits[0]
        assert audit.account_id == 71
        assert audit.previous_state == {
            "status": "REGISTERED",
            "current_cutoff_date": before[1][0].current_cutoff_date.isoformat(),
            "expires_at": before[1][0].expires_at.isoformat(),
            "last_payment_id": payment.id,
        }
        assert audit.new_state == {
            "status": "ANNULLED", "current_cutoff_date": payment.previous_cutoff.isoformat(),
            "expires_at": payment.previous_cutoff.isoformat(),
            "last_payment_id": predecessor, "reason": "Error",
        }
    after = _annul_snapshot(api["factory"])
    assert len(after[0]) == len(before[0])
    assert len(after[2]) == len(before[2]) + 1
    assert [row for row in after[0] if row.id != created["id"]] == [
        row for row in before[0] if row.id != created["id"]]
    assert after[2][:-1] == before[2]


def test_repeated_lifo_annulments_restore_predecessor_then_null(payment_api):
    client = payment_api["client"]
    token = payment_api["admin_token"]
    first = _create_payment(client, token, "lifo-first", "2026-12-06T10:00:00+00:00")
    second = _create_payment(client, token, "lifo-second", "2026-12-05T10:00:00+00:00")
    _assert_annul(payment_api, second, first["id"])
    third = _create_payment(client, token, "lifo-third", "2026-12-07T10:00:00+00:00")
    _assert_annul(payment_api, third, first["id"])
    _assert_annul(payment_api, first, None)


READ_FIELDS = {
    "id",
    "vehiculo_id",
    "cliente_id",
    "mensualidad_id",
    "estado",
    "valor",
    "medio",
    "fecha_pago",
    "cobertura_desde",
    "fecha_corte",
    "fecha_corte_anterior",
    "responsable_id",
    "anulado_en",
    "anulado_por_id",
    "motivo_anulacion",
}


def _create_payment(client, token, key, paid_at):
    response = client.post(
        "/api/pagos",
        json={**_body(key), "fecha_pago": paid_at},
        headers=_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_payment_list_requires_authentication(payment_api):
    response = payment_api["client"].get("/api/pagos")

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_SESSION"
    assert response.headers["www-authenticate"] == "Bearer"


def test_operator_sees_own_payments_and_admin_sees_all(payment_api):
    client = payment_api["client"]
    operator_payment = _create_payment(
        client,
        payment_api["operator_token"],
        "payment-list-operator",
        "2026-12-05T10:00:00+00:00",
    )
    admin_payment = _create_payment(
        client,
        payment_api["admin_token"],
        "payment-list-admin",
        "2026-12-06T10:00:00+00:00",
    )

    operator_response = client.get(
        "/api/pagos",
        headers=_headers(payment_api["operator_token"]),
    )
    admin_response = client.get(
        "/api/pagos",
        headers=_headers(payment_api["admin_token"]),
    )

    assert operator_response.status_code == 200
    assert [item["id"] for item in operator_response.json()] == [operator_payment["id"]]
    assert set(operator_response.json()[0]) == READ_FIELDS
    assert operator_response.json()[0]["responsable_id"] == 70
    assert admin_response.status_code == 200
    assert [item["id"] for item in admin_response.json()] == [
        admin_payment["id"],
        operator_payment["id"],
    ]
    assert all(set(item) == READ_FIELDS for item in admin_response.json())


def test_payment_detail_respects_operator_ownership_and_admin_access(payment_api):
    client = payment_api["client"]
    operator_payment = _create_payment(
        client,
        payment_api["operator_token"],
        "payment-detail-operator",
        "2026-12-05T10:00:00+00:00",
    )
    admin_payment = _create_payment(
        client,
        payment_api["admin_token"],
        "payment-detail-admin",
        "2026-12-06T10:00:00+00:00",
    )

    own = client.get(
        f"/api/pagos/{operator_payment['id']}",
        headers=_headers(payment_api["operator_token"]),
    )
    hidden = client.get(
        f"/api/pagos/{admin_payment['id']}",
        headers=_headers(payment_api["operator_token"]),
    )
    admin = client.get(
        f"/api/pagos/{operator_payment['id']}",
        headers=_headers(payment_api["admin_token"]),
    )

    assert own.status_code == 200
    assert own.json()["id"] == operator_payment["id"]
    assert set(own.json()) == READ_FIELDS
    assert hidden.status_code == 404
    assert hidden.json()["code"] == "PAYMENT_NOT_FOUND"
    assert admin.status_code == 200
    assert admin.json()["id"] == operator_payment["id"]


def test_unknown_payment_detail_returns_payment_not_found(payment_api):
    response = payment_api["client"].get(
        "/api/pagos/999",
        headers=_headers(payment_api["operator_token"]),
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "PAYMENT_NOT_FOUND",
        "message": "El pago no existe.",
        "details": None,
    }


def test_payment_list_is_sorted_by_payment_date_desc_then_id_desc(payment_api):
    client = payment_api["client"]
    token = payment_api["operator_token"]
    older = _create_payment(
        client,
        token,
        "payment-order-older",
        "2026-12-04T10:00:00+00:00",
    )
    same_date_first = _create_payment(
        client,
        token,
        "payment-order-first",
        "2026-12-06T10:00:00+00:00",
    )
    same_date_second = _create_payment(
        client,
        token,
        "payment-order-second",
        "2026-12-06T10:00:00+00:00",
    )

    response = client.get("/api/pagos", headers=_headers(token))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [
        same_date_second["id"],
        same_date_first["id"],
        older["id"],
    ]
