from datetime import datetime

from pydantic import BaseModel, Field, StrictInt, field_validator


class EntryCreateRequest(BaseModel):
    placa: str
    operario_id: StrictInt = Field(gt=0)

    @field_validator("placa")
    @classmethod
    def plate_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("La placa es obligatoria.")
        return normalized


class EntryResponse(BaseModel):
    permanencia_id: int
    placa: str
    celda: str
    comprobante: str
    fecha_entrada: datetime


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: None = None
