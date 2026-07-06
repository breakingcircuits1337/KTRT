from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import require_api_key
from app.schemas.quest import QuestRequest, QuestResponse
from app.services.orchestrator import run_quest, run_quest_stream

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


@router.post(
    "/quests/stream",
    summary="Launch a quest with live Server-Sent Events",
    description=(
        "Same as POST /v1/quests but streams progress as Server-Sent Events: a "
        "`node` event as each knight finishes, then a final `result` event "
        "carrying the full quest response JSON."
    ),
)
async def create_quest_stream(
    request: QuestRequest,
    _: str = Depends(require_api_key),
) -> StreamingResponse:
    return StreamingResponse(
        run_quest_stream(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
