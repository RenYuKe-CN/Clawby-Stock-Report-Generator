"""Clawby API key management endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import ErrorResponse
from app.services import clawby_config as cfg
from app.services.clawby import check_connectivity

router = APIRouter(prefix="/api/clawby-config", tags=["clawby"])


@router.get("")
async def get_clawby_config():
    config = cfg.load_config()
    key = config.get("api_key", "")
    return {
        "configured": bool(key),
        "api_key_preview": f"{key[:8]}...{key[-4:]}" if len(key) > 12 else ("***" if key else ""),
    }


@router.put("")
async def update_clawby_key(body: dict):
    new_key = body.get("api_key", "").strip()
    if not new_key:
        return {"status": "error", "message": "API key cannot be empty"}
    cfg.update_api_key(new_key)
    return {"status": "ok", "message": "API key updated"}


@router.post("/test")
async def test_clawby_connection():
    # Reload key from config before testing
    from app.services import clawby as claw
    key = cfg.get_api_key()
    if not key:
        return {"success": False, "message": "No API key configured", "latency_ms": None}

    import time
    start = time.monotonic()
    result = await check_connectivity()
    latency = int((time.monotonic() - start) * 1000)

    if result == "ok":
        return {"success": True, "message": "Connected to Clawby API", "latency_ms": latency}
    elif result == "invalid_clawby_key":
        return {"success": False, "message": "Invalid API key (401)", "latency_ms": latency}
    else:
        return {"success": False, "message": result, "latency_ms": latency}
