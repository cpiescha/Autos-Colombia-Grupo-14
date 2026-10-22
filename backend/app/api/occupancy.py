from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.occupancy import (
    CeldaResponse,
    MovimientoActivoResponse,
    ReporteOcupacionResponse,
    TotalesOcupacionResponse,
)
from app.services.occupancy import OccupancyService, TotalesOcupacion


router = APIRouter(tags=["ocupacion"])


@router.get("/api/celdas", response_model=list[CeldaResponse])
def list_cells(db: Session = Depends(get_db)) -> list[CeldaResponse] | JSONResponse:
    try:
        return [
            CeldaResponse(**cell.__dict__)
            for cell in OccupancyService(db).list_cells()
        ]
    except Exception:
        return _query_error_response()


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
