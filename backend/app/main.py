from fastapi import FastAPI

from app.api.vehicles import router as vehicles_router

app = FastAPI(
    title="Autos Colombia API",
    version="0.1.0",
)
app.include_router(vehicles_router)


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    """Report that the API process is ready to receive requests."""
    return {"status": "ok", "service": "backend"}
