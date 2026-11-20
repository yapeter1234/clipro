"""Deploy Clipro's FastAPI control plane as a Modal ASGI web endpoint."""
from __future__ import annotations

import modal

APP_NAME = "clipro-api"
SECRET_NAME = "clipro-api-secrets"

app = modal.App(APP_NAME)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements("services/api/requirements.txt")
    .add_local_python_source("services")
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    cpu=1,
    memory=2048,
    timeout=900,
    scaledown_window=60,
    max_containers=3,
)
@modal.asgi_app()
def fastapi_app():
    """Expose the FastAPI control plane through Modal's HTTPS web endpoint."""
    from services.api.app.main import app as api

    return api
