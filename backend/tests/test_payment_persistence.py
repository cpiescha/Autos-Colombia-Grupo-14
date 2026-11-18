from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.migrations import upgrade_schema
from app.models import Client, Membership, Operator, Payment, PaymentAudit, UserAccount, Vehicle
from app.models.enums import AccountRole, VehicleType
from app.services.payment_annulment import PaymentAnnulmentError, PaymentAnnulmentService


@pytest.fixture
def session():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    upgrade_schema(engine)
    db = Session(engine)
    yield db
    db.close()
    engine.dispose()


def _account(session, username, role):
    operator = Operator(name=username)
    session.add(operator)
    session.flush()
    account = UserAccount(
        operator_id=operator.id,
        username=username,
        password_hash="not-used-in-sqlite",
        role=role,
    )
    session.add(account)
    session.flush()
    return account


def _payment(session, account, *, key, cutoff, previous):
    client = Client(name=f"Cliente {key}")
    session.add(client)
    session.flush()
    vehicle = Vehicle(
        license_plate=key[:6].upper(),
        type=VehicleType.CARRO,
        brand="Renault",
        model="Logan",
        color="Rojo",
        client_id=client.id,
    )
    session.add(vehicle)
    session.flush()
    membership = Membership(
        vehicle_id=vehicle.id,
        starts_at=previous - timedelta(days=30),
        expires_at=cutoff,
        current_cutoff_date=cutoff,
        activated_at=previous,
    )
    session.add(membership)
    session.flush()
    payment = Payment(
        vehicle_id=vehicle.id,
        client_id=client.id,
        membership_id=membership.id,
        amount=Decimal("120000.00"),
        payment_method="EFECTIVO",
        paid_at=previous,
        coverage_start=previous,
        coverage_end=cutoff,
        previous_cutoff=previous,
        recorded_by=account.id,
        status="REGISTERED",
        idempotency_key=key,
    )
    session.add(payment)
    session.commit()
    return payment


def test_same_idempotency_key_is_rejected(session):
    admin = _account(session, "admin", AccountRole.ADMINISTRADOR)
    now = datetime.now(timezone.utc)
    first = _payment(
        session, admin, key="pago-001",
        cutoff=now + timedelta(days=30), previous=now,
    )
    duplicate = Payment(
        vehicle_id=first.vehicle_id,
        client_id=first.client_id,
        membership_id=first.membership_id,
        amount=Decimal("120000.00"),
        payment_method="QR",
        paid_at=now,
        coverage_start=now,
        coverage_end=now + timedelta(days=30),
        previous_cutoff=now,
        recorded_by=admin.id,
        status="REGISTERED",
        idempotency_key="pago-001",
    )
    session.add(duplicate)
    with pytest.raises(IntegrityError):
        session.commit()


def test_zero_amount_is_rejected(session):
    admin = _account(session, "admin", AccountRole.ADMINISTRADOR)
    now = datetime.now(timezone.utc)
    payment = _payment(
        session, admin, key="pago-002",
        cutoff=now + timedelta(days=30), previous=now,
    )
    payment.amount = Decimal("0.00")
    with pytest.raises(IntegrityError):
        session.commit()


def test_annulment_restores_cutoff_and_writes_audit(session):
    admin = _account(session, "admin", AccountRole.ADMINISTRADOR)
    now = datetime.now(timezone.utc)
    previous = now - timedelta(days=5)
    payment = _payment(
        session, admin, key="pago-003",
        cutoff=now + timedelta(days=25), previous=previous,
    )
    membership = session.get(Membership, payment.membership_id)
    membership.last_payment_id = payment.id
    session.commit()

    annulled = PaymentAnnulmentService(session).annul(payment.id, admin, "Error de registro")

    assert annulled.status == "ANNULLED"
    assert annulled.annulment_reason == "Error de registro"
    restored = session.get(Membership, payment.membership_id)
    assert restored.current_cutoff_date.replace(tzinfo=timezone.utc) == previous
    assert restored.expires_at.replace(tzinfo=timezone.utc) == previous
    assert restored.last_payment_id is None
    audit = session.scalar(select(PaymentAudit).where(PaymentAudit.payment_id == payment.id))
    assert audit.action == "ANNUL"
    assert audit.account_id == admin.id


def test_second_annulment_conflicts_and_operator_is_forbidden(session):
    admin = _account(session, "admin", AccountRole.ADMINISTRADOR)
    operator = _account(session, "operario1", AccountRole.OPERADOR)
    now = datetime.now(timezone.utc)
    payment = _payment(
        session, admin, key="pago-004",
        cutoff=now + timedelta(days=30), previous=now,
    )

    with pytest.raises(PaymentAnnulmentError) as forbidden:
        PaymentAnnulmentService(session).annul(payment.id, operator, "No corresponde")
    assert forbidden.value.status_code == 403
    assert session.get(Payment, payment.id).status == "REGISTERED"

    PaymentAnnulmentService(session).annul(payment.id, admin, "Error de registro")
    with pytest.raises(PaymentAnnulmentError) as conflict:
        PaymentAnnulmentService(session).annul(payment.id, admin, "Otra vez")
    assert conflict.value.status_code == 409
