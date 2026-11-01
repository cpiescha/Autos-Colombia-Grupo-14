from collections.abc import Callable
from typing import Awaitable

from fastapi import APIRouter, Depends, Path, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.correction import (
    CellCorrectionRequest,
    CellCorrectionResponse,
    ErrorResponse,
)
from app.services.correction import (
    CellCorrectionError,
    CellCorrectionService,
    SqlAlchemyCellCorrectionRepository,
)


class CellCorrectionValidationRoute(APIRoute):
    """Return the correction contract's error shape for invalid requests."""

    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except RequestValidationError:
                return _invalid_data_response()

        return custom_route_handler


router = APIRouter(
    prefix="/api/movimientos",
    tags=["movimientos"],
    route_class=CellCorrectionValidationRoute,
)


@router.patch("/{movement_id}/celda", response_model=CellCorrectionResponse)
def correct_cell(
    request: CellCorrectionRequest,
    movement_id: int = Path(gt=0),
    db: Session = Depends(get_db),
) -> CellCorrectionResponse | JSONResponse:
    try:
        result = CellCorrectionService(SqlAlchemyCellCorrectionRepository(db)).correct(
            stay_id=movement_id,
            spot_code=request.celda,
            operator_id=request.operario_id,
        )
    except CellCorrectionError as error:
        return _error_response(error.status_code, error.code, error.message)
    except Exception:
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "CELL_CORRECTION_FAILED",
            "No fue posible corregir la celda.",
        )

    return CellCorrectionResponse(
        movimiento_id=result.stay_id,
        celda_anterior=result.previous_spot_code,
        celda_nueva=result.new_spot_code,
        operario_id=result.operator_id,
        fecha_correccion=result.corrected_at,
    )


def _invalid_data_response() -> JSONResponse:
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "INVALID_CORRECTION_DATA",
        "Los datos de corrección de celda no son válidos.",
    )


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(code=code, message=message).model_dump(),
    )
