from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.entries import router as entries_router
from app.api.vehicles import router as vehicles_router

app = FastAPI(
    title="Autos Colombia API",
    version="0.1.0",
)
app.include_router(vehicles_router)
app.include_router(entries_router)


@app.exception_handler(RequestValidationError)
async def entry_validation_error_handler(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    if request.url.path == "/api/entradas":
        return JSONResponse(
            status_code=422,
            content={
                "code": "INVALID_ENTRY_DATA",
                "message": "Los datos de entrada no son válidos.",
                "details": None,
            },
        )
    return await request_validation_exception_handler(request, error)


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    """Report that the API process is ready to receive requests."""
    return {"status": "ok", "service": "backend"}
