import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.enums import SpotCategory

_SPOT_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9-]{1,19}$")
SpotState = Literal["ACTIVA", "INACTIVA"]
VisibleSpotState = Literal["disponible", "ocupada", "inactiva"]


class ParkingSpotCreateRequest(BaseModel):
    codigo: str = Field(min_length=2, max_length=20)
    categoria: SpotCategory

    @field_validator("codigo")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        code = value.strip().upper()
        if not _SPOT_CODE_PATTERN.fullmatch(code):
            raise ValueError("invalid parking spot code")
        return code


class ParkingSpotStateRequest(BaseModel):
    estado: SpotState


class ParkingSpotResponse(BaseModel):
    id: int
    codigo: str
    categoria: SpotCategory
    estado: VisibleSpotState
    placa: str | None
    tiene_historial: bool
