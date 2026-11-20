"""Clipro FastAPI public prototype control-plane entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database import close_pool
from .ingestion import UploadPreflightRequest, UploadPreflightResponse, validate_upload_preflight
from .routers.jobs import router as jobs_router
from .routers.uploads import router as uploads_router
from .r2_storage import StorageNotConfigured
from .settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_pool()


settings = get_settings()
configured_origins = [origin.strip() for origin in settings.clipro_web_origins.split(",") if origin.strip()]
allowed_origins = ["*"] if "*" in configured_origins else configured_origins

app = FastAPI(
    title="Clipro API",
    version="0.6.0",
    description="Public prototype control plane for Clipro's source intake and editing jobs.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.include_router(uploads_router)
app.include_router(jobs_router)


@app.exception_handler(StorageNotConfigured)
async def storage_not_configured(_: Request, exc: StorageNotConfigured):
    return JSONResponse(status_code=503, content={"detail": "Media storage is not configured yet."})


@app.exception_handler(RuntimeError)
async def service_not_ready(_: Request, exc: RuntimeError):
    return JSONResponse(status_code=503, content={"detail": "A required Clipro service is not configured or unavailable."})


@app.get("/healthz", tags=["system"])
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "clipro-api"}


@app.post("/api/v1/uploads/preflight", response_model=UploadPreflightResponse, tags=["uploads"])
def upload_preflight(submission: UploadPreflightRequest) -> UploadPreflightResponse:
    return validate_upload_preflight(submission)
