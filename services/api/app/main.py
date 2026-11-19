"""Clipro FastAPI control-plane entrypoint.

M1a exposes health and upload preflight. Storage sessions, authentication,
multipart signing and worker dispatch are separate implementation steps.
Do not expose this service publicly until the auth boundary is configured.
"""
from fastapi import FastAPI

from .ingestion import (
    UploadPreflightRequest,
    UploadPreflightResponse,
    validate_upload_preflight,
)

app = FastAPI(
    title="Clipro API",
    version="0.1.0",
    description="Control plane for Clipro's source intake and editing jobs.",
)


@app.get("/healthz", tags=["system"])
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "clipro-api"}


@app.post(
    "/api/v1/uploads/preflight",
    response_model=UploadPreflightResponse,
    tags=["uploads"],
)
def upload_preflight(
    submission: UploadPreflightRequest,
) -> UploadPreflightResponse:
    """Validate a proposed upload before the browser starts transferring bytes."""

    return validate_upload_preflight(submission)
