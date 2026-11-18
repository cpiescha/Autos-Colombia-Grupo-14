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
        _add_column(connection, "clients", "status",
                    "status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'")
        _add_column(connection, "clients", "inactivated_at", "inactivated_at TIMESTAMP")
        _add_column(connection, "clients", "inactivated_by", "inactivated_by INTEGER")
        _add_column(connection, "clients", "inactivation_reason", "inactivation_reason VARCHAR(255)")
        _add_column(connection, "clients", "reactivated_at", "reactivated_at TIMESTAMP")
        _add_column(connection, "clients", "reactivated_by", "reactivated_by INTEGER")
        _add_column(connection, "memberships", "current_cutoff_date", "current_cutoff_date TIMESTAMP")
        _add_column(connection, "memberships", "last_payment_id", "last_payment_id INTEGER")
        _add_column(connection, "memberships", "activated_at", "activated_at TIMESTAMP")

        # Also supports an empty database; create_all alone cannot add columns
        # to existing tables, hence the explicit additive upgrade above.
        Base.metadata.create_all(connection)
        inspect(connection).clear_cache()

        if inspect(connection).has_table("memberships"):
            connection.execute(text(
                "UPDATE memberships SET current_cutoff_date = expires_at "
                "WHERE current_cutoff_date IS NULL"
            ))
        _add_last_payment_foreign_key(connection)


def _add_column(connection, table: str, column: str, definition: str) -> None:
    inspector = inspect(connection)
    if not inspector.has_table(table):
        return
    names = {item["name"] for item in inspector.get_columns(table)}
    if column not in names:
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {definition}"))


def _add_last_payment_foreign_key(connection) -> None:
    if connection.dialect.name != "postgresql":
        return
    inspector = inspect(connection)
    if not inspector.has_table("memberships") or not inspector.has_table("payments"):
        return
    names = {item["name"] for item in inspector.get_foreign_keys("memberships")}
    if "fk_memberships_last_payment" in names:
        return
    connection.execute(text(
        "ALTER TABLE memberships ADD CONSTRAINT fk_memberships_last_payment "
        "FOREIGN KEY (last_payment_id) REFERENCES payments (id)"
    ))


if __name__ == "__main__":
    from app.db.session import engine

    upgrade_schema(engine)
