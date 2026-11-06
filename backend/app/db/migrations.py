"""Small, additive upgrades for persistent databases created by older releases.

Run with ``python -m app.db.migrations`` before starting the API.
"""

from sqlalchemy import Engine, inspect, text

from app.db.base import Base
from app import models  # noqa: F401 — registers all tables and foreign-key targets.


def upgrade_schema(engine: Engine) -> None:
    """Preserve existing data while bringing the vehicle schema up to date."""
    with engine.begin() as connection:
        # Serialize concurrent backend starts on PostgreSQL. SQLite is used by
        # focused tests; production uses PostgreSQL transactional DDL.
        if connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(74190261)"))

        inspector = inspect(connection)
        if inspector.has_table("vehicles"):
            columns = {column["name"] for column in inspector.get_columns("vehicles")}
            if "active" not in columns:
                connection.execute(text(
                    "ALTER TABLE vehicles ADD COLUMN active BOOLEAN NOT NULL DEFAULT TRUE"
                ))

        # Also supports an empty database; create_all alone cannot add columns
        # to existing tables, hence the explicit additive upgrade above.
        Base.metadata.create_all(connection)


if __name__ == "__main__":
    from app.db.session import engine

    upgrade_schema(engine)
