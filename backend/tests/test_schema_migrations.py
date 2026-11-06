import pytest
from sqlalchemy import create_engine, event, inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.migrations import upgrade_schema
from app.models import Vehicle, VehicleAudit


@pytest.fixture
def engine():
    database = create_engine("sqlite://")

    @event.listens_for(database, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    yield database
    database.dispose()


def legacy_schema(engine):
    # Minimal old tables retain real foreign keys and a vehicle's stored fields.
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE clients (id INTEGER PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE user_accounts (id INTEGER PRIMARY KEY)"))
        connection.execute(text("""
            CREATE TABLE vehicles (
                id INTEGER PRIMARY KEY,
                license_plate VARCHAR(10) NOT NULL UNIQUE,
                type VARCHAR(10) NOT NULL,
                brand VARCHAR(80) NOT NULL,
                model VARCHAR(80) NOT NULL,
                color VARCHAR(40) NOT NULL,
                client_id INTEGER NOT NULL REFERENCES clients(id)
            )
        """))
        connection.execute(text("INSERT INTO clients VALUES (1)"))
        connection.execute(text("INSERT INTO user_accounts VALUES (1)"))
        connection.execute(text("""
            INSERT INTO vehicles VALUES
                (1, 'ABC123', 'CAR', 'Renault', 'Logan', 'Blue', 1)
        """))


def test_legacy_upgrade_preserves_vehicle_and_supports_audits(engine):
    legacy_schema(engine)
    assert not inspect(engine).has_table("vehicle_audits")
    assert "active" not in {c["name"] for c in inspect(engine).get_columns("vehicles")}

    upgrade_schema(engine)
    upgrade_schema(engine)

    with engine.begin() as connection:
        row = connection.execute(text("SELECT * FROM vehicles")).mappings().one()
        assert dict(row) == dict(
            id=1, license_plate="ABC123", type="CAR", brand="Renault",
            model="Logan", color="Blue", client_id=1, active=1,
        )
        assert connection.scalar(select(Vehicle.active)) is True
        connection.execute(VehicleAudit.__table__.insert().values(
            vehicle_id=1, account_id=1, action="UPDATE",
            before_state={"color": "Blue"}, after_state={"color": "Red"},
        ))
        audit = connection.execute(select(VehicleAudit.__table__)).mappings().one()
        assert audit["vehicle_id"] == audit["account_id"] == 1
        assert audit["occurred_at"] is not None

    # Referential integrity is enabled, not merely declared in test DDL.
    for vehicle_id, account_id in [(999, 1), (1, 999)]:
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(VehicleAudit.__table__.insert().values(
                vehicle_id=vehicle_id, account_id=account_id,
                action="UPDATE", after_state={},
            ))

    with engine.begin() as connection:
        connection.execute(text("UPDATE vehicles SET active = FALSE WHERE id = 1"))
    upgrade_schema(engine)
    with engine.connect() as connection:
        assert connection.scalar(select(Vehicle.active)) is False
        assert len(connection.execute(select(VehicleAudit.id)).all()) == 1


def schema_snapshot(engine):
    with engine.connect() as connection:
        return connection.execute(text(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        )).all()


def test_current_schema_is_unchanged_after_repeated_upgrade(engine):
    Base.metadata.create_all(engine)
    before = schema_snapshot(engine)
    upgrade_schema(engine)
    upgrade_schema(engine)
    assert schema_snapshot(engine) == before


def test_empty_database_can_be_initialized(engine):
    upgrade_schema(engine)
    assert set(inspect(engine).get_table_names()) == set(Base.metadata.tables)
    before = schema_snapshot(engine)
    upgrade_schema(engine)
    assert schema_snapshot(engine) == before
