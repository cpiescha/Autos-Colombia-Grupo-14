from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RegisterPaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vehiculo_id: int = Field(gt=0)
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    medio: Literal["EFECTIVO", "TRANSFERENCIA", "QR"]
    clave_idempotencia: str = Field(min_length=1, max_length=80)
    fecha_pago: datetime | None = None


class RegisteredPaymentResponse(BaseModel):
    id: int
    vehiculo_id: int
    cliente_id: int
    mensualidad_id: int
    estado: str
    valor: Decimal
    medio: str
    fecha_pago: datetime
    cobertura_desde: datetime
    fecha_corte: datetime
    fecha_corte_anterior: datetime | None
    responsable_id: int


class PaymentReadResponse(RegisteredPaymentResponse):
    anulado_en: datetime | None
    anulado_por_id: int | None
    motivo_anulacion: str | None


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
