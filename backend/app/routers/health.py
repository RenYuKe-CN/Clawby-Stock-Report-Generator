"""Health check & status endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.services.clawby import check_connectivity
from app.services.llm import registry

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
async def health():
    clawby_status = await check_connectivity()
    providers = registry.list()
    default_prov = next((p for p in providers if p.get("is_default")), None)

    return HealthResponse(
        status="ok",
        clawby_configured=bool(registry),
        clawby_status=clawby_status,
        providers_count=len(providers),
        default_provider=default_prov["name"] if default_prov else None,
    )
