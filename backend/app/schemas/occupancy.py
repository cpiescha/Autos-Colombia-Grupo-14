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
    operario_entrada: str
    comprobante: str | None = None


class CorreccionHistoricaResponse(BaseModel):
    celda_anterior: str
    celda_nueva: str
    operario: str
    fecha_correccion: datetime


class MovimientoHistoricoResponse(BaseModel):
    permanencia_id: int
    placa: str
    celda_final: str
    fecha_entrada: datetime
    fecha_salida: datetime
    comprobante: str | None = None
    operario_entrada: str
    operario_salida: str
    correcciones: list[CorreccionHistoricaResponse]


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
