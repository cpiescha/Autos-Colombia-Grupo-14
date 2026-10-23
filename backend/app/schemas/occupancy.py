from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CeldaResponse(BaseModel):
    codigo: str
    categoria: str
    estado: Literal["disponible", "ocupada"]
    placa: str | None


class MovimientoActivoResponse(BaseModel):
    permanencia_id: int
    placa: str
    celda: str
    fecha_entrada: datetime
    comprobante: str | None = None


class TotalesOcupacionResponse(BaseModel):
    capacidad: int
    ocupadas: int
    disponibles: int


class ReporteOcupacionResponse(BaseModel):
    vehiculos_registrados: int
    vehiculos_presentes: int
    moto: TotalesOcupacionResponse
    automovil: TotalesOcupacionResponse
    total: TotalesOcupacionResponse
