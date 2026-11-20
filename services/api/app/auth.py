"""Shared internal identity for Clipro's public prototype."""
from uuid import UUID

from pydantic import BaseModel

# The current schema records workspace ownership even though this prototype has
# no accounts. Every public request uses the same system identity.
OPERATOR_USER_ID = UUID("00000000-0000-4000-8000-000000000001")


class CurrentUser(BaseModel):
    """Internal workspace identity, not an authenticated human user."""

    user_id: UUID


async def get_current_user() -> CurrentUser:
    """Return the shared prototype identity; no password or API token is needed."""
    return CurrentUser(user_id=OPERATOR_USER_ID)
