from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings
from app.schemas.quest import QuestRequest, QuestResponse
from app.services.orchestrator import run_quest

router = APIRouter(prefix="/v1", tags=["quests"])

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    if not settings.ktrt_api_key:
        # No key configured — open access (dev mode)
        return "dev"
    if api_key != settings.ktrt_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
    return api_key


@router.post(
    "/quests",
    response_model=QuestResponse,
    summary="Launch a research or build quest",
    description=(
        "Primary entry point for the Knights of the Round Table research lab. "
        "Accepts a query and orchestrates a multi-model adversarial research workflow, "
        "returning a consensus answer with citations, debate summary, and confidence score."
    ),
)
async def create_quest(
    request: QuestRequest,
    _: str = Depends(_require_api_key),
) -> QuestResponse:
    return await run_quest(request)
