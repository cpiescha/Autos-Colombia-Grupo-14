from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import VehicleType


class VehicleWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    placa: str = Field(min_length=1, max_length=10)
    tipo: VehicleType
    marca: str = Field(min_length=1, max_length=80)
    modelo: str = Field(min_length=1, max_length=80)
    color: str = Field(min_length=1, max_length=40)
    cliente_id: int = Field(gt=0)

    @field_validator("placa", mode="before")
    @classmethod
    def normalize_plate(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value


class VehicleResponse(VehicleWriteRequest):
    id: int
    activo: bool


class VehicleLookupResponse(BaseModel):
    placa: str
    tipo: str
    marca: str
    modelo: str
    color: str
    estado_mensualidad: Literal["vigente", "vencida"]
    authorized: bool
    rejection_reason: str | None
