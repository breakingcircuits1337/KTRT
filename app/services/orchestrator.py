from __future__ import annotations

import asyncio

from app.config import settings
from app.graph.state import MerlinState
from app.graph.workflow import get_graph
from app.schemas.quest import (
    ArtifactOut,
    DebateSummary,
    DebugSummary,
    QuestRequest,
    QuestResponse,
    SourceOut,
)
from app.utils.ids import make_run_id
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def run_quest(request: QuestRequest) -> QuestResponse:
    run_id = make_run_id("quest")
    logger.info("quest_start", run_id=run_id, query=request.query[:100], mode=request.mode)

    providers = {
        k: v
        for k, v in request.providers.model_dump().items()
        if v is not None
    }

    initial_state = MerlinState(
        run_id=run_id,
        query=request.query,
        mode=request.mode,
        max_debate_rounds=request.max_debate_rounds,
        max_debug_rounds=request.max_debug_rounds,
        providers=providers,
    )

    graph = get_graph()

    try:
        final_state: MerlinState = await asyncio.wait_for(
            graph.ainvoke(initial_state),
            timeout=settings.total_workflow_timeout,
        )
    except asyncio.TimeoutError:
        logger.error("quest_timeout", run_id=run_id)
        return QuestResponse(
            run_id=run_id,
            status="failed",
            final_answer="The quest timed out before completion.",
            confidence=None,
            debate_summary=DebateSummary(rounds=0),
            debug_summary=DebugSummary(rounds=0),
        )

    # LangGraph (>=1.x) returns the graph state as a plain dict even when the
    # state schema is a pydantic model — rehydrate it so attribute access works.
    if isinstance(final_state, dict):
        final_state = MerlinState(**final_state)

    logger.info(
        "quest_complete",
        run_id=run_id,
        status=final_state.run_status,
        debate_rounds=final_state.debate_round,
        debug_rounds=final_state.debug_round,
    )

    key_critiques = [
        f"[{c.severity.upper()}] {c.issue[:120]}"
        for c in (final_state.critiques or [])
    ]
    debug_issues = []
    if final_state.debug_notes and final_state.debug_decision == "BLOCKED":
        debug_issues = ["Blocked: see debug_notes in model trace."]

    sources_out = []
    if request.include_sources:
        sources_out = [
            SourceOut(
                title=s.title,
                url=s.url,
                snippet=s.snippet,
                published_at=s.published_at,
                source_type=s.source_type,
                credibility=s.credibility,
            )
            for s in final_state.sources
        ]

    return QuestResponse(
        run_id=run_id,
        status=final_state.run_status,
        final_answer=final_state.final_answer or final_state.draft_answer,
        confidence=final_state.confidence,
        debate_summary=DebateSummary(
            rounds=final_state.debate_round,
            judge_decision=final_state.judge_decision,
            key_critiques=key_critiques,
        ),
        debug_summary=DebugSummary(
            rounds=final_state.debug_round,
            decision=final_state.debug_decision,
            known_issues=debug_issues,
        ),
        artifacts=[
            ArtifactOut(path=a.path, artifact_type=a.artifact_type)
            for a in final_state.artifacts
        ],
        sources=sources_out,
        model_trace=final_state.model_trace,
    )
