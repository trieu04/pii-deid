from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.config import get_config
from src.api import routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_config()
    yield


app = FastAPI(title="PII De-identification Service", version="1.0.0", lifespan=lifespan)
app.include_router(routes.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}
