from collections.abc import Callable
from typing import Awaitable

from fastapi import APIRouter, Depends, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.exit import (
    ExitCreateRequest,
    ExitErrorResponse,
    ExitPreviewResponse,
    ExitResponse,
)
from app.services.exit import ExitError, ExitService


class ExitValidationRoute(APIRoute):
    """Return the exit contract's common error shape for invalid requests."""

    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except RequestValidationError:
                return _error_response(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "INVALID_EXIT_DATA",
                    "Los datos de salida no son válidos.",
                )

        return custom_route_handler


router = APIRouter(
    prefix="/api/salidas",
    tags=["salidas"],
    route_class=ExitValidationRoute,
)


@router.get("/comprobantes/{receipt_code}", response_model=ExitPreviewResponse)
def preview_exit(
    receipt_code: str,
    db: Session = Depends(get_db),
) -> ExitPreviewResponse | JSONResponse:
    try:
        result = ExitService(db).preview(receipt_code)
    except ExitError as error:
        return _error_response(error.status_code, error.code, error.message)
    except Exception:
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "EXIT_QUERY_FAILED",
            "No fue posible consultar el comprobante.",
        )

    return ExitPreviewResponse(
        permanencia_id=result.stay_id,
        placa=result.plate,
        celda=result.spot_code,
        fecha_entrada=result.entered_at,
    )


@router.post("", response_model=ExitResponse)
def confirm_exit(
    request: ExitCreateRequest,
    db: Session = Depends(get_db),
) -> ExitResponse | JSONResponse:
    try:
        result = ExitService(db).confirm(request.comprobante, request.operario_id)
    except ExitError as error:
        return _error_response(error.status_code, error.code, error.message)
    except Exception:
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "EXIT_CONFIRMATION_FAILED",
            "No fue posible registrar la salida.",
        )

    return ExitResponse(
        permanencia_id=result.stay_id,
        placa=result.plate,
        celda=result.spot_code,
        fecha_entrada=result.entered_at,
        fecha_salida=result.exited_at,
    )


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ExitErrorResponse(code=code, message=message).model_dump(),
    )
