from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Client, ClientStatusAudit, ParkingStay, UserAccount, Vehicle
from app.models.enums import AccountRole, ClientStatus
from app.services.auth import forbidden_error


class ClientLifecycleError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class ClientLifecycleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def deactivate(self, client_id: int, reason: str, account: UserAccount) -> Client:
        try:
            if account.role not in {AccountRole.ADMINISTRADOR, AccountRole.OPERADOR}:
                raise forbidden_error()
            if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 255:
                raise ClientLifecycleError(422, 'INVALID_CLIENT_DATA', 'Los datos del cliente no son válidos.')
            client = self.db.scalar(
                select(Client).where(Client.id == client_id)
                .with_for_update().execution_options(populate_existing=True)
            )
            if client is None:
                raise ClientLifecycleError(404, 'CLIENT_NOT_FOUND', 'El cliente no existe.')
            # Consume all rows before checking stays: entry holds the same vehicle lock.
            vehicles = list(self.db.scalars(
                select(Vehicle).where(Vehicle.client_id == client.id).order_by(Vehicle.id)
                .with_for_update().execution_options(populate_existing=True)
            ))
            if client.status == ClientStatus.INACTIVE.value:
                self.db.commit()
                return client
            open_stay = self.db.scalar(select(ParkingStay.id).where(
                ParkingStay.vehicle_id.in_([vehicle.id for vehicle in vehicles]),
                ParkingStay.exited_at.is_(None),
            ).limit(1))
            if open_stay is not None:
                raise ClientLifecycleError(409, 'CLIENT_HAS_OPEN_STAY', 'El cliente tiene vehículos con permanencias abiertas.')
            client.status = ClientStatus.INACTIVE.value
            client.inactivated_at = datetime.now(timezone.utc)
            client.inactivated_by = account.id
            client.inactivation_reason = reason.strip()
            self.db.add(ClientStatusAudit(
                client_id=client.id, account_id=account.id,
                action='INACTIVATE', reason=client.inactivation_reason,
            ))
            self.db.commit()
            self.db.refresh(client)
            return client
        except Exception:
            self.db.rollback()
            raise
