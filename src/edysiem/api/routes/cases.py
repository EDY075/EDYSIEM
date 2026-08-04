"""Rota de criacao de cases."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...container import ApplicationContainer
from ...incidents import Incident
from ..deps import get_container
from ..schemas import CaseCreateRequest, CaseCreateResponse

router = APIRouter(tags=["cases"])


@router.post(
    "/cases",
    response_model=CaseCreateResponse,
    summary="Cria um case de investigacao a partir de um incidente",
)
async def create_case(
    body: CaseCreateRequest,
    container: ApplicationContainer = Depends(get_container),
) -> CaseCreateResponse:
    """Abre um workspace de investigacao para um incidente."""
    # Sem persistence: constroi um Incident sintetico a partir do ID.
    incident = Incident(
        title=body.title or f"Incidente {body.incident_id}",
        description="Incidente referenciado pela API (sem persistence)",
        id=body.incident_id,
    )

    result = await container.cases.create_from_incident(incident, owner=body.owner)
    return CaseCreateResponse(
        case_id=result.case.id,
        title=result.case.title,
        status=result.case.status.value,
    )


__all__ = ["router"]
