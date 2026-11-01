from datetime import datetime

from pydantic import BaseModel, Field, StrictInt, field_validator


class ExitCreateRequest(BaseModel):
    comprobante: str
    operario_id: StrictInt = Field(gt=0)

    @field_validator("comprobante")
    @classmethod
    def receipt_must_not_be_blank(cls, value: str) -> str:
        receipt_code = value.strip()
        if not receipt_code:
            raise ValueError("El comprobante es obligatorio.")
        return receipt_code


class ExitPreviewResponse(BaseModel):
    permanencia_id: int
    placa: str
    celda: str
    fecha_entrada: datetime


class ExitResponse(ExitPreviewResponse):
    fecha_salida: datetime


class ExitErrorResponse(BaseModel):
    code: str
    message: str
    details: None = None
