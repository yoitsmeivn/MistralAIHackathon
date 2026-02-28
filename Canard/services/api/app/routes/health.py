# pyright: basic, reportMissingImports=false
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.models.api import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc).isoformat())
