from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import init_db
from .routes.observations import router as observations_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CampusPulse API",
    description="Anonymous campus environment observations and intelligence data.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(observations_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
