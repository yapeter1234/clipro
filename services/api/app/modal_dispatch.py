"""Modal function dispatch for Clipro's serverless processing jobs."""
from __future__ import annotations

from .settings import get_settings


class ModalDispatchDisabled(RuntimeError):
    pass


def spawn_media_probe(*, job_id: str, asset_id: str, workspace_id: str) -> str:
    """Spawn the deployed Modal probe function and return its FunctionCall ID."""
    settings = get_settings()
    if not settings.clipro_modal_dispatch_enabled:
        raise ModalDispatchDisabled("Modal dispatch is disabled.")

    # Import lazily so the API can still serve uploads before Modal is enabled.
    import modal

    function = modal.Function.from_name(
        settings.clipro_modal_app_name,
        settings.clipro_modal_probe_function,
    )
    call = function.spawn(job_id, asset_id, workspace_id)
    return str(call.object_id)
