from fastapi import FastAPI

app = FastAPI(
    title="Autos Colombia API",
    version="0.1.0",
)


@app.get("/api/health", tags=["health"])
def health() -> dict[str, str]:
    """Report that the API process is ready to receive requests."""
    return {"status": "ok", "service": "backend"}
