from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from app.db.migrations import upgrade_schema
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
from app.models.enums import AccountRole, ClientStatus, VehicleType
from app.services.payment_registration import (
    PaymentRegistrationError,
    PaymentRegistrationService,
)


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


def _utc(value):
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _account(session):
    operator = Operator(name="Operador pagos")
    session.add(operator)
    session.flush()
    account = UserAccount(
        operator_id=operator.id,
        username="operador.pagos",
        password_hash="not-used-in-sqlite",
        role=AccountRole.OPERADOR,
    )
    session.add(account)
    session.flush()
    return account


def _vehicle_with_membership(session, *, inactive=False, cutoff=None, second_membership=False):
    client = Client(
        name="Cliente pagos",
        status=ClientStatus.INACTIVE.value if inactive else ClientStatus.ACTIVE.value,
    )
    session.add(client)
    session.flush()
    vehicle = Vehicle(
        license_plate="PAY123",
        type=VehicleType.CARRO,
        brand="Renault",
        model="Logan",
        color="Azul",
        client_id=client.id,
    )
    session.add(vehicle)
    session.flush()
    now = datetime(2026, 11, 10, tzinfo=timezone.utc)
    first = Membership(
        vehicle_id=vehicle.id,
        starts_at=now - timedelta(days=60),
        expires_at=now - timedelta(days=30),
        current_cutoff_date=now - timedelta(days=30),
        activated_at=now - timedelta(days=60),
    )
    session.add(first)
    session.flush()
    selected = first
    if second_membership:
        selected = Membership(
            vehicle_id=vehicle.id,
            starts_at=now - timedelta(days=10),
            expires_at=cutoff or now,
            current_cutoff_date=cutoff,
            activated_at=None if cutoff is None else now - timedelta(days=10),
        )
        session.add(selected)
        session.flush()
    elif cutoff is not None:
        first.current_cutoff_date = cutoff
        first.expires_at = cutoff
    session.commit()
    return client, vehicle, selected, first


def test_registration_uses_latest_membership_and_writes_atomic_state(session):
    account = _account(session)
    cutoff = datetime(2026, 12, 20, tzinfo=timezone.utc)
    client, vehicle, membership, older_membership = _vehicle_with_membership(
        session,
        cutoff=cutoff,
        second_membership=True,
    )
    paid_at = datetime(2026, 12, 5, 14, 30, tzinfo=timezone.utc)

    payment = PaymentRegistrationService(session).register(
        vehicle_id=vehicle.id,
        amount=Decimal("120000.00"),
        payment_method="EFECTIVO",
        idempotency_key="payment-atomic-001",
        account=account,
        paid_at=paid_at,
    )

    session.refresh(membership)
    session.refresh(older_membership)
    assert payment.membership_id == membership.id
    assert payment.recorded_by == account.id
    assert _utc(payment.previous_cutoff) == cutoff
    assert _utc(payment.coverage_start) == cutoff
    assert _utc(payment.coverage_end) == cutoff + timedelta(days=30)
    assert _utc(membership.current_cutoff_date) == cutoff + timedelta(days=30)
    assert _utc(membership.expires_at) == cutoff + timedelta(days=30)
    assert membership.last_payment_id == payment.id
    assert _utc(older_membership.current_cutoff_date) == datetime(
        2026, 10, 11, tzinfo=timezone.utc
    )
    assert session.scalar(
        select(func.count()).select_from(PaymentAudit).where(
            PaymentAudit.payment_id == payment.id,
            PaymentAudit.action == "CREATE",
        )
    ) == 1
    assert client.status == ClientStatus.ACTIVE.value


def test_first_payment_reactivates_client_and_sets_activation_date(session):
    account = _account(session)
    client, vehicle, membership, _ = _vehicle_with_membership(
        session,
        inactive=True,
        cutoff=None,
        second_membership=True,
    )
    paid_at = datetime(2026, 12, 7, 9, 0, tzinfo=timezone.utc)

    payment = PaymentRegistrationService(session).register(
        vehicle_id=vehicle.id,
        amount=Decimal("120000.00"),
        payment_method="TRANSFERENCIA",
        idempotency_key="payment-reactivate-001",
        account=account,
        paid_at=paid_at,
    )

    session.refresh(client)
    session.refresh(membership)
    assert payment.previous_cutoff is None
    assert _utc(payment.coverage_start) == paid_at
    assert _utc(payment.coverage_end) == paid_at + timedelta(days=30)
    assert _utc(membership.activated_at) == paid_at
    assert client.status == ClientStatus.ACTIVE.value
    assert _utc(client.reactivated_at) == paid_at
    assert client.reactivated_by == account.id
    audit = session.scalar(
        select(ClientStatusAudit).where(ClientStatusAudit.client_id == client.id)
    )
    assert audit.action == "REACTIVATE"
    assert audit.account_id == account.id


def test_same_idempotency_key_returns_original_without_advancing_again(session):
    account = _account(session)
    cutoff = datetime(2026, 12, 20, tzinfo=timezone.utc)
    _, vehicle, membership, _ = _vehicle_with_membership(session, cutoff=cutoff)
    service = PaymentRegistrationService(session)
    request = {
        "vehicle_id": vehicle.id,
        "amount": Decimal("120000.00"),
        "payment_method": "QR",
        "idempotency_key": "payment-retry-001",
        "account": account,
        "paid_at": datetime(2026, 12, 10, 8, 0, tzinfo=timezone.utc),
    }

    first = service.register(**request)
    replay = service.register(**request)

    session.refresh(membership)
    assert replay.id == first.id
    assert _utc(membership.current_cutoff_date) == cutoff + timedelta(days=30)
    assert session.scalar(select(func.count()).select_from(Payment)) == 1
    assert session.scalar(select(func.count()).select_from(PaymentAudit)) == 1


@pytest.mark.parametrize("same_account", [True, False])
def test_integrity_error_replay_checks_owner(session, monkeypatch, same_account):
    account = _account(session)
    _, vehicle, membership, _ = _vehicle_with_membership(
        session, cutoff=datetime(2026, 12, 20, tzinfo=timezone.utc),
    )
    other_operator = Operator(name="Otro operador pagos")
    session.add(other_operator)
    session.flush()
    other = UserAccount(
        operator_id=other_operator.id,
        username="other-payment-account",
        password_hash="unused",
        role=AccountRole.OPERADOR,
    )
    session.add(other)
    session.commit()
    service = PaymentRegistrationService(session)
    request = dict(
        vehicle_id=vehicle.id,
        amount=Decimal("120000.00"),
        payment_method="QR",
        idempotency_key="payment-race",
        account=account,
        paid_at=datetime(2026, 12, 10, tzinfo=timezone.utc),
    )
    first = service.register(**request)
    cutoff = membership.current_cutoff_date
    lookup = service._payment_by_key
    calls = []

    def miss_initial_lookup(key):
        calls.append(key)
        return None if len(calls) == 1 else lookup(key)

    monkeypatch.setattr(service, "_payment_by_key", miss_initial_lookup)
    request["account"] = account if same_account else other
    if same_account:
        assert service.register(**request).id == first.id
    else:
        with pytest.raises(PaymentRegistrationError) as error:
            service.register(**request)
        assert error.value.status_code == 409
        assert error.value.code == "IDEMPOTENCY_CONFLICT"
        assert error.value.message == "La clave de idempotencia no está disponible."
    assert len(calls) == 2
    session.refresh(membership)
    assert membership.current_cutoff_date == cutoff
    assert membership.last_payment_id == first.id
    assert session.scalar(select(func.count()).select_from(Payment)) == 1
    assert session.scalar(select(func.count()).select_from(PaymentAudit)) == 1
    assert session.scalar(select(func.count()).select_from(ClientStatusAudit)) == 0


def test_registration_failure_rolls_back_payment_cutoff_and_reactivation(session):
    account = _account(session)
    client, vehicle, membership, _ = _vehicle_with_membership(
        session,
        inactive=True,
        cutoff=None,
        second_membership=True,
    )
    original_expiry = membership.expires_at

    def fail_when_audit_is_flushed(db, _context, _instances):
        if any(isinstance(item, PaymentAudit) for item in db.new):
            raise RuntimeError("forced audit failure")

    event.listen(session, "before_flush", fail_when_audit_is_flushed)
    with pytest.raises(RuntimeError, match="forced audit failure"):
        PaymentRegistrationService(session).register(
            vehicle_id=vehicle.id,
            amount=Decimal("120000.00"),
            payment_method="EFECTIVO",
            idempotency_key="payment-rollback-001",
            account=account,
            paid_at=datetime(2026, 12, 7, 9, 0, tzinfo=timezone.utc),
        )
    event.remove(session, "before_flush", fail_when_audit_is_flushed)

    session.expire_all()
    assert session.scalar(select(func.count()).select_from(Payment)) == 0
    assert session.scalar(select(func.count()).select_from(PaymentAudit)) == 0
    assert session.scalar(select(func.count()).select_from(ClientStatusAudit)) == 0
    restored_membership = session.get(Membership, membership.id)
    restored_client = session.get(Client, client.id)
    assert restored_membership.current_cutoff_date is None
    assert restored_membership.expires_at == original_expiry
    assert restored_membership.last_payment_id is None
    assert restored_client.status == ClientStatus.INACTIVE.value
    assert restored_client.reactivated_at is None
    assert restored_client.reactivated_by is None
