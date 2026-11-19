"""Clipro FastAPI control-plane entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .database import close_pool
from .ingestion import UploadPreflightRequest, UploadPreflightResponse, validate_upload_preflight
from .routers.uploads import router as uploads_router
from .r2_storage import StorageNotConfigured


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_pool()


app = FastAPI(
    title="Clipro API",
    version="0.3.0",
    description="Control plane for Clipro's source intake and editing jobs.",
    lifespan=lifespan,
)
app.include_router(uploads_router)


@app.exception_handler(StorageNotConfigured)
async def storage_not_configured(_: Request, exc: StorageNotConfigured):
    return JSONResponse(
        status_code=503,
        content={"detail": "Media storage is not configured yet."},
    )


@app.exception_handler(RuntimeError)
async def service_not_ready(_: Request, exc: RuntimeError):
    # Avoid returning driver/connection details to the public API caller.
    return JSONResponse(
        status_code=503,
        content={"detail": "A required Clipro service is not configured or unavailable."},
    )


@app.get("/healthz", tags=["system"])
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "clipro-api"}


@app.post("/api/v1/uploads/preflight", response_model=UploadPreflightResponse, tags=["uploads"])
def upload_preflight(submission: UploadPreflightRequest) -> UploadPreflightResponse:
    return validate_upload_preflight(submission)
