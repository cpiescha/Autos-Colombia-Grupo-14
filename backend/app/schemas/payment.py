from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AnnulPaymentRequest(BaseModel):
    motivo: str = Field(min_length=1, max_length=255)


class PaymentResponse(BaseModel):
    id: int
    estado: str
    valor: Decimal
    medio: str
    fecha_corte_anterior: datetime | None
    anulado_en: datetime | None
    motivo_anulacion: str | None
