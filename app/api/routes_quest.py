from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_api_key
from app.schemas.quest import QuestRequest, QuestResponse
from app.services.orchestrator import run_quest

router = APIRouter(prefix="/v1", tags=["quests"])


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
    _: str = Depends(require_api_key),
) -> QuestResponse:
    return await run_quest(request)
