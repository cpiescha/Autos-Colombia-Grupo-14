from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.entry import EntryRepository, SqlAlchemyEntryRepository
from app.services.vehicle_authorization import (
    SqlAlchemyVehicleRepository,
    VehicleRepository,
)


def get_vehicle_repository(
    db: Session = Depends(get_db),
) -> VehicleRepository:
    return SqlAlchemyVehicleRepository(db)


def get_entry_repository(
    db: Session = Depends(get_db),
) -> EntryRepository:
    return SqlAlchemyEntryRepository(db)
