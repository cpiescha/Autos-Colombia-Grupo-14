from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_entry_repository
from app.schemas.entry import EntryCreateRequest, EntryResponse, ErrorResponse
from app.services.entry import EntryError, EntryRepository, EntryService


router = APIRouter(prefix="/api/entradas", tags=["entradas"])


@router.post("", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    request: EntryCreateRequest,
    repository: EntryRepository = Depends(get_entry_repository),
) -> EntryResponse | JSONResponse:
    try:
        result = EntryService(repository).create(request.placa, request.operario_id)
    except EntryError as error:
        return _error_response(error.status_code, error.code, error.message)
    except Exception:
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "ENTRY_CREATION_FAILED",
            "No fue posible registrar la entrada.",
        )

    return EntryResponse(
        permanencia_id=result.stay_id,
        placa=result.plate,
        celda=result.spot_code,
        comprobante=result.receipt_code,
        fecha_entrada=result.entered_at,
    )


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(code=code, message=message).model_dump(),
    )
