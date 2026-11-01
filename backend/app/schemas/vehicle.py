from typing import Literal

from pydantic import BaseModel


class VehicleLookupResponse(BaseModel):
    placa: str
    tipo: str
    marca: str
    modelo: str
    color: str
    estado_mensualidad: Literal["vigente", "vencida"]
    authorized: bool
    rejection_reason: str | None
