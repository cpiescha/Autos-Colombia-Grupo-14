from datetime import datetime

from pydantic import BaseModel, Field, StrictInt, StrictStr, field_validator


class CellCorrectionRequest(BaseModel):
    celda: StrictStr
    operario_id: StrictInt = Field(gt=0)

    @field_validator("celda")
    @classmethod
    def spot_code_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("La celda es obligatoria.")
        return normalized


class CellCorrectionResponse(BaseModel):
    movimiento_id: int
    celda_anterior: str
    celda_nueva: str
    operario_id: int
    fecha_correccion: datetime


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: None = None
