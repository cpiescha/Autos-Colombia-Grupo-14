from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class MembershipResponse(BaseModel):
    vehiculo_id: int
    cliente_id: int
    placa: str
    mensualidad_id: int | None
    fecha_corte: datetime | None
    estado: Literal["vigente", "vencido"]
    fecha_ultimo_pago: datetime | None
