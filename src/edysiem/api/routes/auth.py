"""Operator identity endpoint used by API clients and the local UI."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..security import AuthenticatedIdentity, get_authenticated_identity

router = APIRouter(tags=["auth"])


@router.get("/auth/me", summary="Return the authenticated operator identity")
async def auth_me(
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
) -> dict[str, str]:
    return {
        "identity": identity.identity_id,
        "role": identity.role,
        "auth_type": identity.auth_type,
    }


__all__ = ["router"]
