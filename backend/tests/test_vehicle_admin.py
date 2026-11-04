import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_current_account
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Client, Operator, UserAccount, Vehicle
from app.models.enums import AccountRole


@pytest.fixture
def context():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as db:
        operator = Operator(name='Actor')
        customer = Client(name='Existing')
        db.add_all([operator, customer])
        db.flush()
        account = UserAccount(operator_id=operator.id, username='actor', password_hash='unused', role=AccountRole.ADMINISTRADOR, active=True)
        db.add(account)
        db.commit()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_account] = lambda: account
        with TestClient(app) as client:
            yield client, db, account, customer.id
    app.dependency_overrides.clear()
    engine.dispose()


def payload(client_id, plate=' abc123 '):
    return dict(placa=plate, tipo='CARRO', marca='Renault', modelo='Logan', color='Gris', cliente_id=client_id)


def snapshot(db):
    return (list(db.execute(text('SELECT * FROM vehicles'))), list(db.execute(text('SELECT * FROM vehicle_audits'))))


@pytest.mark.parametrize('role', list(AccountRole))
def test_registration_and_durable_actor(context, role):
    client, db, account, customer = context
    account.role = role
    response = client.post('/api/vehiculos', json=payload(customer))
    assert response.status_code == 201
    assert response.json()['placa'] == 'ABC123'
    assert db.scalar(select(Vehicle)).client_id == customer
    assert list(db.execute(text('SELECT action, account_id FROM vehicle_audits'))) == [('CREATE', account.id)]


def test_lookup_requires_authentication(context):
    client, db, account, customer = context
    del app.dependency_overrides[get_current_account]
    assert client.get('/api/vehiculos/ABC123').status_code == 401


def test_admin_update_retire_and_audit(context):
    client, db, account, customer = context
    assert client.post('/api/vehiculos', json=payload(customer)).status_code == 201
    assert client.put('/api/vehiculos/abc123', json=payload(customer, 'new123')).status_code == 200
    from datetime import datetime, timezone
    from app.models import ParkingSpot, ParkingStay
    from app.models.enums import SpotCategory

    spot = ParkingSpot(code='A-01', category=SpotCategory.AUTOMOVIL)
    db.add(spot)
    db.flush()
    stay = ParkingStay(vehicle_id=db.scalar(select(Vehicle.id)), parking_spot_id=spot.id,
                       entry_operator_id=account.operator_id, entered_at=datetime.now(timezone.utc))
    db.add(stay)
    db.commit()
    assert client.delete('/api/vehiculos/NEW123').status_code == 200
    assert db.get(ParkingStay, stay.id).vehicle_id == db.scalar(select(Vehicle.id))
    assert client.get('/api/vehiculos/NEW123').json()['authorized'] is False
    vehicle = db.scalar(select(Vehicle))
    assert vehicle.license_plate == 'NEW123' and not vehicle.active
    assert list(db.execute(text('SELECT action, account_id FROM vehicle_audits ORDER BY id'))) == [('CREATE', account.id), ('UPDATE', account.id), ('RETIRE', account.id)]


def test_rejections_are_atomic(context):
    client, db, account, customer = context
    assert client.post('/api/vehiculos', json=payload(customer)).status_code == 201
    before = snapshot(db)
    invalid = payload(customer, 'OTHER')
    invalid['account_id'] = 999
    assert client.post('/api/vehiculos', json=invalid).status_code == 422
    assert client.post('/api/vehiculos', json=payload(customer, '   ')).status_code == 422
    assert client.post('/api/vehiculos', json=payload(customer, ' ABC123 ')).status_code == 409
    assert client.post('/api/vehiculos', json=payload(999, 'OTHER')).status_code == 422
    assert client.put('/api/vehiculos/ABC123', json=payload(999)).status_code == 422
    assert snapshot(db) == before
    account.role = AccountRole.OPERADOR
    assert client.put('/api/vehiculos/ABC123', json=payload(customer)).status_code == 403
    assert client.delete('/api/vehiculos/ABC123').status_code == 403
    assert snapshot(db) == before
    del app.dependency_overrides[get_current_account]
    assert client.post('/api/vehiculos', json=payload(customer)).status_code == 401
    assert client.put('/api/vehiculos/ABC123', json=payload(customer)).status_code == 401
    assert client.delete('/api/vehiculos/ABC123').status_code == 401
    assert snapshot(db) == before
