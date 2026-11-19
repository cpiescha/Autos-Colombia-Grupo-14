from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints


class ClientResponse(BaseModel):
    id: int
    nombre: str


class ClientDeactivationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class ClientLifecycleResponse(ClientResponse):
    estado: Literal['ACTIVO', 'INACTIVO']
    fecha_baja: datetime | None
    motivo: str | None
    responsable_id: int | None
