from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.vehicle_authorization import (
    SqlAlchemyVehicleRepository,
    VehicleRepository,
)


def get_vehicle_repository(
    db: Session = Depends(get_db),
) -> VehicleRepository:
    return SqlAlchemyVehicleRepository(db)
