from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_account
from app.db.session import get_db
from app.schemas.occupancy import (
    CorreccionHistoricaResponse,
    MovimientoActivoResponse,
    MovimientoHistoricoResponse,
    ReporteOcupacionResponse,
    TotalesOcupacionResponse,
)
from app.services.occupancy import OccupancyService, TotalesOcupacion


router = APIRouter(tags=["ocupacion"], dependencies=[Depends(get_current_account)])



@router.get(
    "/api/movimientos/activos",
    response_model=list[MovimientoActivoResponse],
)
def list_active_movements(
    db: Session = Depends(get_db),
) -> list[MovimientoActivoResponse] | JSONResponse:
    try:
        return [
            MovimientoActivoResponse(**movement.__dict__)
            for movement in OccupancyService(db).list_active_movements()
        ]
    except Exception:
        return _query_error_response()


@router.get(
    "/api/movimientos/historial",
    response_model=list[MovimientoHistoricoResponse],
)
def list_movement_history(
    db: Session = Depends(get_db),
) -> list[MovimientoHistoricoResponse] | JSONResponse:
    try:
        return [
            MovimientoHistoricoResponse(
                permanencia_id=movement.permanencia_id,
                placa=movement.placa,
                celda_final=movement.celda_final,
                fecha_entrada=movement.fecha_entrada,
                fecha_salida=movement.fecha_salida,
                comprobante=movement.comprobante,
                operario_entrada=movement.operario_entrada,
                operario_salida=movement.operario_salida,
                correcciones=[
                    CorreccionHistoricaResponse(**correction.__dict__)
                    for correction in movement.correcciones
                ],
            )
            for movement in OccupancyService(db).list_movement_history()
        ]
    except Exception:
        return _query_error_response()


@router.get("/api/reportes/ocupacion", response_model=ReporteOcupacionResponse)
def occupancy_report(
    db: Session = Depends(get_db),
) -> ReporteOcupacionResponse | JSONResponse:
    try:
        report = OccupancyService(db).occupancy_report()
        return ReporteOcupacionResponse(
            vehiculos_registrados=report.vehiculos_registrados,
            vehiculos_presentes=report.vehiculos_presentes,
            moto=_totals_response(report.moto),
            automovil=_totals_response(report.automovil),
            total=_totals_response(report.total),
        )
    except Exception:
        return _query_error_response()


def _totals_response(totals: TotalesOcupacion) -> TotalesOcupacionResponse:
    return TotalesOcupacionResponse(**totals.__dict__)


def _query_error_response() -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "OCCUPANCY_QUERY_FAILED",
            "message": "No fue posible consultar la ocupación.",
            "details": None,
        },
    )
