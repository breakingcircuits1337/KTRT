from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    theme: str


@router.get("/healthz", response_model=HealthResponse, summary="Health check")
async def healthz() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="ktrt",
        theme="Merlin's Knights of the Round Table",
    )
