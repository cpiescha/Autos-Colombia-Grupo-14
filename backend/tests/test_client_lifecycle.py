from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select, event

from test_cell_admin import client, session_factory, _authorization, _token
from app.models import Client, ClientStatusAudit, Vehicle, ParkingStay, Membership, Receipt, UserAccount


def headers(client, username='admin', password='Admin2026'):
    return _authorization(_token(client, username, password))


def close_stay(factory):
    with factory.begin() as db:
        db.get(ParkingStay, 1).exited_at = datetime.now(timezone.utc)
        db.get(ParkingStay, 1).exit_operator_id = 1


def snapshot(factory):
    with factory() as db:
        return {model.__tablename__: [tuple(row) for row in db.execute(select(model.__table__).order_by(model.id))]
                for model in (Client, Vehicle, ParkingStay, ClientStatusAudit, Receipt)}


@pytest.mark.parametrize('username,password', [('admin', 'Admin2026'), ('operario1', 'Operario2026')])
def test_deactivate_exact_dto_and_idempotency(client, session_factory, username, password):
    close_stay(session_factory)
    auth = headers(client, username, password)
    response = client.patch('/api/clientes/1/baja', headers=auth, json={'motivo': '  Solicitud del cliente  '})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {'id', 'nombre', 'estado', 'fecha_baja', 'motivo', 'responsable_id'}
    assert body['estado'] == 'INACTIVO'
    assert body['motivo'] == 'Solicitud del cliente'
    datetime.fromisoformat(body['fecha_baja'])
    with session_factory() as db:
        row = db.get(Client, 1)
        assert row.status == 'INACTIVE'
        assert row.inactivated_at.isoformat() == body['fecha_baja'].replace('Z', '+00:00').removesuffix('+00:00')
        assert row.inactivation_reason == body['motivo']
        assert row.inactivated_by == body['responsable_id']
        assert body['nombre'] == row.name and body['id'] == row.id
        assert db.get(Vehicle, 1).client_id == row.id
        audits = list(db.scalars(select(ClientStatusAudit)))
        assert len(audits) == 1
        assert (audits[0].action, audits[0].account_id, audits[0].reason) == ('INACTIVATE', row.inactivated_by, row.inactivation_reason)
    before = snapshot(session_factory)
    replay = client.patch('/api/clientes/1/baja', headers=headers(client, 'operario1', 'Operario2026'), json={'motivo': 'Otro motivo'})
    assert replay.status_code == 200 and replay.json() == body
    assert snapshot(session_factory) == before


@pytest.mark.parametrize('payload', [{}, {'motivo': None}, {'motivo': ''}, {'motivo': '   '}, {'motivo': 'x' * 256}, {'motivo': 12}])
def test_required_reason(client, payload):
    response = client.patch('/api/clientes/1/baja', headers=headers(client), json=payload)
    assert response.status_code == 422
    assert response.json() == {'code': 'INVALID_CLIENT_DATA', 'message': 'Los datos del cliente no son válidos.', 'details': None}


def test_auth_and_missing(client):
    assert client.patch('/api/clientes/1/baja', json={'motivo': 'Baja'}).status_code == 401


def test_missing_client(client):
    response = client.patch('/api/clientes/999/baja', headers=headers(client), json={'motivo': 'Baja'})
    assert response.status_code == 404
    assert response.json() == {'code': 'CLIENT_NOT_FOUND', 'message': 'El cliente no existe.', 'details': None}


def test_any_vehicle_open_rejects_without_mutation(client, session_factory):
    with session_factory.begin() as db:
        db.add(Vehicle(id=2, license_plate='NEW002', type='CARRO', brand='Marca', model='Modelo', color='Gris', client_id=1))
    before = snapshot(session_factory)
    response = client.patch('/api/clientes/1/baja', headers=headers(client), json={'motivo': 'Baja'})
    assert response.status_code == 409
    assert response.json() == {'code': 'CLIENT_HAS_OPEN_STAY', 'message': 'El cliente tiene vehículos con permanencias abiertas.', 'details': None}
    assert snapshot(session_factory) == before


@pytest.mark.parametrize('failure', ['audit', 'commit'])
def test_failure_rolls_back_and_session_is_reusable(session_factory, monkeypatch, failure):
    from app.services.client_lifecycle import ClientLifecycleService
    close_stay(session_factory)
    before = snapshot(session_factory)
    with session_factory() as db:
        account = db.get(UserAccount, 1)
        def fail(*args, **kwargs):
            raise RuntimeError('induced failure')
        if failure == 'commit':
            monkeypatch.setattr(db, 'commit', fail)
        else:
            event.listen(ClientStatusAudit, 'before_insert', fail)
        try:
            with pytest.raises(RuntimeError, match='induced failure'):
                ClientLifecycleService(db).deactivate(1, 'Baja', account)
            assert db.get(Client, 1).status == 'ACTIVE'
            assert list(db.scalars(select(ClientStatusAudit))) == []
        finally:
            if failure == 'audit':
                event.remove(ClientStatusAudit, 'before_insert', fail)
    assert snapshot(session_factory) == before


def test_locks_and_refreshes_before_stay_check(session_factory):
    from sqlalchemy.dialects import postgresql
    from app.services.client_lifecycle import ClientLifecycleService
    close_stay(session_factory)
    with session_factory() as db:
        cached = db.get(Client, 1)
        account = db.get(UserAccount, 1)
        # Simulate state committed elsewhere while this identity map remains stale.
        db.execute(Client.__table__.update().where(Client.id == 1).values(
            status='INACTIVE', inactivation_reason='Original', inactivated_by=2,
            inactivated_at=datetime(2026, 1, 1),
        ))
        db.commit()
        assert cached.status == 'ACTIVE'
        statements = []
        def capture(state):
            if state.is_select:
                statements.append((str(state.statement.compile(dialect=postgresql.dialect())), state.execution_options))
        event.listen(db, 'do_orm_execute', capture)
        result = ClientLifecycleService(db).deactivate(1, 'Nuevo', account)
        assert result.inactivation_reason == 'Original'
        assert result.inactivated_by == 2
        assert 'FROM clients' in statements[0][0] and 'FOR UPDATE' in statements[0][0]
        assert 'FROM vehicles' in statements[1][0] and 'FOR UPDATE' in statements[1][0]
        assert all(options.get('populate_existing') for _, options in statements[:2])
        assert list(db.scalars(select(ClientStatusAudit))) == []


def test_service_rechecks_role(session_factory):
    from app.services.client_lifecycle import ClientLifecycleService
    from app.services.auth import AuthorizationError
    with session_factory() as db:
        with pytest.raises(AuthorizationError):
            ClientLifecycleService(db).deactivate(1, 'Baja', SimpleNamespace(id=1, role='OTHER'))


@pytest.mark.parametrize('username,password,count', [('admin', 'Admin2026', 1), ('operario1', 'Operario2026', 0)])
def test_inactive_visibility(client, session_factory, username, password, count):
    with session_factory.begin() as db:
        db.get(Client, 1).status = 'INACTIVE'
    response = client.get('/api/clientes', headers=headers(client, username, password))
    assert response.status_code == 200
    assert len(response.json()) == count


def test_inactive_entry_with_current_membership(client, session_factory):
    close_stay(session_factory)
    now = datetime.now(timezone.utc)
    with session_factory.begin() as db:
        db.get(Client, 1).status = 'INACTIVE'
        db.add(Membership(vehicle_id=1, starts_at=now-timedelta(days=2), expires_at=now+timedelta(days=20)))
    before = snapshot(session_factory)
    response = client.post('/api/entradas', headers=headers(client), json={'placa': 'HIS001'})
    assert response.status_code == 409
    assert response.json()['code'] == 'CLIENT_INACTIVE'
    assert snapshot(session_factory) == before


def test_visibility_and_payment_restores_entry(client, session_factory):
    close_stay(session_factory)
    now = datetime.now(timezone.utc)
    with session_factory.begin() as db:
        # SQLite create_all does not implement the PostgreSQL partial stay index;
        # use a second vehicle with no history for the post-payment entry.
        db.add(Vehicle(id=2, license_plate='NEW002', type='CARRO', brand='Marca', model='Modelo', color='Gris', client_id=1))
        db.flush()
        db.add(Membership(vehicle_id=2, starts_at=now-timedelta(days=2), expires_at=now+timedelta(days=20), current_cutoff_date=now+timedelta(days=20)))
    admin = headers(client)
    operator = headers(client, 'operario1', 'Operario2026')
    assert client.patch('/api/clientes/1/baja', headers=admin, json={'motivo': 'Baja'}).status_code == 200
    assert len(client.get('/api/clientes', headers=admin).json()) == 1
    assert client.get('/api/clientes', headers=operator).json() == []
    before = snapshot(session_factory)
    response = client.post('/api/entradas', headers=operator, json={'placa': 'NEW002'})
    assert response.status_code == 409
    assert response.json() == {'code': 'CLIENT_INACTIVE', 'message': 'El cliente está inactivo.', 'details': None}
    assert snapshot(session_factory) == before
    payload = {'vehiculo_id': 2, 'valor': '120000', 'medio': 'EFECTIVO', 'clave_idempotencia': 'lifecycle-reactivation'}
    response = client.post('/api/pagos', headers=admin, json=payload)
    assert response.status_code == 201, response.text
    assert client.post('/api/pagos', headers=admin, json=payload).status_code == 201
    payload['clave_idempotencia'] = 'lifecycle-second-payment'
    assert client.post('/api/pagos', headers=admin, json=payload).status_code == 201
    with session_factory() as db:
        assert len(list(db.scalars(select(ClientStatusAudit).where(ClientStatusAudit.action == 'REACTIVATE')))) == 1
    assert client.post('/api/entradas', headers=operator, json={'placa': 'NEW002'}).status_code == 201
    assert client.patch('/api/clientes/1/reactivar', headers=admin).status_code == 404
