from fastapi import FastAPI

from app.interfaces.router import router

app = FastAPI(
    title="Ring Tryon AI Service",
    description="Hand landmark detection and finger measurement for ring virtual try-on",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
