"""Read-only client selector contract, using the authenticated integration fixture."""
import pytest
from sqlalchemy import select

from test_cell_admin import client, session_factory, _authorization, _token
from app.models import Client


@pytest.mark.parametrize('username,password', [('admin', 'Admin2026'), ('operario1', 'Operario2026')])
def test_both_roles_read_existing_clients(client, session_factory, username, password):
    with session_factory.begin() as session:
        session.add(Client(name='Segundo cliente'))
    with session_factory() as session:
        expected = [{'id': row.id, 'nombre': row.name} for row in session.scalars(select(Client).order_by(Client.id))]
    response = client.get('/api/clientes', headers=_authorization(_token(client, username, password)))
    assert response.status_code == 200
    assert response.json() == expected


def test_client_list_requires_authentication(client):
    response = client.get('/api/clientes')
    assert response.status_code == 401
    assert response.json()['code'] == 'INVALID_SESSION'


def test_client_endpoint_does_not_allow_creation(client):
    response = client.post('/api/clientes', headers=_authorization(_token(client, 'admin', 'Admin2026')), json={'nombre': 'Nuevo'})
    assert response.status_code == 405
